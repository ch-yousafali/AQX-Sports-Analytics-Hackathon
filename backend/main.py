"""
Day 3 — main.py
FastAPI backend for CricketIQ.
Routes:
  GET  /api/matches           → paginated match list from matches_index.json
  GET  /api/match/{id}        → ball-by-ball probability sequence for a match
  POST /api/predict            → single game state → win probability
  GET  /api/health             → health check
"""

import os
import json
import math
import joblib
import numpy as np
from pathlib import Path
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent   # project root
DATA_DIR      = BASE_DIR / "data" / "processed"
MODELS_DIR    = BASE_DIR / "models"
SEQUENCES_DIR = DATA_DIR / "match_sequences"

# ── Feature columns (must match train_model.py) ───────────────────────────────
FEATURE_COLS = [
    "innings",
    "over",
    "ball",
    "runs_scored",
    "wickets_fallen",
    "balls_remaining",
    "target",
    "runs_required",
    "current_run_rate",
    "required_run_rate",
    "run_rate_diff",
    "runs_last_3_overs",
    "wickets_last_3_overs",
]

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CricketIQ API",
    description="Win probability engine for T20 cricket",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# Startup: load model + index once
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_model():
    """Load model bundle (RF + isotonic calibration) once and cache."""
    model_path = MODELS_DIR / "model_bundle.pkl"
    if not model_path.exists():
        raise RuntimeError(f"Model not found at {model_path}")
    bundle = joblib.load(model_path)
    return bundle["rf"], bundle["iso"]


@lru_cache(maxsize=1)
def get_matches_index() -> list[dict]:
    """Load matches_index.json once and cache."""
    index_path = DATA_DIR / "matches_index.json"
    if not index_path.exists():
        raise RuntimeError(f"matches_index.json not found at {index_path}")
    with open(index_path) as f:
        return json.load(f)


def predict_proba(features: list[float]) -> float:
    """Run RF → isotonic calibration → return calibrated win probability."""
    rf, iso = get_model()
    X = np.array(features, dtype=float).reshape(1, -1)
    raw_prob = rf.predict_proba(X)[0, 1]
    cal_prob = float(iso.transform([raw_prob])[0])
    return round(float(np.clip(cal_prob, 0.0, 1.0)), 4)


def confidence_label(prob: float, balls_remaining: int) -> str:
    """Simple confidence label based on how far prob is from 50/50."""
    margin = abs(prob - 0.5)
    if balls_remaining < 6:
        return "very high"
    if margin > 0.35:
        return "high"
    if margin > 0.20:
        return "medium"
    return "low"


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════

class PredictRequest(BaseModel):
    innings: int = Field(..., ge=1, le=2, description="1 or 2")
    over: int = Field(..., ge=0, le=19, description="Over index (0-based)")
    ball: int = Field(..., ge=0, le=5, description="Ball within over (0-based)")
    runs_scored: int = Field(..., ge=0)
    wickets_fallen: int = Field(..., ge=0, le=10)
    target: int = Field(0, ge=0, description="2nd innings target (0 if 1st innings)")
    format: str = Field("T20", description="T20 or ODI (T20 only for MVP)")
    # Optional — will be estimated if omitted
    runs_last_3_overs: Optional[int] = Field(None, ge=0)
    wickets_last_3_overs: Optional[int] = Field(None, ge=0)


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.get("/api/matches")
def list_matches(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Filter by team name"),
):
    """
    Returns paginated list of available matches.
    Optionally filter by team name (case-insensitive substring match).
    """
    matches = get_matches_index()

    if search:
        q = search.lower()
        matches = [
            m for m in matches
            if any(q in t.lower() for t in m.get("teams", []))
        ]

    total = len(matches)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "matches": matches[start:end],
    }


