import { useEffect, useState } from 'react';
import { Archive, RefreshCw, Plus } from 'lucide-react';

interface Backup { name: string; size_mb: number; created: number; }

const S = {
  root:  { height: '100%', overflowY: 'auto' as const, padding: '12px', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text)' },
  head:  { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' },
  title: { color: '#34d399', letterSpacing: '2px', textTransform: 'uppercase' as const, fontSize: '11px' },
  btn:   { background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'rgba(255,255,255,0.5)', padding: '3px 8px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  newBtn:{ background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: '4px', color: '#34d399', padding: '4px 12px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  card:  { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '10px 12px', marginBottom: '8px' },
  label: { color: 'rgba(255,255,255,0.3)', fontSize: '9px', letterSpacing: '1.5px', textTransform: 'uppercase' as const, marginBottom: '6px' },
  row:   { display: 'flex', alignItems: 'center', gap: '8px', padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' },
  name:  { flex: 1, color: 'rgba(255,255,255,0.7)', fontSize: '10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  info:  { background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: '6px', padding: '8px 12px', marginBottom: '10px', fontSize: '10px', color: '#34d399' },
  err:   { background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', borderRadius: '6px', padding: '8px 12px', marginBottom: '10px', fontSize: '10px', color: '#f87171' },
};

function fmtDate(ts: number) {
  return new Date(ts * 1000).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
}

// SERVER: using relative /api/* via Vite proxy

export default function BackupPanel() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [creating, setCreating] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [msg, setMsg]           = useState<{ ok: boolean; text: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/backup/list`);
      const d = await r.json();
      if (d.ok) setBackups(d.backups);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    setCreating(true); setMsg(null);
    try {
      const r = await fetch(`/api/backup/create`, { method: 'POST' });
      const d = await r.json();
      if (d.ok) {
        setMsg({ ok: true, text: `✓ Backup created: ${d.name} (${d.size_mb} MB)` });
        load();
      } else {
        setMsg({ ok: false, text: d.error || 'Backup failed' });
      }
    } catch (e) { setMsg({ ok: false, text: String(e) }); }
    setCreating(false);
  };

  return (
    <div style={S.root}>
      <div style={S.head}>
        <span style={S.title}>💾 Backups</span>
        <button style={S.btn} onClick={load}><RefreshCw size={9} />{loading ? '…' : 'Refresh'}</button>
        <button style={S.newBtn} onClick={create} disabled={creating}>
          <Plus size={9} />{creating ? 'Creating…' : 'New Backup'}
        </button>
      </div>

      {msg && <div style={msg.ok ? S.info : S.err}>{msg.text}</div>}

      <div style={S.card}>
        <div style={S.label}><Archive size={9} style={{ display: 'inline', marginRight: '4px' }} />What's Backed Up</div>
        <ul style={{ margin: 0, padding: '0 0 0 16px', color: 'rgba(255,255,255,0.5)', fontSize: '10px', lineHeight: '1.8' }}>
          <li>core_os/memory/milla_long_term.db (9,405+ memories)</li>
          <li>core_os/memory/neuro_state.json</li>
          <li>core_os/memory/persona_override.txt</li>
          <li>.env (API keys)</li>
        </ul>
        <div style={{ marginTop: '6px', fontSize: '9px', color: 'rgba(255,255,255,0.25)' }}>
          Saved to: ~/milla_backups/
        </div>
      </div>

      <div style={S.card}>
        <div style={S.label}>Backup History ({backups.length})</div>
        {backups.length === 0
          ? <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: '10px', padding: '4px 0' }}>
              {loading ? 'Loading…' : 'No backups yet — create one!'}
            </div>
          : backups.map((b, i) => (
            <div key={i} style={S.row}>
              <Archive size={10} color="#34d399" />
              <span style={S.name}>{b.name}</span>
              <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '9px', flexShrink: 0 }}>{b.size_mb} MB</span>
              <span style={{ color: 'rgba(255,255,255,0.25)', fontSize: '9px', flexShrink: 0 }}>{fmtDate(b.created)}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
}
