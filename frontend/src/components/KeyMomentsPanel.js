import React from 'react';

function ballToOver(ballNum) {
  const over = Math.floor((ballNum - 1) / 6);
  const ball = ((ballNum - 1) % 6) + 1;
  return `${over}.${ball}`;
}

export default function KeyMomentsPanel({ innings1Moments, innings2Moments, balls1, balls2 }) {
  const all = [
    ...(innings1Moments || []).map(m => ({ m, innings: 1 })),
    ...(innings2Moments || []).map(m => ({ m, innings: 2 })),
  ]
    .sort((a, b) => b.m[1] - a.m[1])
    .slice(0, 5);

  if (all.length === 0) return null;

  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#999', marginBottom: 10 }}>
        Key moments
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {all.map(({ m, innings }, i) => {
          const [ballIdx, delta, probAfter] = m;
          const balls = innings === 1 ? balls1 : balls2;
          const ball = balls?.[ballIdx - 1];
          const swing = Math.round(delta * 100);
          const up = probAfter > (probAfter - delta);

          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 12px', background: '#fff', borderRadius: 6,
              border: '1px solid #ebebeb',
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                background: '#f5f5f5', display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 11, color: '#888', fontWeight: 600,
              }}>
                {i + 1}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: '#1a1a1a' }}>
                  Over {ballToOver(ballIdx)}
                  {ball?.is_wicket ? ' · Wicket' : ball?.runs_this_ball > 5 ? ` · ${ball.runs_this_ball} runs` : ''}
                  <span style={{ fontSize: 11, color: '#bbb', fontWeight: 400, marginLeft: 6 }}>Inn. {innings}</span>
                </div>
                {ball?.score && <div style={{ fontSize: 11, color: '#999' }}>{ball.score}</div>}
              </div>
              <div style={{
                fontSize: 14, fontWeight: 600,
                color: up ? '#27ae60' : '#e74c3c',
                flexShrink: 0,
              }}>
                {up ? '+' : '-'}{swing}%
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
