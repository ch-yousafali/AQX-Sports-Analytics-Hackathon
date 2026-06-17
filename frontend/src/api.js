const BASE = process.env.REACT_APP_API_URL || '';

export async function fetchMatches({ page = 1, perPage = 50, search = '' } = {}) {
  const params = new URLSearchParams({ page, per_page: perPage });
  if (search) params.set('search', search);
  const res = await fetch(`${BASE}/api/matches?${params}`);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

export async function fetchMatch(matchId) {
  const res = await fetch(`${BASE}/api/match/${matchId}`);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

export async function postPredict(state) {
  const res = await fetch(`${BASE}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}
