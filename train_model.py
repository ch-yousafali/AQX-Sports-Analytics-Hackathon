"""
Day 2 — train_model.py
Trains win probability model on ball-by-ball cricket data.
Pipeline:
  1. Load features
  2. Train/test split (by match, not by row — prevents leakage)
  3. Train Random Forest + XGBoost
  4. Evaluate: Log Loss, ROC-AUC, Brier Score
  5. Calibrate best model (isotonic regression)
  6. Serialize model + feature list
  7. Generate per-match probability sequences for frontend
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm

from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss

import xgboost as xgb

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.join(os.path.dirname(__file__), '..')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
MODELS_DIR    = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Feature columns used for training ─────────────────────────────────────────
FEATURE_COLS = [
    'innings',
    'over',
    'ball',
    'runs_scored',
    'wickets_fallen',
    'balls_remaining',
    'target',
    'runs_required',
    'current_run_rate',
    'required_run_rate',
    'run_rate_diff',
    'runs_last_3_overs',
    'wickets_last_3_overs',
]

LABEL_COL = 'batting_team_won'


# ══════════════════════════════════════════════════════════════════════════════
# 1. LOAD & SPLIT
# ══════════════════════════════════════════════════════════════════════════════

def load_and_split(test_size=0.2):
    """
    Load features and split by MATCH (not by row).
    Splitting by row would leak future game state into training.
    """
    print("Loading features...")
    df = pd.read_parquet(os.path.join(PROCESSED_DIR, 'features_labeled.parquet'))

    # Cap extreme RRR to reduce noise (> 100 RRR = match is effectively over)
    df['required_run_rate'] = df['required_run_rate'].clip(upper=100)
    df['run_rate_diff']     = df['run_rate_diff'].clip(lower=-100, upper=100)

    X = df[FEATURE_COLS].values
    y = df[LABEL_COL].values
    groups = df['match_id'].values  # used for group-aware split

    # GroupShuffleSplit: all rows of a match go to same split
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    print(f"Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")
    print(f"Train matches: {len(np.unique(groups[train_idx]))} | Test matches: {len(np.unique(groups[test_idx]))}")

    return X_train, X_test, y_train, y_test, df


# ══════════════════════════════════════════════════════════════════════════════
# 2. TRAIN
# ══════════════════════════════════════════════════════════════════════════════

def train_random_forest(X_train, y_train):
    print("\n── Training Random Forest ──")
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=20,
        n_jobs=-1,
        random_state=42,
        class_weight='balanced',
    )
    rf.fit(X_train, y_train)
    print("  Done.")
    return rf


def train_xgboost(X_train, y_train):
    print("\n── Training XGBoost ──")
    xgb_model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train)],
        verbose=False,
    )
    print("  Done.")
    return xgb_model


# ══════════════════════════════════════════════════════════════════════════════
# 3. EVALUATE
# ══════════════════════════════════════════════════════════════════════════════

def evaluate(model, X_test, y_test, name="Model"):
    probs = model.predict_proba(X_test)[:, 1]
    ll    = log_loss(y_test, probs)
    auc   = roc_auc_score(y_test, probs)
    bs    = brier_score_loss(y_test, probs)
    print(f"\n  [{name}]")
    print(f"    Log Loss   : {ll:.4f}  (target < 0.45)")
    print(f"    ROC-AUC    : {auc:.4f}  (target > 0.80)")
    print(f"    Brier Score: {bs:.4f}  (lower = better calibrated)")
    return {'log_loss': ll, 'roc_auc': auc, 'brier': bs, 'probs': probs}


def feature_importance_report(model, model_name):
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        pairs = sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
        print(f"\n  [{model_name}] Feature Importances:")
        for feat, imp in pairs:
            bar = '█' * int(imp * 50)
            print(f"    {feat:<25} {imp:.4f}  {bar}")


# ══════════════════════════════════════════════════════════════════════════════
# 4. CALIBRATE
# ══════════════════════════════════════════════════════════════════════════════

def calibrate_model(base_model, X_train, y_train):
    """
    Wrap model with isotonic calibration.
    Tree models output poorly calibrated probabilities by default.
    Isotonic regression corrects the probability scale.
    """
    print("\n── Calibrating model (isotonic regression) ──")
    calibrated = CalibratedClassifierCV(
        base_model,
        method='isotonic',
        cv=5,
    )
    calibrated.fit(X_train, y_train)
    print("  Done.")
    return calibrated


# ══════════════════════════════════════════════════════════════════════════════
# 5. GENERATE PER-MATCH PROBABILITY SEQUENCES
# ══════════════════════════════════════════════════════════════════════════════

def find_key_moments(probs, top_n=5):
    """Find deliveries with largest probability swings."""
    deltas = []
    for i in range(1, len(probs)):
        delta = abs(probs[i] - probs[i - 1])
        deltas.append((i, round(delta, 4), round(probs[i], 4)))
    deltas.sort(key=lambda x: x[1], reverse=True)
    return deltas[:top_n]


def generate_match_sequences(model, df, sample_matches=None):
    """
    For each match, run model on every delivery and save the
    ball-by-ball probability sequence as JSON.
    Optionally limit to sample_matches for speed during dev.
    """
    out_dir = os.path.join(PROCESSED_DIR, 'match_sequences')
    os.makedirs(out_dir, exist_ok=True)

    match_ids = df['match_id'].unique()
    if sample_matches:
        match_ids = match_ids[:sample_matches]

    print(f"\n── Generating probability sequences for {len(match_ids)} matches ──")

    for match_id in tqdm(match_ids, desc="Generating sequences"):
        match_df = df[df['match_id'] == match_id].copy()

        X_match = match_df[FEATURE_COLS].values
        X_match[:, FEATURE_COLS.index('required_run_rate')] = \
            np.clip(X_match[:, FEATURE_COLS.index('required_run_rate')], 0, 100)

        probs = model.predict_proba(X_match)[:, 1]

        # Separate innings
        innings_1 = match_df[match_df['innings'] == 1]
        innings_2 = match_df[match_df['innings'] == 2]

        def build_balls(sub_df, sub_probs):
            balls = []
            for i, (_, row) in enumerate(sub_df.iterrows()):
                balls.append({
                    'ball_num':     i + 1,
                    'over':         int(row['over']),
                    'delivery':     int(row['ball']),
                    'runs_scored':  int(row['runs_scored']),
                    'wickets':      int(row['wickets_fallen']),
                    'win_prob':     round(float(sub_probs[i]), 4),
                    'runs_this_ball': int(row['runs_this_ball']),
                    'is_wicket':    bool(row['wicket_this_ball']),
                    'score':        f"{int(row['runs_scored'])}/{int(row['wickets_fallen'])}",
                })
            return balls

        inn1_probs = probs[:len(innings_1)]
        inn2_probs = probs[len(innings_1):]

        batting_team_1 = innings_1['batting_team'].iloc[0] if not innings_1.empty else ''
        batting_team_2 = innings_2['batting_team'].iloc[0] if not innings_2.empty else ''
        winner         = match_df['winner'].iloc[0]

        key_moments_1 = find_key_moments(inn1_probs.tolist()) if len(inn1_probs) > 1 else []
        key_moments_2 = find_key_moments(inn2_probs.tolist()) if len(inn2_probs) > 1 else []

        sequence = {
            'match_id':       str(match_id),
            'batting_team_1': str(batting_team_1),
            'batting_team_2': str(batting_team_2),
            'winner':         str(winner),
            'innings_1': {
                'balls':        build_balls(innings_1, inn1_probs),
                'key_moments':  key_moments_1,
                'final_score':  int(innings_1['runs_scored'].iloc[-1] + innings_1['runs_this_ball'].iloc[-1])
                                if not innings_1.empty else 0,
            },
            'innings_2': {
                'balls':        build_balls(innings_2, inn2_probs),
                'key_moments':  key_moments_2,
            },
        }

        out_path = os.path.join(out_dir, f"{match_id}.json")
        with open(out_path, 'w') as f:
            json.dump(sequence, f)

    print(f"  Sequences saved to {out_dir}/")


# ══════════════════════════════════════════════════════════════════════════════
# 6. SAVE MODEL
# ══════════════════════════════════════════════════════════════════════════════

def save_model(model, metrics, model_name='xgb_calibrated'):
    model_path = os.path.join(MODELS_DIR, f'{model_name}.pkl')
    meta_path  = os.path.join(MODELS_DIR, 'model_meta.json')

    joblib.dump(model, model_path)

    meta = {
        'model_name':   model_name,
        'feature_cols': FEATURE_COLS,
        'metrics':      {k: round(v, 4) for k, v in metrics.items() if k != 'probs'},
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"\n  Model saved  → {model_path}")
    print(f"  Metadata     → {meta_path}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 55)
    print("CricketIQ — Day 2: Model Training")
    print("=" * 55)

    # 1. Load & split
    X_train, X_test, y_train, y_test, df = load_and_split()

    # 2. Train both models
    rf  = train_random_forest(X_train, y_train)
    xgb_model = train_xgboost(X_train, y_train)

    # 3. Evaluate uncalibrated
    print("\n── Evaluation (uncalibrated) ──")
    rf_metrics  = evaluate(rf,        X_test, y_test, "Random Forest")
    xgb_metrics = evaluate(xgb_model, X_test, y_test, "XGBoost")

    # 4. Feature importance
    feature_importance_report(rf,        "Random Forest")
    feature_importance_report(xgb_model, "XGBoost")

    # 5. Pick best model (lower log loss = better)
    best_name  = "XGBoost" if xgb_metrics['log_loss'] < rf_metrics['log_loss'] else "Random Forest"
    best_model = xgb_model if best_name == "XGBoost" else rf
    best_raw_metrics = xgb_metrics if best_name == "XGBoost" else rf_metrics
    print(f"\n  ✓ Best model: {best_name}")

    # 6. Calibrate best model
    calibrated = calibrate_model(best_model, X_train, y_train)

    print("\n── Evaluation (after calibration) ──")
    cal_metrics = evaluate(calibrated, X_test, y_test, f"{best_name} Calibrated")

    # 7. Save
    save_model(calibrated, cal_metrics, model_name='xgb_calibrated')

    # 8. Generate match sequences (all matches)
    generate_match_sequences(calibrated, df, sample_matches=None)

    print("\n" + "=" * 55)
    print("Day 2 Complete.")
    print(f"  Log Loss : {cal_metrics['log_loss']:.4f}")
    print(f"  ROC-AUC  : {cal_metrics['roc_auc']:.4f}")
    print(f"  Brier    : {cal_metrics['brier']:.4f}")
    print("=" * 55)
