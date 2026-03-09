import { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, Play, ChevronDown, ChevronUp, Clock, Plus } from 'lucide-react';

interface CronJob {
  id: string;
  name: string;
  schedule: string;
  script: string;
  log_tail: string;
}

export default function CronManager() {
  const [jobs, setJobs] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [logs, setLogs] = useState<Record<string, string>>({});
  const [showNew, setShowNew]     = useState(false);
  const [newSchedule, setNewSchedule] = useState('0 6 * * *');
  const [newCommand, setNewCommand]   = useState('');
  const [newLabel, setNewLabel]       = useState('');
  const [creating, setCreating]       = useState(false);
  const [createMsg, setCreateMsg]     = useState<{ ok: boolean; text: string } | null>(null);

  const fetchJobs = () => {
    axios.get('/api/cron/list')
      .then(r => { setJobs(r.data.jobs || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchJobs(); }, []);

  const trigger = async (id: string) => {
    setTriggering(id);
    try {
      await axios.post('/api/cron/trigger', { job_id: id });
      setTimeout(fetchJobs, 2000);
    } catch {}
    setTriggering(null);
  };

  const toggleLogs = async (id: string) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    if (!logs[id]) {
      try {
        const r = await axios.get(`/api/cron/${id}/logs?lines=40`);
        setLogs(prev => ({ ...prev, [id]: r.data.log || '[no logs]' }));
      } catch {
        setLogs(prev => ({ ...prev, [id]: '[error loading logs]' }));
      }
    }
  };

  const createJob = async () => {
    if (!newCommand.trim()) { setCreateMsg({ ok: false, text: 'Command is required' }); return; }
    setCreating(true); setCreateMsg(null);
    try {
      const r = await axios.post('/api/cron/create', { schedule: newSchedule, command: newCommand, label: newLabel });
      if (r.data.ok) {
        setCreateMsg({ ok: true, text: `✓ Added: ${r.data.line}` });
        setNewCommand(''); setNewLabel(''); setShowNew(false);
        fetchJobs();
      } else {
        setCreateMsg({ ok: false, text: r.data.error || 'Failed' });
      }
    } catch (e: unknown) { setCreateMsg({ ok: false, text: String(e) }); }
    setCreating(false);
  };

  return (
    <div className="h-full flex flex-col gap-3 overflow-y-auto">
      <div className="flex items-center justify-between">
        <p className="text-[9px] uppercase tracking-[0.4em] opacity-40" style={{ color: 'var(--cyan)' }}>
          ⟳ {jobs.length} Scheduled Jobs
        </p>
        <div className="flex items-center gap-2">
          <button onClick={() => { setShowNew(n => !n); setCreateMsg(null); }}
            className="flex items-center gap-1 opacity-60 hover:opacity-100 text-[9px] uppercase tracking-widest px-2 py-1 rounded"
            style={{ color: '#34d399', border: '1px solid rgba(52,211,153,0.3)' }}>
            <Plus size={9} />New Job
          </button>
          <button onClick={fetchJobs} className="opacity-40 hover:opacity-80">
            <RefreshCw size={11} style={{ color: 'var(--cyan)' }} />
          </button>
        </div>
      </div>

      {/* New Job form */}
      {showNew && (
        <div style={{ background: 'rgba(52,211,153,0.04)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: 12, fontSize: 11 }}>
          <div style={{ marginBottom: 6, color: '#34d399', fontSize: 10, letterSpacing: '1.5px', textTransform: 'uppercase' }}>New Cron Job</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', marginBottom: 2 }}>Schedule (5 fields)</div>
                <input value={newSchedule} onChange={e => setNewSchedule(e.target.value)}
                  style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#fff', padding: '4px 8px', fontFamily: 'monospace', fontSize: 11 }}
                  placeholder="0 6 * * *" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', marginBottom: 2 }}>Label (optional)</div>
                <input value={newLabel} onChange={e => setNewLabel(e.target.value)}
                  style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#fff', padding: '4px 8px', fontFamily: 'monospace', fontSize: 11 }}
                  placeholder="My job" />
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', marginBottom: 2 }}>Command</div>
              <input value={newCommand} onChange={e => setNewCommand(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') createJob(); }}
                style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: '#fff', padding: '4px 8px', fontFamily: 'monospace', fontSize: 11 }}
                placeholder="cd /home/nexus/ogdray && venv/bin/python3 my_script.py" />
            </div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <button onClick={createJob} disabled={creating}
                style={{ background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: 4, color: '#34d399', padding: '4px 12px', cursor: 'pointer', fontSize: 10 }}>
                {creating ? 'Adding…' : 'Add Job'}
              </button>
              <button onClick={() => { setShowNew(false); setCreateMsg(null); }}
                style={{ background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 4, color: 'rgba(255,255,255,0.4)', padding: '4px 10px', cursor: 'pointer', fontSize: 10 }}>
                Cancel
              </button>
              {createMsg && <span style={{ fontSize: 10, color: createMsg.ok ? '#34d399' : '#f87171' }}>{createMsg.text}</span>}
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-[10px] opacity-40" style={{ color: 'var(--cyan)' }}>Loading cron jobs...</p>
      ) : (
        <div className="flex flex-col gap-2">
          {jobs.map(job => (
            <div key={job.id} className="glass rounded-lg overflow-hidden" style={{ border: '1px solid rgba(245,158,11,0.15)' }}>
              <div className="flex items-center gap-3 px-3 py-2">
                <Clock size={11} style={{ color: 'var(--amber)', flexShrink: 0 }} />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-bold truncate neon-amber">{job.name}</p>
                  <p className="text-[8px] opacity-40 font-mono" style={{ color: 'var(--cyan)' }}>{job.schedule}</p>
                </div>
                <button
                  onClick={() => trigger(job.id)}
                  disabled={triggering === job.id}
                  className="p-1.5 rounded border text-[9px] uppercase tracking-widest flex items-center gap-1"
                  style={{ color: 'var(--green)', borderColor: 'rgba(34,197,94,0.4)', opacity: triggering === job.id ? 0.4 : 1 }}>
                  <Play size={8} />
                  {triggering === job.id ? '...' : 'Run'}
                </button>
                <button onClick={() => toggleLogs(job.id)} className="opacity-40 hover:opacity-80 ml-1">
                  {expanded === job.id
                    ? <ChevronUp size={11} style={{ color: 'var(--cyan)' }} />
                    : <ChevronDown size={11} style={{ color: 'var(--cyan)' }} />}
                </button>
              </div>
              {expanded === job.id && (
                <div className="px-3 pb-2 pt-1 border-t" style={{ borderColor: 'rgba(245,158,11,0.1)' }}>
                  <pre className="text-[8px] opacity-50 font-mono whitespace-pre-wrap overflow-auto max-h-32"
                    style={{ color: 'var(--cyan)' }}>
                    {logs[job.id] || 'Loading...'}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
