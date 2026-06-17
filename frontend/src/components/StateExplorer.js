import React, { useState } from 'react';
import { postPredict } from '../api';

const Field = ({ label, children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
    <label style={{ fontSize: 11, fontWeight: 600, color: '#999', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{label}</label>
    {children}
  </div>
);

const inputStyle = {
  height: 36, padding: '0 10px', background: '#fff',
  border: '1px solid #d4d4d4', borderRadius: 6, fontSize: 13,
  color: '#1a1a1a', width: '100%',
};

const DEFAULT = { innings: 2, over: 15, ball: 0, runs_scored: 120, wickets_fallen: 4, target: 165, format: 'T20' };

export default function StateExplorer() {
  const [form, setForm] = useState(DEFAULT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const run = async () => {
    setLoading(true); setError(null);
    try {
      const data = await postPredict({
        ...form,
        innings: +form.innings, over: +form.over, ball: +form.ball,
        runs_scored: +form.runs_scored, wickets_fallen: +form.wickets_fallen, target: +form.target,
      });
      setResult(data);
    } catch(e) { setError('Prediction failed — is the backend running?'); }
    finally { setLoading(false); }
  };

  const winPct = result ? Math.round(result.win_probability * 100) : null;
  const isWinning = winPct >= 50;

  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#999', marginBottom: 12 }}>
        What-if explorer
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <Field label="Innings">
            <select style={inputStyle} value={form.innings} onChange={e => set('innings', e.target.value)}>
              <option value={1}>1st innings</option>
              <option value={2}>2nd innings</option>
            </select>
          </Field>
          <Field label="Format">
            <select style={inputStyle} value={form.format} onChange={e => set('format', e.target.value)}>
              <option value="T20">T20</option>
              <option value="ODI">ODI</option>
            </select>
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <Field label="Over (0–19)">
            <input style={inputStyle} type="number" min={0} max={19} value={form.over} onChange={e => set('over', e.target.value)} />
          </Field>
          <Field label="Ball (0–5)">
            <input style={inputStyle} type="number" min={0} max={5} value={form.ball} onChange={e => set('ball', e.target.value)} />
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <Field label="Runs scored">
            <input style={inputStyle} type="number" min={0} value={form.runs_scored} onChange={e => set('runs_scored', e.target.value)} />
          </Field>
          <Field label="Wickets fallen">
            <input style={inputStyle} type="number" min={0} max={10} value={form.wickets_fallen} onChange={e => set('wickets_fallen', e.target.value)} />
          </Field>
        </div>

        {+form.innings === 2 && (
          <Field label="Target">
            <input style={inputStyle} type="number" min={1} value={form.target} onChange={e => set('target', e.target.value)} />
          </Field>
        )}

        <button
          onClick={run}
          disabled={loading}
          style={{
            height: 38, background: '#1a1a1a', color: '#fff', border: 'none',
            borderRadius: 6, fontSize: 13, fontWeight: 500,
            opacity: loading ? 0.6 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
        >
          {loading
            ? <><div style={{ width: 12, height: 12, border: '1.5px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />Predicting…</>
            : 'Predict win probability'
          }
        </button>

        {error && <div style={{ fontSize: 12, color: '#c0392b', padding: '8px 10px', background: '#fdf0ed', borderRadius: 6 }}>{error}</div>}
      </div>

      {result && (
        <div style={{ marginTop: 16, padding: '14px', background: '#fff', border: '1px solid #ebebeb', borderRadius: 8, animation: 'fadeIn 0.2s ease' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
            <span style={{ fontSize: 36, fontWeight: 700, lineHeight: 1, color: isWinning ? '#27ae60' : '#e74c3c' }}>{winPct}%</span>
            <span style={{ fontSize: 13, color: '#666' }}>batting team wins</span>
          </div>

          <div style={{ height: 6, background: '#f0f0f0', borderRadius: 99, overflow: 'hidden', marginBottom: 12 }}>
            <div style={{
              height: '100%', width: `${winPct}%`, borderRadius: 99,
              background: isWinning ? '#27ae60' : '#e74c3c',
              transition: 'width 0.5s ease',
            }} />
          </div>

          {result.derived && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {[
                ['Balls left', result.derived.balls_remaining],
                result.derived.runs_required > 0 && ['Need', result.derived.runs_required + ' runs'],
                result.derived.current_run_rate > 0 && ['CRR', result.derived.current_run_rate],
                result.derived.required_run_rate > 0 && ['RRR', result.derived.required_run_rate],
              ].filter(Boolean).map(([k, v]) => (
                <div key={k} style={{ padding: '6px 8px', background: '#f8f8f7', borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: '#aaa', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>{k}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginTop: 2 }}>{v}</div>
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: 10, fontSize: 11, color: '#bbb' }}>Confidence: {result.confidence}</div>
        </div>
      )}
    </div>
  );
}
