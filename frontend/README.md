# CricketIQ — Frontend (Day 4)

React frontend for the CricketIQ Win Probability Engine.

## Stack
- React 18
- Recharts (AreaChart for probability curves)
- Lucide React (icons)
- No UI library — custom CSS-in-JS with design tokens

## Features
- **Match Picker** — searchable dropdown across 3,000+ T20 matches with infinite scroll
- **Win Probability Chart** — ball-by-ball AreaChart with wicket markers, hover tooltips, innings tabs
- **Key Moments Panel** — top 6 momentum swings ranked by probability delta, across both innings
- **Match Summary Bar** — teams, date, venue, winner badge
- **What-If Explorer** — manual state input → live prediction from the ML model

## Setup

```bash
cd cricketiq-frontend
npm install
```

Copy the env file:
```bash
cp .env.example .env
```

For local dev, leave `REACT_APP_API_URL` blank — React proxies to `localhost:8000` (the FastAPI backend).

```bash
npm start
```

## Folder structure

```
src/
  api.js                    # All fetch calls to FastAPI backend
  App.js                    # Root layout + match state management
  index.js / index.css      # Entry + global design tokens
  components/
    MatchPicker.js          # Searchable dropdown with pagination
    WinProbabilityChart.js  # Recharts AreaChart with annotations
    KeyMomentsPanel.js      # Ranked momentum swings
    MatchSummaryBar.js      # Match metadata bar
    StateExplorer.js        # What-if prediction form
```

## Deploy to Vercel

1. Push this folder to GitHub
2. Import to Vercel
3. Set environment variable: `REACT_APP_API_URL=https://your-render-backend.onrender.com`
4. Deploy

## How it connects to the backend

All API calls go through `src/api.js`:

| Function | Endpoint | Used by |
|---|---|---|
| `fetchMatches` | `GET /api/matches` | MatchPicker |
| `fetchMatch(id)` | `GET /api/match/{id}` | App.js on match select |
| `postPredict(state)` | `POST /api/predict` | StateExplorer |

The `package.json` proxy (`"proxy": "http://localhost:8000"`) forwards API calls in dev so no CORS issues locally.
