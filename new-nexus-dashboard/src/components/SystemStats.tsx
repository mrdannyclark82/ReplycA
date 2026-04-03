import { useEffect, useRef, useState } from 'react';
import { Activity, Cpu, HardDrive, Wifi, Thermometer, RefreshCw } from 'lucide-react';

interface Stats {
  cpu_percent: number;
  cpu_count: number;
  mem_total_gb: number;
  mem_used_gb: number;
  mem_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_percent: number;
  net_sent_mb: number;
  net_recv_mb: number;
  uptime_secs: number;
  temperatures: Record<string, number>;
  top_procs: Array<{ pid: number; name: string; cpu_percent: number; memory_percent: number }>;
}

const S = {
  root:    { height: '100%', overflowY: 'auto' as const, padding: '12px', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text)' },
  grid:    { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' },
  card:    { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '12px' },
  label:   { color: 'rgba(255,255,255,0.4)', fontSize: '10px', letterSpacing: '1.5px', textTransform: 'uppercase' as const, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '5px' },
  big:     { fontSize: '26px', fontWeight: 900, lineHeight: 1 },
  bar:     { height: '4px', background: 'rgba(255,255,255,0.07)', borderRadius: '2px', overflow: 'hidden' as const, marginTop: '6px' },
  fill:    (pct: number, color: string) => ({ width: `${pct}%`, height: '100%', background: color, borderRadius: '2px', transition: 'width 0.5s ease' }),
  sub:     { color: 'rgba(255,255,255,0.35)', fontSize: '10px', marginTop: '3px' },
  head:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' },
  title:   { fontSize: '12px', color: 'var(--cyan)', letterSpacing: '2px', textTransform: 'uppercase' as const },
  btn:     { background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'rgba(255,255,255,0.5)', padding: '3px 8px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  table:   { width: '100%', borderCollapse: 'collapse' as const },
  th:      { color: 'rgba(255,255,255,0.3)', fontSize: '9px', letterSpacing: '1px', textAlign: 'left' as const, padding: '3px 6px', borderBottom: '1px solid rgba(255,255,255,0.05)' },
  td:      { padding: '4px 6px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.7)' },
  uptime:  { color: 'var(--amber)', fontSize: '10px', textAlign: 'center' as const, padding: '6px', opacity: 0.6 },
};

function fmtUptime(s: number) {
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${d}d ${h}h ${m}m`;
}

function GaugeBar({ pct, color }: { pct: number; color: string }) {
  const warn = pct > 80 ? '#f87171' : pct > 60 ? '#fbbf24' : color;
  return <div style={S.bar}><div style={S.fill(pct, warn)} /></div>;
}

// SERVER: using relative /api/* via Vite proxy

export default function SystemStats() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [prevNet, setPrevNet] = useState<{ sent: number; recv: number } | null>(null);
  const [netRate, setNetRate] = useState<{ up: number; down: number } | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch_ = async () => {
    setLoading(true);
    try {
      const r = await fetch(`/api/system/stats`);
      const d: Stats & { ok: boolean } = await r.json();
      if (d.ok) {
        if (prevNet) {
          setNetRate({
            up:   Math.max(0, (d.net_sent_mb - prevNet.sent) * 1024),
            down: Math.max(0, (d.net_recv_mb - prevNet.recv) * 1024),
          });
        }
        setPrevNet({ sent: d.net_sent_mb, recv: d.net_recv_mb });
        setStats(d);
      }
    } catch { /* silent */ }
    setLoading(false);
  };

  useEffect(() => {
    fetch_();
    intervalRef.current = setInterval(fetch_, 4000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  if (!stats) return (
    <div style={{ ...S.root, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.3)' }}>
      {loading ? 'Loading system stats…' : 'No data'}
    </div>
  );

  return (
    <div style={S.root}>
      <div style={S.head}>
        <span style={S.title}>⚡ System Stats</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={S.uptime}>⏱ {fmtUptime(stats.uptime_secs)}</span>
          <button style={S.btn} onClick={fetch_}><RefreshCw size={9} />{loading ? '…' : 'Refresh'}</button>
        </div>
      </div>

      <div style={S.grid}>
        {/* CPU */}
        <div style={S.card}>
          <div style={S.label}><Cpu size={11} /> CPU</div>
          <div style={{ ...S.big, color: stats.cpu_percent > 80 ? '#f87171' : 'var(--amber)' }}>{stats.cpu_percent.toFixed(0)}<span style={{ fontSize: '12px', opacity: 0.6 }}>%</span></div>
          <GaugeBar pct={stats.cpu_percent} color="var(--amber)" />
          <div style={S.sub}>{stats.cpu_count} cores</div>
        </div>

        {/* RAM */}
        <div style={S.card}>
          <div style={S.label}><Activity size={11} /> RAM</div>
          <div style={{ ...S.big, color: 'var(--cyan)' }}>{stats.mem_percent.toFixed(0)}<span style={{ fontSize: '12px', opacity: 0.6 }}>%</span></div>
          <GaugeBar pct={stats.mem_percent} color="var(--cyan)" />
          <div style={S.sub}>{stats.mem_used_gb} / {stats.mem_total_gb} GB</div>
        </div>

        {/* Disk */}
        <div style={S.card}>
          <div style={S.label}><HardDrive size={11} /> Disk</div>
          <div style={{ ...S.big, color: '#a78bfa' }}>{stats.disk_percent.toFixed(0)}<span style={{ fontSize: '12px', opacity: 0.6 }}>%</span></div>
          <GaugeBar pct={stats.disk_percent} color="#a78bfa" />
          <div style={S.sub}>{stats.disk_used_gb} / {stats.disk_total_gb} GB</div>
        </div>

        {/* Network */}
        <div style={S.card}>
          <div style={S.label}><Wifi size={11} /> Network</div>
          <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 700 }}>
            ↑ {netRate ? `${netRate.up.toFixed(0)} KB/s` : `${stats.net_sent_mb} MB`}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--cyan)', fontWeight: 700, marginTop: '2px' }}>
            ↓ {netRate ? `${netRate.down.toFixed(0)} KB/s` : `${stats.net_recv_mb} MB`}
          </div>
          <div style={S.sub}>total: ↑{stats.net_sent_mb} ↓{stats.net_recv_mb} MB</div>
        </div>
      </div>

      {/* Temperatures */}
      {Object.keys(stats.temperatures ?? {}).length > 0 && (
        <div style={{ ...S.card, marginBottom: '10px' }}>
          <div style={S.label}><Thermometer size={11} /> Temperatures</div>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' as const }}>
            {Object.entries(stats.temperatures ?? {}).map(([k, v]) => (
              <div key={k}>
                <div style={{ color: v > 80 ? '#f87171' : v > 65 ? '#fbbf24' : '#34d399', fontWeight: 700, fontSize: '14px' }}>{v}°C</div>
                <div style={S.sub}>{k}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Processes */}
      <div style={S.card}>
        <div style={S.label}>Top Processes</div>
        <table style={S.table}>
          <thead>
            <tr>
              <th style={S.th}>PID</th>
              <th style={S.th}>Name</th>
              <th style={S.th}>CPU%</th>
              <th style={S.th}>MEM%</th>
            </tr>
          </thead>
          <tbody>
            {(stats.top_procs ?? []).map((p, i) => (
              <tr key={i}>
                <td style={{ ...S.td, color: 'rgba(255,255,255,0.3)' }}>{p.pid}</td>
                <td style={S.td}>{p.name}</td>
                <td style={{ ...S.td, color: (p.cpu_percent || 0) > 20 ? '#fbbf24' : 'rgba(255,255,255,0.6)' }}>{(p.cpu_percent || 0).toFixed(1)}</td>
                <td style={{ ...S.td, color: 'rgba(255,255,255,0.5)' }}>{(p.memory_percent || 0).toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
