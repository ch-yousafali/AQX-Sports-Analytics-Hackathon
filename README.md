# CricketIQ — Live Match Win Probability Engine

> AQX Sports Analytics Hackathon | June 2026

A web-based interactive dashboard that models win probability ball-by-ball across 3,000+ T20 cricket matches using machine learning, and visualizes how each delivery shifted the outcome of a match.

**Live Demo:** [aqx-sports-analytics-hackathon.vercel.app](https://aqx-sports-analytics-hackathon.vercel.app)  
**API:** [web-production-c3fda.up.railway.app](https://web-production-c3fda.up.railway.app)

---

## The Problem

Cricket commentary platforms like ESPN Cricinfo and CricBuzz show static scorecards. Fans, analysts, and coaches have no visual, interactive tool that shows *how* win probability shifted ball-by-ball throughout a match — and *why* it shifted.

**The question we answer:**
> At any point in a cricket match, given the current game state, what is each team's probability of winning — and what moments actually changed the match?

---

## What It Does

- Trains a Random Forest model on 3,281 T20 international matches (749,336 deliveries)
- Generates a win probability curve for every ball of every match
- Automatically detects the top 5 momentum shift moments per match
- Lets users explore any historical match visually via an interactive chart
- Provides a "What If" State Explorer — input any hypothetical game state and get an instant win probability

---

## Demo

Select any match from the dropdown → see the probability curve update ball by ball → hover over any point to see the exact game state → key moments are annotated automatically.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data | Cricsheet.org — 3,281 T20I matches (ball-by-ball CSV) |
| ML Model | Random Forest (scikit-learn) + Isotonic Calibration |
| Backend | FastAPI + Uvicorn |
| Frontend | React (Create React App) + Recharts |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## ML Model

**Features used at every delivery:**

| Feature | Description |
|---|---|
| `innings` | 1st or 2nd innings |
| `over` | Current over (0–19) |
| `ball` | Ball within over (0–5) |
| `runs_scored` | Cumulative runs so far |
| `wickets_fallen` | Cumulative wickets lost |
| `balls_remaining` | Balls left in innings |
| `target` | 2nd innings target (0 in 1st) |
| `runs_required` | Runs still needed (2nd innings) |
| `current_run_rate` | Runs per over so far |
| `required_run_rate` | Runs per over needed |
| `run_rate_diff` | CRR minus RRR (pressure indicator) |
| `runs_last_3_overs` | Momentum signal |
| `wickets_last_3_overs` | Pressure signal |

**Model performance:**
- Log Loss: `0.4907`
- ROC-AUC: `0.8360`
- Brier Score: `0.1651`
- Train/test split: by match (not by row) to prevent data leakage
- Calibration: Isotonic regression on held-out calibration set

---

## Project Structure

```
cricketiq/
├── backend/
│   ├── main.py              # FastAPI app — 3 endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js           # API calls via REACT_APP_API_URL
│   │   └── components/
│   │       ├── MatchPicker.js
│   │       ├── WinProbabilityChart.js
│   │       ├── KeyMomentsPanel.js
│   │       └── StateExplorer.js
│   └── vercel.json
├── scripts/
│   ├── parse_data.py        # Parse Cricsheet CSVs
│   ├── feature_engineering.py  # Build game state features
│   └── train_model.py       # Train, calibrate, serialize model
├── models/
│   ├── model_bundle.pkl     # Trained RF + isotonic calibrator
│   └── model_meta.json      # Feature list + metrics
├── data/
│   └── processed/
│       ├── matches_index.json       # Match metadata for frontend
│       └── match_sequences/         # Per-match probability JSONs
├── .python-version          # Python 3.12 (Railway)
├── Procfile                 # uvicorn backend.main:app
└── requirements.txt
```

---

## API Endpoints

### `GET /api/matches`
Returns searchable list of all matches.

### `GET /api/match/{match_id}`
Returns full ball-by-ball win probability sequence + key moments for a match.

### `POST /api/predict`
Takes a hypothetical game state, returns win probability instantly.

```json
{
  "innings": 2,
  "over": 15,
  "ball": 3,
  "runs_scored": 112,
  "wickets_fallen": 4,
  "target": 165,
  "format": "T20"
}
```

---

## Running Locally

### Prerequisites
- Python 3.12+
- Node.js 18+

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn backend.main:app --reload --port 8000
```

API will be live at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000" > .env
npm start
```

Frontend will be live at `http://localhost:3000`

---

## Data

Data sourced from **[Cricsheet.org](https://cricsheet.org/downloads/)** — free, open-source ball-by-ball cricket data.

Download `t20s_male_csv2.zip` and extract into `data/raw/`.

To regenerate processed data from scratch:

```bash
python scripts/parse_data.py
python scripts/feature_engineering.py
python scripts/train_model.py
```

> Note: `data/raw/` and `data/processed/*.parquet` are excluded from this repo due to size. The processed `match_sequences/` and `matches_index.json` are included.

---

## Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | aqx-sports-analytics-hackathon.vercel.app |
| Backend | Railway | web-production-c3fda.up.railway.app |

Environment variable required on Vercel:
```
REACT_APP_API_URL=https://web-production-c3fda.up.railway.app
```

---

## Key Moments Algorithm

The top 5 deliveries with the largest win probability swing are automatically detected and annotated on the chart:

```python
def find_key_moments(probs, top_n=5):
    deltas = [(i, abs(probs[i] - probs[i-1])) for i in range(1, len(probs))]
    return sorted(deltas, key=lambda x: x[1], reverse=True)[:top_n]
```

---

## V2 Extensions

- Live match integration via CricAPI
- Player-level features (bowler economy, batsman strike rate)
- Over-level strategy recommender
- ODI format support
- Mobile-responsive layout

---

## Author

**Yousuf Ali**  
Computational Physics, University of the Punjab   
GitHub: [@ch-yousafali](https://github.com/ch-yousafali)  
LinkedIn: [ch-yousafali](https://linkedin.com/in/ch-yousafali)
