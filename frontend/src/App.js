import React, { useState, useCallback } from 'react';
import MatchPicker from './components/MatchPicker';
import WinProbabilityChart from './components/WinProbabilityChart';
import KeyMomentsPanel from './components/KeyMomentsPanel';
import StateExplorer from './components/StateExplorer';
import { fetchMatch } from './api';

function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#1a1a1a' }}>{value}</div>
    </div>
  );
}

function Divider() {
  return <div style={{ height: 1, background: '#ebebeb', margin: '4px 0' }} />;
}

export default function App() {
  const [selected, setSelected] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeInn, setActiveInn] = useState(1);

  const handleSelect = useCallback(async (match) => {
    setSelected(match);
    setMatchData(null);
    setError(null);
    setLoading(true);
    setActiveInn(1);
    try {
      const data = await fetchMatch(match.id);
      setMatchData(data);
    } catch(e) {
      setError('Could not load match data. Check if the backend is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  const teamA = matchData?.batting_team_1 || selected?.teams?.[0] || '—';
  const teamB = matchData?.batting_team_2 || selected?.teams?.[1] || '—';
  const inn1 = matchData?.innings_1;
  const inn2 = matchData?.innings_2;
  const currentBalls = activeInn === 1 ? inn1?.balls : inn2?.balls;
  const currentMoments = activeInn === 1 ? inn1?.key_moments : inn2?.key_moments;
  const battingTeam = activeInn === 1 ? teamA : teamB;
  const fieldingTeam = activeInn === 1 ? teamB : teamA;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8f8f7' }}>

      {/* Header */}
      <header style={{
        height: 52, borderBottom: '1px solid #e8e8e8', background: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 24px', position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1a1a1a', letterSpacing: '-0.01em' }}>CricketIQ</span>
          <span style={{ fontSize: 11, padding: '2px 7px', background: '#f0f0f0', borderRadius: 99, color: '#666', marginLeft: 2 }}>T20</span>
        </div>
        <div style={{ fontSize: 12, color: '#bbb' }}>Win probability engine</div>
      </header>

      {/* Main */}
      <main style={{ flex: 1, maxWidth: 1200, width: '100%', margin: '0 auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Top bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <MatchPicker selectedMatch={selected} onSelect={handleSelect} />
          {selected && !loading && matchData && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '0 14px', height: 38, background: '#fff', border: '1px solid #ebebeb', borderRadius: 8 }}>
              <Stat label="Date" value={selected.date} />
              <div style={{ width: 1, height: 24, background: '#ebebeb' }} />
              <Stat label="Venue" value={selected.venue || '—'} />
              <div style={{ width: 1, height: 24, background: '#ebebeb' }} />
              <Stat label="Winner" value={selected.winner || 'No result'} />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div style={{ padding: '10px 14px', background: '#fdf0ed', border: '1px solid #f5c6c0', borderRadius: 8, fontSize: 13, color: '#c0392b' }}>
            {error}
          </div>
        )}

        {/* Empty state */}
        {!selected && (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '80px 20px', gap: 10, textAlign: 'center',
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d0d0d0" strokeWidth="1.5">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <div style={{ fontSize: 16, fontWeight: 500, color: '#1a1a1a' }}>Pick a match to get started</div>
            <div style={{ fontSize: 13, color: '#999', maxWidth: 320, lineHeight: 1.6 }}>
              Search across 3,000+ T20 matches and see how win probability shifted ball by ball.
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '60px 0', color: '#999', fontSize: 13 }}>
            <div style={{ width: 14, height: 14, border: '1.5px solid #e0e0e0', borderTopColor: '#1a1a1a', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
            Loading match data…
          </div>
        )}

        {/* Content grid */}
        {matchData && !loading && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16, alignItems: 'start' }}>

            {/* Left — chart + moments */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* Chart card */}
              <div style={{ background: '#fff', border: '1px solid #ebebeb', borderRadius: 10, padding: '18px 20px' }}>

                {/* Teams header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', letterSpacing: '-0.01em' }}>
                    {selected?.teams?.[0]}
                    <span style={{ color: '#ccc', fontWeight: 400, margin: '0 8px' }}>vs</span>
                    {selected?.teams?.[1]}
                  </div>
                  {selected?.winner && (
                    <div style={{ fontSize: 12, padding: '4px 10px', background: '#f0f7f3', border: '1px solid #c3e6d0', borderRadius: 99, color: '#27ae60', fontWeight: 500 }}>
                      {selected.winner} won
                    </div>
                  )}
                </div>

                {/* Innings tabs */}
                <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                  {[1, 2].map(i => {
                    const balls = i === 1 ? inn1?.balls : inn2?.balls;
                    const team = i === 1 ? teamA : teamB;
                    const active = activeInn === i;
                    const score = i === 1 && inn1?.final_score != null ? ` (${inn1.final_score})` : '';
                    return (
                      <button
                        key={i}
                        disabled={!balls?.length}
                        onClick={() => setActiveInn(i)}
                        style={{
                          height: 30, padding: '0 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                          border: active ? '1px solid #1a1a1a' : '1px solid #e0e0e0',
                          background: active ? '#1a1a1a' : '#fff',
                          color: active ? '#fff' : '#666',
                          opacity: balls?.length ? 1 : 0.4,
                          transition: 'all 0.15s',
                        }}
                      >
                        {team} bats{score}
                      </button>
                    );
                  })}
                </div>

                <WinProbabilityChart
                  balls={currentBalls}
                  keyMoments={currentMoments}
                  teamA={battingTeam}
                  teamB={fieldingTeam}
                />

                <div style={{ marginTop: 10, display: 'flex', gap: 16, fontSize: 11, color: '#bbb' }}>
                  <span><span style={{ display: 'inline-block', width: 20, height: 1, background: '#e74c3c', verticalAlign: 'middle', marginRight: 4, opacity: 0.5 }} />Wicket</span>
                  <span><span style={{ display: 'inline-block', width: 20, height: 1, background: '#f39c12', verticalAlign: 'middle', marginRight: 4 }} />Key moment</span>
                  <span style={{ marginLeft: 'auto' }}>{currentBalls?.length || 0} deliveries · hover for details</span>
                </div>
              </div>

              {/* Key moments */}
              <div style={{ background: '#fff', border: '1px solid #ebebeb', borderRadius: 10, padding: '18px 20px' }}>
                <KeyMomentsPanel
                  innings1Moments={inn1?.key_moments}
                  innings2Moments={inn2?.key_moments}
                  balls1={inn1?.balls}
                  balls2={inn2?.balls}
                />
              </div>
            </div>

            {/* Right — sidebar */}
            <div style={{ background: '#fff', border: '1px solid #ebebeb', borderRadius: 10, padding: '18px 20px' }}>
              <StateExplorer />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
