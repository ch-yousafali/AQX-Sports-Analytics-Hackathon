import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload, teamA, teamB }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  const prob = d.win_prob;
  const winPct = Math.round(prob * 100);
  const losePct = 100 - winPct;
  return (
    <div style={{
      background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8,
      padding: '10px 13px', fontSize: 12, minWidth: 160,
      boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: '#1a1a1a' }}>Over {d.over}.{d.delivery}</div>
      <div style={{ color: '#555', marginBottom: 2 }}>Score: <strong style={{ color: '#1a1a1a' }}>{d.score}</strong></div>
      {d.is_wicket && <div style={{ color: '#c0392b', fontWeight: 500, marginBottom: 2 }}>Wicket</div>}
      {d.runs_this_ball > 0 && <div style={{ color: '#555', marginBottom: 6 }}>+{d.runs_this_ball} runs</div>}
      <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 6, marginTop: 2 }}>
        <div style={{ color: '#1a1a1a' }}>{teamA}: <strong>{winPct}%</strong></div>
        <div style={{ color: '#999' }}>{teamB}: {losePct}%</div>
      </div>
    </div>
  );
};

export default function WinProbabilityChart({ balls, keyMoments, teamA, teamB }) {
  if (!balls || balls.length === 0) {
    return <div style={{ padding: '40px 0', textAlign: 'center', color: '#bbb', fontSize: 13 }}>No data for this innings</div>;
  }

  const data = balls.map(b => ({
    ...b,
    win_prob_pct: Math.round(b.win_prob * 100),
  }));

  const momentSet = new Set((keyMoments || []).map(k => k[0]));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 4, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="probGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1a1a1a" stopOpacity={0.12} />
            <stop offset="100%" stopColor="#1a1a1a" stopOpacity={0.01} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
        <XAxis
          dataKey="ball_num"
          tick={{ fill: '#bbb', fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: '#ebebeb' }}
        />
        <YAxis
          domain={[0, 100]}
          tickFormatter={v => `${v}%`}
          tick={{ fill: '#bbb', fontSize: 10 }}
          tickLine={false}
          axisLine={false}
        />
        <ReferenceLine y={50} stroke="#e0e0e0" strokeDasharray="4 4" />
        <Tooltip content={<CustomTooltip teamA={teamA} teamB={teamB} />} />
        <Area
          type="monotone"
          dataKey="win_prob_pct"
          stroke="#1a1a1a"
          strokeWidth={1.5}
          fill="url(#probGrad)"
          dot={false}
          activeDot={{ r: 4, fill: '#1a1a1a', stroke: '#fff', strokeWidth: 2 }}
        />
        {data.filter(d => d.is_wicket).map(d => (
          <ReferenceLine key={`w-${d.ball_num}`} x={d.ball_num} stroke="#e74c3c" strokeWidth={1} strokeOpacity={0.4} />
        ))}
        {data.filter(d => momentSet.has(d.ball_num)).map(d => (
          <ReferenceLine key={`m-${d.ball_num}`} x={d.ball_num} stroke="#f39c12" strokeWidth={1.5} strokeOpacity={0.6} strokeDasharray="2 2" />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