@app.get("/api/match/{match_id}")
def get_match(match_id: str):
    """
    Returns full ball-by-ball win probability sequence for a match.
    Reads from pre-generated match_sequences/{match_id}.json.
    If not found, regenerates on the fly from features_labeled.parquet.
    """
    seq_path = SEQUENCES_DIR / f"{match_id}.json"

    if seq_path.exists():
        with open(seq_path) as f:
            return json.load(f)

    # ── Fallback: generate on the fly ──────────────────────────────────────
    # This handles matches that weren't pre-generated.
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(status_code=404, detail=f"Match {match_id} sequence not found and pandas unavailable for live generation.")

    features_path = DATA_DIR / "features_labeled.parquet"
    if not features_path.exists():
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    df = pd.read_parquet(features_path)
    match_df = df[df["match_id"].astype(str) == str(match_id)]

    if match_df.empty:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    rf, iso = get_model()

    X = match_df[FEATURE_COLS].values.astype(float)
    X[:, FEATURE_COLS.index("required_run_rate")] = np.clip(
        X[:, FEATURE_COLS.index("required_run_rate")], 0, 100
    )
    raw_probs = rf.predict_proba(X)[:, 1]
    probs = iso.transform(raw_probs)
    probs = np.clip(probs, 0, 1)

    innings_1 = match_df[match_df["innings"] == 1]
    innings_2 = match_df[match_df["innings"] == 2]
    inn1_probs = probs[: len(innings_1)]
    inn2_probs = probs[len(innings_1) :]

    def build_balls(sub_df, sub_probs):
        balls = []
        for i, (_, row) in enumerate(sub_df.iterrows()):
            balls.append({
                "ball_num": i + 1,
                "over": int(row["over"]),
                "delivery": int(row["ball"]),
                "runs_scored": int(row["runs_scored"]),
                "wickets": int(row["wickets_fallen"]),
                "win_prob": round(float(sub_probs[i]), 4),
                "runs_this_ball": int(row["runs_this_ball"]),
                "is_wicket": bool(row["wicket_this_ball"]),
                "score": f"{int(row['runs_scored'])}/{int(row['wickets_fallen'])}",
            })
        return balls

    def find_key_moments(p_list, top_n=5):
        deltas = [
            (i, round(abs(p_list[i] - p_list[i - 1]), 4), round(p_list[i], 4))
            for i in range(1, len(p_list))
        ]
        deltas.sort(key=lambda x: x[1], reverse=True)
        return deltas[:top_n]

    winner = match_df["winner"].iloc[0] if "winner" in match_df.columns else ""
    batting_team_1 = innings_1["batting_team"].iloc[0] if not innings_1.empty else ""
    batting_team_2 = innings_2["batting_team"].iloc[0] if not innings_2.empty else ""

    sequence = {
        "match_id": str(match_id),
        "batting_team_1": str(batting_team_1),
        "batting_team_2": str(batting_team_2),
        "winner": str(winner),
        "innings_1": {
            "balls": build_balls(innings_1, inn1_probs),
            "key_moments": find_key_moments(inn1_probs.tolist()) if len(inn1_probs) > 1 else [],
            "final_score": int(innings_1["runs_scored"].iloc[-1] + innings_1["runs_this_ball"].iloc[-1])
            if not innings_1.empty else 0,
        },
        "innings_2": {
            "balls": build_balls(innings_2, inn2_probs),
            "key_moments": find_key_moments(inn2_probs.tolist()) if len(inn2_probs) > 1 else [],
        },
    }

    # Cache it for next time
    SEQUENCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(seq_path, "w") as f:
        json.dump(sequence, f)

    return sequence


@app.post("/api/predict")
def predict(req: PredictRequest):
    """
    Takes an arbitrary match state, returns win probability for the batting team.
    """
    legal_balls = req.over * 6 + req.ball
    balls_remaining = max(0, 120 - legal_balls)
    runs_required = max(0, req.target - req.runs_scored) if req.innings == 2 else 0

    overs_completed = legal_balls / 6 if legal_balls > 0 else 0
    crr = req.runs_scored / overs_completed if overs_completed > 0 else 0
    rrr = (runs_required / (balls_remaining / 6)) if balls_remaining > 0 and req.innings == 2 else 0
    run_rate_diff = (crr - rrr) if req.innings == 2 else 0

    # Clamp extremes
    rrr = min(rrr, 100)
    run_rate_diff = max(-100, min(100, run_rate_diff))

    features = [
        req.innings,
        req.over,
        req.ball,
        req.runs_scored,
        req.wickets_fallen,
        balls_remaining,
        req.target if req.innings == 2 else 0,
        runs_required,
        round(crr, 4),
        round(rrr, 4),
        round(run_rate_diff, 4),
        req.runs_last_3_overs if req.runs_last_3_overs is not None else 0,
        req.wickets_last_3_overs if req.wickets_last_3_overs is not None else 0,
    ]

    win_prob = predict_proba(features)

    return {
        "win_probability": win_prob,
        "lose_probability": round(1.0 - win_prob, 4),
        "confidence": confidence_label(win_prob, balls_remaining),
        "derived": {
            "balls_remaining": balls_remaining,
            "runs_required": runs_required,
            "current_run_rate": round(crr, 2),
            "required_run_rate": round(rrr, 2),
        },
    }
