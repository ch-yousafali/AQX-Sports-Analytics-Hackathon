import React, { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMatches } from '../api';

export default function MatchPicker({ selectedMatch, onSelect }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [matches, setMatches] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const listRef = useRef(null);
  const timer = useRef(null);
  const wrapRef = useRef(null);

  const load = useCallback(async (q, p) => {
    setLoading(true);
    try {
      const data = await fetchMatches({ page: p, perPage: 40, search: q });
      if (p === 1) setMatches(data.matches);
      else setMatches(prev => [...prev, ...data.matches]);
      setTotal(data.total);
      setHasMore(p < data.total_pages);
    } catch(e) {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (!open) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => { setPage(1); load(search, 1); }, 220);
    return () => clearTimeout(timer.current);
  }, [search, open, load]);

  useEffect(() => {
    const handler = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const onScroll = () => {
    const el = listRef.current;
    if (!el || loading || !hasMore) return;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 60) {
      const next = page + 1; setPage(next); load(search, next);
    }
  };

  const label = selectedMatch ? `${selectedMatch.teams[0]} vs ${selectedMatch.teams[1]}` : 'Select a match';

  return (
    <div ref={wrapRef} style={{ position: 'relative', width: '100%', maxWidth: 480 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 8, padding: '0 12px', height: 38,
          background: '#fff', border: '1px solid #d4d4d4', borderRadius: 8,
          fontSize: 14, color: selectedMatch ? '#1a1a1a' : '#888',
          transition: 'border-color 0.15s',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          {selectedMatch && <span style={{ fontSize: 11, padding: '2px 6px', background: '#f0f0f0', borderRadius: 4, color: '#555' }}>{selectedMatch.format}</span>}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2" style={{ transform: open ? 'rotate(180deg)' : 'none', transition: '0.15s' }}><path d="m6 9 6 6 6-6"/></svg>
        </span>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0, zIndex: 200,
          background: '#fff', border: '1px solid #d4d4d4', borderRadius: 8,
          boxShadow: '0 4px 24px rgba(0,0,0,0.1)', overflow: 'hidden',
          animation: 'fadeIn 0.12s ease',
        }}>
          <div style={{ padding: '8px 10px', borderBottom: '1px solid #ebebeb', display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input
              autoFocus
              placeholder={`Search ${total.toLocaleString()} matches…`}
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, border: 'none', outline: 'none', fontSize: 13, background: 'transparent', color: '#1a1a1a' }}
            />
            {loading && <div style={{ width: 12, height: 12, border: '1.5px solid #ddd', borderTopColor: '#1a1a1a', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />}
          </div>
          <div ref={listRef} onScroll={onScroll} style={{ maxHeight: 300, overflowY: 'auto' }}>
            {matches.length === 0 && !loading && (
              <div style={{ padding: '20px', textAlign: 'center', color: '#999', fontSize: 13 }}>No matches found</div>
            )}
            {matches.map(m => (
              <div
                key={m.id}
                onClick={() => { onSelect(m); setOpen(false); setSearch(''); }}
                style={{
                  padding: '9px 12px', cursor: 'pointer', borderBottom: '1px solid #f5f5f5',
                  background: selectedMatch?.id === m.id ? '#f8f8f7' : '#fff',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#f8f8f7'}
                onMouseLeave={e => e.currentTarget.style.background = selectedMatch?.id === m.id ? '#f8f8f7' : '#fff'}
              >
                <div style={{ fontSize: 13, fontWeight: 500, color: '#1a1a1a', marginBottom: 2 }}>
                  {m.teams[0]} <span style={{ color: '#bbb', fontWeight: 400 }}>vs</span> {m.teams[1]}
                </div>
                <div style={{ fontSize: 11, color: '#999' }}>
                  {m.date} {m.venue ? `· ${m.venue}` : ''} {m.winner ? `· ${m.winner} won` : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
