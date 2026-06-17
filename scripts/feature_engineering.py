"""
Day 1 — Script 2: feature_engineering.py
Takes the raw parsed data and builds game state features
at every single delivery of every match.
Output: features_labeled.parquet — ready for model training.
"""

import os
import pandas as pd
import numpy as np
from tqdm import tqdm

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')


def extract_over_ball(ball_col):
    """Convert Cricsheet ball float (e.g. 1.3) to (over_index, ball_index)."""
    ball_str = str(ball_col)
    parts = ball_str.split('.')
    over = int(parts[0])
    ball = int(parts[1]) if len(parts) > 1 else 0
    return over, ball


def build_innings_features(innings_df: pd.DataFrame, innings_num: int,
                            target: int, batting_team: str, winner: str) -> list:
    """
    Given a single innings DataFrame (sorted by ball),
    compute cumulative game state at each delivery.
    Returns list of feature dicts.
    """
    rows = []

    cumulative_runs     = 0
    cumulative_wickets  = 0
    legal_balls_bowled  = 0

    # For momentum: last 3 overs (18 balls)
    run_history    = []
    wicket_history = []

    for _, delivery in innings_df.iterrows():
        over_num, ball_num = extract_over_ball(delivery['ball'])

        # State BEFORE this delivery (what the model sees)
        balls_remaining = max(0, 120 - legal_balls_bowled)
        runs_required   = max(0, target - cumulative_runs) if innings_num == 2 else 0
        overs_completed = legal_balls_bowled / 6

        crr = (cumulative_runs / overs_completed) if overs_completed > 0 else 0
        rrr = (runs_required / (balls_remaining / 6)) if balls_remaining > 0 and innings_num == 2 else 0

        # Momentum: last 18 balls
        last_18_runs    = sum(run_history[-18:])
        last_18_wickets = sum(wicket_history[-18:])

        feature_row = {
            # Identity
            'match_id':             delivery['match_id'],
            'innings':              innings_num,
            'batting_team':         batting_team,
            'over':                 over_num,
            'ball':                 ball_num,
            'legal_ball_number':    legal_balls_bowled,

            # Core game state features
            'runs_scored':          cumulative_runs,
            'wickets_fallen':       cumulative_wickets,
            'balls_remaining':      balls_remaining,
            'target':               target if innings_num == 2 else 0,
            'runs_required':        runs_required,
            'current_run_rate':     round(crr, 4),
            'required_run_rate':    round(rrr, 4),
            'run_rate_diff':        round(crr - rrr, 4) if innings_num == 2 else 0,

            # Momentum signals
            'runs_last_3_overs':    last_18_runs,
            'wickets_last_3_overs': last_18_wickets,

            # This delivery's outcome (for label + next state)
            'runs_this_ball':       int(delivery['total_runs']),
            'wicket_this_ball':     int(delivery['is_wicket']),
            'is_legal':             int(delivery['is_legal']),

            # Label
            'batting_team_won':     1 if batting_team == winner else 0,
        }

        rows.append(feature_row)

        # Update state AFTER this delivery
        cumulative_runs    += int(delivery['total_runs'])
        cumulative_wickets += int(delivery['is_wicket'])

        run_history.append(int(delivery['runs_off_bat']))
        wicket_history.append(int(delivery['is_wicket']))

        if delivery['is_legal']:
            legal_balls_bowled += 1

        # All out
        if cumulative_wickets >= 10:
            break

    return rows


def get_innings1_target(match_df: pd.DataFrame) -> int:
    """Get 1st innings final score to use as target for 2nd innings."""
    inn1 = match_df[match_df['innings'] == 1]
    if inn1.empty:
        return 0
    total = inn1['total_runs'].sum()
    return int(total) + 1  # +1 because target = score + 1


def build_all_features():
    raw_path = os.path.join(PROCESSED_DIR, 'all_matches_raw.parquet')
    print(f"Loading {raw_path}...")
    df = pd.read_parquet(raw_path)

    match_ids = df['match_id'].unique()
    print(f"Building features for {len(match_ids)} matches...")

    all_rows = []
    skipped  = 0

    for match_id in tqdm(match_ids, desc="Feature engineering"):
        match_df = df[df['match_id'] == match_id].copy()
        match_df = match_df.sort_values('ball')

        winner = match_df['winner'].iloc[0]

        # ── Innings 1 ──
        inn1_df = match_df[match_df['innings'] == 1]
        if inn1_df.empty:
            skipped += 1
            continue

        batting_team_1 = inn1_df['batting_team'].iloc[0]
        target_for_inn2 = get_innings1_target(match_df)

        inn1_rows = build_innings_features(inn1_df, 1, 0, batting_team_1, winner)
        all_rows.extend(inn1_rows)

        # ── Innings 2 ──
        inn2_df = match_df[match_df['innings'] == 2]
        if inn2_df.empty:
            skipped += 1
            continue

        batting_team_2 = inn2_df['batting_team'].iloc[0]
        inn2_rows = build_innings_features(inn2_df, 2, target_for_inn2, batting_team_2, winner)
        all_rows.extend(inn2_rows)

    print(f"\nSkipped {skipped} matches (incomplete data)")
    features_df = pd.DataFrame(all_rows)
    print(f"Total feature rows: {len(features_df):,}")

    # Drop rows where model can't learn anything useful
    # (first ball of match, no game state yet — still keep, model handles it)
    out_path = os.path.join(PROCESSED_DIR, 'features_labeled.parquet')
    features_df.to_parquet(out_path, index=False)
    print(f"Saved to {out_path}")

    # Quick stats
    print(f"\nLabel distribution:")
    print(features_df['batting_team_won'].value_counts(normalize=True).round(3))
    print(f"\nFeature columns: {list(features_df.columns)}")
    return features_df


def build_match_index():
    """Build a match index JSON for the frontend match picker."""
    raw_path = os.path.join(PROCESSED_DIR, 'all_matches_raw.parquet')
    df = pd.read_parquet(raw_path)

    index_rows = []
    for match_id, grp in df.groupby('match_id'):
        winner   = grp['winner'].iloc[0]
        team1    = grp['team1'].iloc[0]
        team2    = grp['team2'].iloc[0]
        date     = grp['match_date'].iloc[0]
        venue    = grp['venue'].iloc[0]

        index_rows.append({
            'id':     str(match_id),
            'teams':  [str(team1), str(team2)],
            'winner': str(winner),
            'date':   str(date),
            'venue':  str(venue),
            'format': 'T20',
        })

    import json
    index_path = os.path.join(PROCESSED_DIR, 'matches_index.json')
    with open(index_path, 'w') as f:
        json.dump(index_rows, f, indent=2)
    print(f"\nMatch index saved: {len(index_rows)} matches → {index_path}")


if __name__ == '__main__':
    print("=" * 50)
    print("CricketIQ — Day 1: Feature Engineering")
    print("=" * 50)
    features_df = build_all_features()
    build_match_index()

    print("\nSample features (first 3 rows):")
    sample_cols = ['match_id', 'innings', 'over', 'ball', 'runs_scored',
                   'wickets_fallen', 'balls_remaining', 'required_run_rate',
                   'runs_last_3_overs', 'batting_team_won']
    print(features_df[sample_cols].head(3).to_string())
    print("\nDone.")
