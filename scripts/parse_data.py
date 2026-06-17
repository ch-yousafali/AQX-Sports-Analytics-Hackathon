"""
Day 1 — Script 1: parse_data.py
Reads all Cricsheet CSV match files and info files,
extracts ball-by-ball data + match metadata,
saves as a single merged parquet for fast processing.
"""

import os
import pandas as pd
from tqdm import tqdm

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUT_DIR  = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)


def parse_info_file(filepath: str) -> dict:
    """Extract match metadata from _info.csv file."""
    meta = {}
    try:
        df = pd.read_csv(filepath, header=None, names=['type', 'key', 'value', 'extra', 'extra2'])
        for _, row in df.iterrows():
            key = str(row['key']).strip()
            val = str(row['value']).strip()

            if key == 'winner':
                meta['winner'] = val
            elif key == 'match_type':
                meta['match_type'] = val
            elif key == 'team' and 'team1' not in meta:
                meta['team1'] = val
            elif key == 'team' and 'team1' in meta:
                meta['team2'] = val
            elif key == 'date':
                meta['date'] = val
            elif key == 'venue':
                meta['venue'] = val
            elif key == 'toss_winner':
                meta['toss_winner'] = val
            elif key == 'toss_decision':
                meta['toss_decision'] = val
    except Exception:
        pass
    return meta


def load_all_matches():
    """Load all match CSV files, merge with metadata, return combined DataFrame."""
    all_files = os.listdir(RAW_DIR)

    # Get unique match IDs (files without _info suffix)
    match_ids = set()
    for f in all_files:
        if f.endswith('.csv') and '_info' not in f:
            match_ids.add(f.replace('.csv', ''))

    print(f"Found {len(match_ids)} matches")

    all_frames = []
    skipped = 0

    for match_id in tqdm(match_ids, desc="Parsing matches"):
        data_file = os.path.join(RAW_DIR, f"{match_id}.csv")
        info_file = os.path.join(RAW_DIR, f"{match_id}_info.csv")

        if not os.path.exists(data_file) or not os.path.exists(info_file):
            skipped += 1
            continue

        try:
            # Load ball-by-ball data
            df = pd.read_csv(data_file)

            # Load metadata
            meta = parse_info_file(info_file)

            # Skip if no winner (abandoned, no result)
            if 'winner' not in meta or not meta['winner'] or meta['winner'] == 'nan':
                skipped += 1
                continue

            # Skip non-T20
            if meta.get('match_type', '') != 'T20':
                skipped += 1
                continue

            # Attach metadata columns
            df['winner']        = meta.get('winner', '')
            df['team1']         = meta.get('team1', '')
            df['team2']         = meta.get('team2', '')
            df['match_date']    = meta.get('date', '')
            df['venue']         = meta.get('venue', '')
            df['toss_winner']   = meta.get('toss_winner', '')
            df['toss_decision'] = meta.get('toss_decision', '')

            all_frames.append(df)

        except Exception as e:
            skipped += 1
            continue

    print(f"\nLoaded: {len(all_frames)} matches | Skipped: {skipped}")
    combined = pd.concat(all_frames, ignore_index=True)
    print(f"Total deliveries: {len(combined):,}")
    return combined


def clean_and_save(df: pd.DataFrame):
    """Basic cleaning and save to parquet."""

    # Fill NaN extras/wickets with 0
    for col in ['wides', 'noballs', 'byes', 'legbyes', 'penalty']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['wicket_type']       = df['wicket_type'].fillna('')
    df['player_dismissed']  = df['player_dismissed'].fillna('')
    df['runs_off_bat']      = pd.to_numeric(df['runs_off_bat'], errors='coerce').fillna(0)
    df['extras']            = pd.to_numeric(df['extras'], errors='coerce').fillna(0)

    # is_wicket flag
    df['is_wicket'] = df['wicket_type'].apply(lambda x: 1 if x and x != '' else 0)

    # Total runs on this delivery
    df['total_runs'] = df['runs_off_bat'] + df['extras']

    # is_wide / is_noball
    df['is_wide']   = df['wides'].apply(lambda x: 1 if x > 0 else 0)
    df['is_noball'] = df['noballs'].apply(lambda x: 1 if x > 0 else 0)

    # Fix mixed-type columns for parquet
    df['season'] = df['season'].astype(str)

    # Legal delivery flag (wide/noball don't count toward over)
    df['is_legal'] = ((df['is_wide'] == 0) & (df['is_noball'] == 0)).astype(int)

    out_path = os.path.join(OUT_DIR, 'all_matches_raw.parquet')
    df.to_parquet(out_path, index=False)
    print(f"\nSaved to {out_path}")
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    return df


if __name__ == '__main__':
    print("=" * 50)
    print("CricketIQ — Day 1: Data Parser")
    print("=" * 50)
    df = load_all_matches()
    df = clean_and_save(df)
    print("\nSample (first 5 rows):")
    print(df[['match_id', 'innings', 'ball', 'batting_team', 'runs_off_bat',
              'is_wicket', 'winner']].head())
    print("\nDone.")
