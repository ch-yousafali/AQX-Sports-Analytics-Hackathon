// src/components/MatchSummaryBar.js
import React from 'react';
import { Trophy, Calendar, MapPin } from 'lucide-react';

const styles = {
  bar: {
    display: 'flex',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 20,
    padding: '14px 20px',
    background: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
  },
  teams: {
    fontFamily: 'var(--font-display)',
    fontWeight: 800,
    fontSize: 20,
    color: 'var(--text-primary)',
    letterSpacing: '-0.02em',
  },
  vs: {
    color: 'var(--text-muted)',
    fontWeight: 600,
    fontSize: 14,
    margin: '0 8px',
  },
  badge: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    fontSize: 12,
    color: 'var(--text-secondary)',
    fontFamily: 'var(--font-mono)',
  },
  winner: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '5px 12px',
    background: 'var(--green-dim)',
    border: '1px solid var(--border-active)',
    borderRadius: 99,
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    color: 'var(--green)',
    fontWeight: 600,
    marginLeft: 'auto',
  },
  scores: {
    display: 'flex',
    gap: 20,
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
    color: 'var(--text-secondary)',
  },
  scoreItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  scoreLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: 'var(--text-muted)',
  },
  scoreVal: {
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
};

export default function MatchSummaryBar({ match, matchData }) {
  if (!match) return null;
  const innings1Score = matchData?.innings_1?.final_score;
  return (
    <div style={styles.bar}>
      <div style={styles.teams}>
        {match.teams[0]}
        <span style={styles.vs}>vs</span>
        {match.teams[1]}
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div style={styles.badge}>
          <Calendar size={12} />
          {match.date}
        </div>
        {match.venue && (
          <div style={styles.badge}>
            <MapPin size={12} />
            {match.venue}
          </div>
        )}
        <div style={{
          ...styles.badge,
          padding: '2px 8px',
          background: 'rgba(0,229,160,0.08)',
          borderRadius: 4,
          color: 'var(--green)',
        }}>
          {match.format}
        </div>
      </div>

      {match.winner && (
        <div style={styles.winner}>
          <Trophy size={11} />
          {match.winner} won
        </div>
      )}
    </div>
  );
}
