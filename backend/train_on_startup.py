"""
Trains model on Railway if no pkl exists.
Runs once on cold start.
"""
import os, joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupShuffleSplit

FEATURE_COLS = ['innings','over','ball','runs_scored','wickets_fallen',
    'balls_remaining','target','runs_required','current_run_rate',
    'required_run_rate','run_rate_diff','runs_last_3_overs','wickets_last_3_overs']

def train_and_save(model_path):
    print("Training model from scratch...")
    df = pd.read_parquet('data/processed/features_labeled.parquet')
    df['required_run_rate'] = df['required_run_rate'].clip(upper=100)
    df['run_rate_diff'] = df['run_rate_diff'].clip(lower=-100, upper=100)

    X = df[FEATURE_COLS].values
    y = df['batting_team_won'].values
    groups = df['match_id'].values

    gss = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
    train_idx, rest_idx = next(gss.split(X, y, groups))
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
    cal_idx, _ = next(gss2.split(X[rest_idx], y[rest_idx], groups[rest_idx]))

    X_train, y_train = X[train_idx], y[train_idx]
    X_cal = X[rest_idx][cal_idx]
    y_cal = y[rest_idx][cal_idx]

    rf = RandomForestClassifier(n_estimators=100, max_depth=10,
        min_samples_leaf=20, n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)

    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(rf.predict_proba(X_cal)[:,1], y_cal)

    joblib.dump({'rf': rf, 'iso': iso}, model_path)
    print(f"Model saved to {model_path}")
