import { useEffect, useState } from 'react';
import { GitBranch, GitCommit, RefreshCw, Download, Plus } from 'lucide-react';

interface Commit { hash: string; subject: string; author: string; ago: string; }

const S = {
  root:    { height: '100%', overflowY: 'auto' as const, padding: '12px', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text)' },
  head:    { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' as const },
  title:   { color: '#a78bfa', letterSpacing: '2px', textTransform: 'uppercase' as const, fontSize: '11px' },
  btn:     { background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'rgba(255,255,255,0.5)', padding: '3px 8px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  card:    { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '10px 12px', marginBottom: '8px' },
  label:   { color: 'rgba(255,255,255,0.3)', fontSize: '9px', letterSpacing: '1.5px', textTransform: 'uppercase' as const, marginBottom: '4px' },
  badge:   (c: string) => ({ background: `${c}22`, border: `1px solid ${c}44`, borderRadius: '4px', color: c, fontSize: '9px', padding: '1px 6px', letterSpacing: '1px' }),
  diff:    { background: 'rgba(0,0,0,0.3)', borderRadius: '4px', padding: '8px', fontSize: '10px', lineHeight: '1.6', maxHeight: '200px', overflowY: 'auto' as const, whiteSpace: 'pre-wrap' as const },
  input:   { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: '#fff', padding: '5px 8px', fontSize: '11px', width: '100%', outline: 'none', fontFamily: 'monospace' },
  commitRow:{ padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', display: 'flex', gap: '8px', alignItems: 'flex-start' },
  hash:    { color: '#60a5fa', fontSize: '10px', flexShrink: 0, fontFamily: 'monospace' },
  msg:     { ok: false } as const,
};

// SERVER: using relative /api/* via Vite proxy

export default function GitPanel() {
  const [status, setStatus]   = useState<{ status: string; branch: string; remote: string } | null>(null);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [pulling, setPulling] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [commitMsg, setCommitMsg]   = useState('');
  const [output, setOutput]   = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [sr, lr] = await Promise.all([
        fetch(`/api/git/status`).then(r => r.json()),
        fetch(`/api/git/log?n=20`).then(r => r.json()),
      ]);
      if (sr.ok !== undefined) setStatus(sr);
      if (lr.ok !== undefined) setCommits(lr.commits || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const pull = async () => {
    setPulling(true); setOutput('');
    try {
      const r = await fetch(`/api/git/pull`, { method: 'POST' });
      const d = await r.json();
      setOutput(d.output || (d.ok ? 'Already up to date.' : 'Pull failed'));
      if (d.ok) refresh();
    } catch (e) { setOutput(String(e)); }
    setPulling(false);
  };

  const commit = async () => {
    if (!commitMsg.trim()) return;
    setCommitting(true); setOutput('');
    try {
      const r = await fetch(`/api/git/commit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: commitMsg }),
      });
      const d = await r.json();
      setOutput(d.output || (d.ok ? 'Committed.' : 'Commit failed'));
      if (d.ok) { setCommitMsg(''); refresh(); }
    } catch (e) { setOutput(String(e)); }
    setCommitting(false);
  };

  return (
    <div style={S.root}>
      <div style={S.head}>
        <span style={S.title}>⎇ Git</span>
        <button style={S.btn} onClick={refresh}><RefreshCw size={9} />{loading ? '…' : 'Refresh'}</button>
        <button style={{ ...S.btn, color: '#60a5fa' }} onClick={pull} disabled={pulling}>
          <Download size={9} />{pulling ? 'Pulling…' : 'Pull'}
        </button>
      </div>

      {/* Status */}
      {status && (
        <div style={S.card}>
          <div style={S.label}>Status</div>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' as const }}>
            <span style={S.badge('#a78bfa')}><GitBranch size={9} style={{ display: 'inline', marginRight: '3px' }} />{status.branch}</span>
            <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', alignSelf: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>{status.remote}</span>
          </div>
          {status.status
            ? <div style={S.diff}>{status.status}</div>
            : <div style={{ color: '#34d399', fontSize: '10px' }}>✓ Working tree clean</div>
          }
        </div>
      )}

      {/* Commit */}
      <div style={S.card}>
        <div style={S.label}><Plus size={9} style={{ display: 'inline', marginRight: '3px' }} />Commit All Changes</div>
        <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
          <input
            style={S.input}
            placeholder="Commit message…"
            value={commitMsg}
            onChange={e => setCommitMsg(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') commit(); }}
          />
          <button style={{ ...S.btn, color: '#34d399', border: '1px solid rgba(52,211,153,0.3)', flexShrink: 0 }}
                  onClick={commit} disabled={committing || !commitMsg.trim()}>
            <GitCommit size={9} />{committing ? '…' : 'Commit'}
          </button>
        </div>
      </div>

      {/* Output */}
      {output && (
        <div style={{ ...S.card, marginBottom: '8px' }}>
          <div style={S.label}>Output</div>
          <div style={S.diff}>{output}</div>
        </div>
      )}

      {/* Log */}
      <div style={S.card}>
        <div style={S.label}><GitCommit size={9} style={{ display: 'inline', marginRight: '3px' }} />Recent Commits ({commits.length})</div>
        {commits.length === 0
          ? <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: '10px', padding: '4px 0' }}>No commits found</div>
          : commits.map((c, i) => (
            <div key={i} style={S.commitRow}>
              <span style={S.hash}>{c.hash}</span>
              <span style={{ flex: 1, color: 'rgba(255,255,255,0.7)', fontSize: '10px', lineHeight: '1.4' }}>{c.subject}</span>
              <span style={{ color: 'rgba(255,255,255,0.25)', fontSize: '9px', flexShrink: 0 }}>{c.ago}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
}
