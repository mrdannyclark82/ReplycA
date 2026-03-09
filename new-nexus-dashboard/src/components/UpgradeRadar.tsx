import { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RefreshCw, Zap, ChevronDown, ChevronUp, Clock } from 'lucide-react';

const SERVER = import.meta.env.VITE_SERVER_URL ?? 'http://100.89.122.112:8000';

interface Scan {
  heading: string;
  date: string;
  brief: string;
  systemUpdates: string[];
  rawExpanded: boolean;
  raw: string;
}

function parseMd(content: string): Scan[] {
  const sections = content.split(/^## /m).filter(Boolean);
  return sections.map(sec => {
    const lines = sec.split('\n');
    const heading = lines[0].trim();
    const dateMatch = heading.match(/\d{4}-\d{2}-\d{2}[^\n]*/);
    const date = dateMatch ? dateMatch[0] : heading;

    // Extract intelligence brief
    const briefIdx = sec.indexOf('**Intelligence Brief:**');
    let brief = '';
    if (briefIdx !== -1) {
      const afterBrief = sec.slice(briefIdx + 22);
      const rawIdx = afterBrief.indexOf('<details');
      brief = (rawIdx !== -1 ? afterBrief.slice(0, rawIdx) : afterBrief).trim();
      // Remove leading **Summary:** if present
      brief = brief.replace(/^\*\*Summary:\*\*\s*/i, '').trim();
    }

    // Extract system update list
    const sysUpdates: string[] = [];
    const sysMatch = sec.match(/\*\*System:\*\*[^\n]*\n((?:\s+-[^\n]+\n?)+)/);
    if (sysMatch) {
      sysMatch[1].split('\n').forEach(l => {
        const m = l.match(/^\s+-\s+(.+)/);
        if (m) sysUpdates.push(m[1].trim());
      });
    }

    // Extract raw details content
    const rawMatch = sec.match(/<details>[\s\S]*?<summary>[^<]*<\/summary>([\s\S]*?)<\/details>/);
    const raw = rawMatch ? rawMatch[1].trim() : '';

    return { heading, date, brief, systemUpdates: sysUpdates, rawExpanded: false, raw };
  });
}

export default function UpgradeRadar() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState('');
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const fetchRadar = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${SERVER}/api/files/read`, {
        params: { path: 'core_os/memory/upgrade_radar.md' }
      });
      const content = r.data.content || r.data.text || r.data || '';
      setScans(parseMd(typeof content === 'string' ? content : JSON.stringify(content)).reverse());
    } catch {
      setScans([]);
    }
    setLoading(false);
  };

  useEffect(() => { fetchRadar(); }, []);

  const runNow = async () => {
    setRunning(true);
    setRunMsg('');
    try {
      const r = await axios.post(`${SERVER}/api/cron/trigger`, { job_id: 'upgrade' });
      setRunMsg(r.data.ok ? '✅ Scan complete. Refreshing...' : `❌ ${r.data.error}`);
      if (r.data.ok) setTimeout(() => { fetchRadar(); setRunMsg(''); }, 1500);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setRunMsg(`❌ ${msg}`);
    }
    setRunning(false);
  };

  const toggleExpand = (i: number) => setExpanded(prev => ({ ...prev, [i]: !prev[i] }));

  return (
    <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: 12, fontFamily: 'monospace' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Radar size={16} style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 6px rgba(6,182,212,0.8))' }} />
          <span style={{ color: 'var(--cyan)', fontWeight: 700, fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Upgrade Radar
          </span>
          <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.2em' }}>
            / TECH INTEL
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            onClick={fetchRadar}
            disabled={loading}
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.5)', padding: '4px 8px', borderRadius: 4, cursor: 'pointer', fontSize: 10, display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <RefreshCw size={10} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button
            onClick={runNow}
            disabled={running}
            style={{ background: running ? 'rgba(6,182,212,0.1)' : 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.4)', color: 'var(--cyan)', padding: '4px 10px', borderRadius: 4, cursor: running ? 'wait' : 'pointer', fontSize: 10, display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600 }}
          >
            <Zap size={10} /> {running ? 'Scanning...' : 'Run Now'}
          </button>
        </div>
      </div>

      {runMsg && (
        <div style={{ fontSize: 11, padding: '6px 10px', borderRadius: 4, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: runMsg.startsWith('✅') ? '#34d399' : '#f87171' }}>
          {runMsg}
        </div>
      )}

      {loading ? (
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, textAlign: 'center', padding: 20 }}>Loading radar data...</div>
      ) : scans.length === 0 ? (
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, textAlign: 'center', padding: 20 }}>
          No scans yet. Click "Run Now" to perform the first tech intel scan.
        </div>
      ) : (
        scans.map((scan, i) => (
          <div key={i} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(6,182,212,0.15)', borderRadius: 6, overflow: 'hidden' }}>
            {/* Scan header */}
            <button
              onClick={() => toggleExpand(i)}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={11} style={{ color: 'var(--cyan)', opacity: 0.7 }} />
                <span style={{ fontSize: 11, color: 'var(--cyan)', fontWeight: 600 }}>{scan.date}</span>
                {i === 0 && (
                  <span style={{ fontSize: 8, background: 'rgba(6,182,212,0.2)', color: 'var(--cyan)', padding: '1px 6px', borderRadius: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>LATEST</span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {scan.systemUpdates.length > 0 && (
                  <span style={{ fontSize: 9, color: '#fbbf24', opacity: 0.8 }}>{scan.systemUpdates.length} pkg updates</span>
                )}
                {expanded[i] ? <ChevronUp size={12} style={{ color: 'rgba(255,255,255,0.3)' }} /> : <ChevronDown size={12} style={{ color: 'rgba(255,255,255,0.3)' }} />}
              </div>
            </button>

            {/* Always show brief preview for latest */}
            {(i === 0 || expanded[i]) && (
              <div style={{ padding: '0 12px 12px' }}>
                {scan.brief && (
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', lineHeight: 1.6, marginBottom: scan.systemUpdates.length > 0 ? 10 : 0 }}>
                    {scan.brief.split('\n').filter(Boolean).map((line, li) => {
                      // Bold **text** patterns
                      const parts = line.split(/(\*\*[^*]+\*\*)/g);
                      return (
                        <p key={li} style={{ margin: '2px 0' }}>
                          {parts.map((p, pi) =>
                            p.startsWith('**') ? <strong key={pi} style={{ color: 'rgba(255,255,255,0.9)' }}>{p.replace(/\*\*/g, '')}</strong> : p
                          )}
                        </p>
                      );
                    })}
                  </div>
                )}

                {scan.systemUpdates.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 6 }}>
                      System Packages ({scan.systemUpdates.length})
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {scan.systemUpdates.map((pkg, pi) => {
                        const [name, ...rest] = pkg.split(' ');
                        return (
                          <span key={pi} style={{ fontSize: 9, background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.2)', color: '#fbbf24', padding: '2px 6px', borderRadius: 4 }} title={rest.join(' ')}>
                            {name}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
