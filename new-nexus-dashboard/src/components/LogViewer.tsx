import { useEffect, useRef, useState } from 'react';
import { RefreshCw, Play, Square } from 'lucide-react';

interface LogMeta { name: string; path: string; size_kb: number; exists: boolean; }

const S = {
  root:   { height: '100%', display: 'flex', flexDirection: 'column' as const, fontFamily: 'monospace', fontSize: '11px', color: 'var(--text)' },
  head:   { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)', flexWrap: 'wrap' as const },
  title:  { color: 'var(--amber)', letterSpacing: '2px', textTransform: 'uppercase' as const, fontSize: '11px' },
  select: { background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: '#fff', padding: '3px 6px', fontSize: '10px', cursor: 'pointer' },
  btn:    { background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'rgba(255,255,255,0.5)', padding: '3px 8px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  meta:   { marginLeft: 'auto', color: 'rgba(255,255,255,0.3)', fontSize: '9px' },
  body:   { flex: 1, overflowY: 'auto' as const, padding: '10px 12px', background: 'rgba(0,0,0,0.25)' },
  line:   (txt: string) => ({
    padding: '1px 0',
    color: txt.toLowerCase().includes('error') || txt.toLowerCase().includes('traceback')
      ? '#f87171'
      : txt.toLowerCase().includes('warn')
      ? '#fbbf24'
      : txt.includes('[heartbeat]')
      ? 'rgba(255,255,255,0.15)'
      : 'rgba(255,255,255,0.65)',
    fontSize: '10px',
    lineHeight: '1.5',
    wordBreak: 'break-all' as const,
  }),
};

// SERVER: using relative /api/* via Vite proxy

export default function LogViewer() {
  const [logs, setLogs]         = useState<LogMeta[]>([]);
  const [selected, setSelected] = useState('nexus-server');
  const [lines, setLines]       = useState<string[]>([]);
  const [streaming, setStreaming]= useState(false);
  const [autoScroll, setAutoScroll]= useState(true);
  const bodyRef  = useRef<HTMLDivElement>(null);
  const esRef    = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch(`/api/logs/list`).then(r => r.json()).then(d => { if (d.ok) setLogs(d.logs); });
  }, []);

  const loadTail = async () => {
    stopStream();
    try {
      const r = await fetch(`/api/logs/tail?file=${selected}&lines=200`);
      const d = await r.json();
      if (d.ok) setLines(d.content.split('\n').filter(Boolean));
    } catch { /* ignore */ }
  };

  useEffect(() => { loadTail(); }, [selected]);

  const stopStream = () => {
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    setStreaming(false);
  };

  const startStream = () => {
    stopStream();
    const es = new EventSource(`/api/logs/stream?file=${selected}`);
    esRef.current = es;
    setStreaming(true);
    es.onmessage = (e) => {
      setLines(prev => [...prev.slice(-800), e.data]);
    };
    es.onerror = () => { stopStream(); };
  };

  useEffect(() => {
    if (autoScroll && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines, autoScroll]);

  useEffect(() => () => stopStream(), []);

  const meta = logs.find(l => l.name === selected);

  return (
    <div style={S.root}>
      <div style={S.head}>
        <span style={S.title}>📋 Logs</span>
        <select style={S.select} value={selected} onChange={e => setSelected(e.target.value)}>
          {logs.map(l => (
            <option key={l.name} value={l.name} disabled={!l.exists}>
              {l.name}{!l.exists ? ' (missing)' : ''}
            </option>
          ))}
        </select>
        <button style={S.btn} onClick={loadTail}><RefreshCw size={9} />Reload</button>
        {!streaming
          ? <button style={{ ...S.btn, color: '#34d399' }} onClick={startStream}><Play size={9} />Stream</button>
          : <button style={{ ...S.btn, color: '#f87171' }} onClick={stopStream}><Square size={9} />Stop</button>
        }
        <label style={{ ...S.btn, cursor: 'pointer' }}>
          <input type="checkbox" checked={autoScroll} onChange={e => setAutoScroll(e.target.checked)} style={{ marginRight: '3px' }} />
          Auto-scroll
        </label>
        {meta && <span style={S.meta}>{meta.size_kb} KB</span>}
        {streaming && <span style={{ ...S.meta, color: '#34d399', animation: 'pulse 1s infinite' }}>● LIVE</span>}
      </div>

      <div ref={bodyRef} style={S.body}>
        {lines.length === 0
          ? <div style={{ color: 'rgba(255,255,255,0.2)', paddingTop: '20px', textAlign: 'center' }}>No log content</div>
          : lines.map((l, i) => <div key={i} style={S.line(l)}>{l}</div>)
        }
      </div>
    </div>
  );
}
