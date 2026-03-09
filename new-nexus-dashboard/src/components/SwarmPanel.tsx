import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Bot, Play, RefreshCw, Zap, ShieldAlert, Code2, Search, BookOpen, MessageSquareCode, TriangleAlert, Trash2, ChevronDown, ChevronRight, Activity } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  script: string;
  schedule: string;
  type: 'security' | 'dev' | 'analysis' | 'memory';
  running: boolean;
  last_run: string;
}

interface Flag {
  timestamp: string;
  agent: string;
  details: string;
  level: 'low' | 'medium' | 'high' | 'critical';
  status: string;
}

interface SwarmStatus {
  agents: Agent[];
  flags_count: number;
  flags_recent: Flag[];
  latest_report: Record<string, unknown> | null;
  swarm_active: boolean;
}

const TYPE_ICON: Record<string, React.ReactNode> = {
  security: <ShieldAlert size={11} />,
  dev:      <Code2 size={11} />,
  analysis: <Search size={11} />,
  memory:   <BookOpen size={11} />,
};

const TYPE_COLOR: Record<string, string> = {
  security: 'rgba(244,63,94,',
  dev:      'rgba(6,182,212,',
  analysis: 'rgba(168,85,247,',
  memory:   'rgba(34,197,94,',
};

const LEVEL_COLOR: Record<string, string> = {
  low:      '#22c55e',
  medium:   '#f59e0b',
  high:     '#f97316',
  critical: '#ef4444',
};

const SwarmPanel: React.FC = () => {
  const [status, setStatus]       = useState<SwarmStatus | null>(null);
  const [log, setLog]             = useState('');
  const [flags, setFlags]         = useState<Flag[]>([]);
  const [loading, setLoading]     = useState(false);
  const [launching, setLaunching] = useState<string | null>(null);
  const [showLog, setShowLog]     = useState(false);
  const [showFlags, setShowFlags] = useState(true);
  const [taskInput, setTaskInput] = useState<Record<string, string>>({});
  const [dispatching, setDispatching] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [s, f, l] = await Promise.all([
        axios.get<SwarmStatus>('/api/swarm/status'),
        axios.get<{flags: Flag[]}>('/api/swarm/flags?limit=20'),
        axios.get<{log: string}>('/api/swarm/log?lines=80'),
      ]);
      setStatus(s.data);
      setFlags(f.data.flags.reverse());
      setLog(l.data.log);
    } catch (_) {}
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  const dispatch = async (agentId: string) => {
    setLaunching(agentId);
    try {
      const payload: Record<string, unknown> = {};
      const task = taskInput[agentId];
      if (task) {
        payload.query = task;
        payload.task  = task;
        setTaskInput(p => ({ ...p, [agentId]: '' }));
      }
      await axios.post('/api/swarm/dispatch', { agent_id: agentId, payload });
      setTimeout(refresh, 1500);
    } catch (_) {}
    setLaunching(null);
  };

  const dispatchAll = async () => {
    setDispatching(true);
    try {
      await axios.post('/api/swarm/dispatch_all');
      setTimeout(refresh, 2000);
    } catch (_) {}
    setDispatching(false);
  };

  const clearFlags = async () => {
    await axios.delete('/api/swarm/flags');
    setFlags([]);
    setStatus(s => s ? { ...s, flags_count: 0, flags_recent: [] } : s);
  };

  const grouped = status?.agents.reduce<Record<string, Agent[]>>((acc, ag) => {
    (acc[ag.type] = acc[ag.type] || []).push(ag);
    return acc;
  }, {}) ?? {};

  return (
    <div className="flex flex-col h-full gap-3 overflow-y-auto custom-scrollbar p-1">
      {/* Header */}
      <div className="glass glass-cyan cyber-corners rounded-lg overflow-hidden">
        <div className="panel-header flex items-center justify-between px-4 py-2.5">
          <div className="flex items-center gap-2">
            <Activity size={13} style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 5px rgba(6,182,212,0.9))' }} />
            <span className="text-[10px] font-bold tracking-[0.25em] uppercase neon-cyan">Agent Swarm</span>
            {status && (
              <span className="text-[8px] font-mono px-1.5 py-0.5 rounded"
                style={status.swarm_active
                  ? { background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.35)', color: '#22c55e' }
                  : { background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.25)', color: 'rgba(6,182,212,0.6)' }}>
                {status.swarm_active ? '⬤ ACTIVE' : '◯ IDLE'}
              </span>
            )}
            {status && (
              <span className="text-[8px] font-mono px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(244,63,94,0.10)', border: '1px solid rgba(244,63,94,0.28)', color: '#f43f5e' }}>
                {status.flags_count} FLAG{status.flags_count !== 1 ? 'S' : ''}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={dispatchAll} disabled={dispatching}
              className="cyber-btn rounded px-2 py-1 text-[9px] flex items-center gap-1"
              style={{ borderColor: 'rgba(34,197,94,0.4)', color: '#22c55e' }}>
              <Zap size={9} />{dispatching ? 'Launching…' : 'Launch All Security'}
            </button>
            <button onClick={refresh} disabled={loading} className="p-1 rounded transition-colors"
              style={{ color: loading ? 'rgba(255,255,255,0.2)' : 'var(--cyan)' }}>
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Agent Cards */}
        <div className="p-3 space-y-4">
          {Object.entries(grouped).map(([type, agents]) => (
            <div key={type}>
              <div className="flex items-center gap-1.5 mb-2 text-[9px] font-mono uppercase tracking-widest"
                style={{ color: `${TYPE_COLOR[type]}0.55)` }}>
                {TYPE_ICON[type]}
                <span>{type}</span>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {agents.map(ag => (
                  <div key={ag.id} className="rounded-lg p-3 transition-all"
                    style={{
                      background: ag.running
                        ? `${TYPE_COLOR[ag.type]}0.10)`
                        : 'rgba(0,0,0,0.25)',
                      border: `1px solid ${TYPE_COLOR[ag.type]}${ag.running ? '0.40' : '0.15'})`,
                      boxShadow: ag.running ? `0 0 14px ${TYPE_COLOR[ag.type]}0.12)` : 'none',
                    }}>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span style={{ color: `${TYPE_COLOR[ag.type]}${ag.running ? '0.9' : '0.5'})` }}>
                          {TYPE_ICON[ag.type]}
                        </span>
                        <div className="min-w-0">
                          <div className="text-[10px] font-semibold truncate" style={{ color: ag.running ? '#fff' : 'rgba(255,255,255,0.65)' }}>
                            {ag.name}
                          </div>
                          <div className="text-[8px] font-mono opacity-40 flex items-center gap-2">
                            <span>{ag.schedule}</span>
                            <span>·</span>
                            <span>last: {ag.last_run}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {ag.running && (
                          <span className="text-[8px] font-mono animate-pulse" style={{ color: '#22c55e' }}>RUNNING</span>
                        )}
                        <button
                          onClick={() => dispatch(ag.id)}
                          disabled={ag.running || launching === ag.id}
                          className="rounded px-2 py-1 text-[9px] flex items-center gap-1 transition-all"
                          style={{
                            background:  ag.running ? 'rgba(255,255,255,0.04)' : `${TYPE_COLOR[ag.type]}0.08)`,
                            border:      `1px solid ${TYPE_COLOR[ag.type]}${ag.running ? '0.10' : '0.30'})`,
                            color:       ag.running ? 'rgba(255,255,255,0.2)' : `${TYPE_COLOR[ag.type]}0.85)`,
                            cursor:      ag.running ? 'not-allowed' : 'pointer',
                          }}>
                          {launching === ag.id ? <RefreshCw size={9} className="animate-spin" /> : <Play size={9} />}
                          {launching === ag.id ? 'Starting…' : 'Run'}
                        </button>
                      </div>
                    </div>
                    {/* Optional task input for dev agents */}
                    {(ag.id === 'coding' || ag.id === 'research' || ag.id === 'utility') && (
                      <div className="mt-2 flex gap-1">
                        <input
                          value={taskInput[ag.id] || ''}
                          onChange={e => setTaskInput(p => ({ ...p, [ag.id]: e.target.value }))}
                          onKeyDown={e => e.key === 'Enter' && !ag.running && dispatch(ag.id)}
                          placeholder={`Dispatch task to ${ag.name.split(' ')[0]}…`}
                          className="flex-1 rounded px-2 py-1 text-[10px] outline-none font-mono"
                          style={{ background: 'rgba(0,0,0,0.4)', border: `1px solid ${TYPE_COLOR[ag.type]}0.18)`, color: '#fff' }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Flags */}
      <div className="glass rounded-lg overflow-hidden" style={{ border: '1px solid rgba(244,63,94,0.18)' }}>
        <button onClick={() => setShowFlags(v => !v)}
          className="w-full panel-header flex items-center justify-between px-4 py-2.5"
          style={{ borderBottom: showFlags ? '1px solid rgba(244,63,94,0.12)' : 'none' }}>
          <div className="flex items-center gap-2">
            <ShieldAlert size={12} style={{ color: '#f43f5e' }} />
            <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: '#f43f5e' }}>
              Security Flags
            </span>
            <span className="text-[8px] font-mono px-1 rounded" style={{ background: 'rgba(244,63,94,0.12)', color: '#f43f5e' }}>
              {flags.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {flags.length > 0 && (
              <button onClick={e => { e.stopPropagation(); clearFlags(); }}
                className="p-1 rounded transition-colors" title="Clear flags"
                style={{ color: 'rgba(244,63,94,0.5)' }}
                onMouseEnter={e => (e.currentTarget.style.color = '#f43f5e')}
                onMouseLeave={e => (e.currentTarget.style.color = 'rgba(244,63,94,0.5)')}>
                <Trash2 size={11} />
              </button>
            )}
            {showFlags ? <ChevronDown size={11} style={{ color: 'rgba(255,255,255,0.3)' }} /> : <ChevronRight size={11} style={{ color: 'rgba(255,255,255,0.3)' }} />}
          </div>
        </button>
        {showFlags && (
          <div className="p-3 space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar">
            {flags.length === 0 ? (
              <div className="text-[10px] font-mono text-center py-4 opacity-25">No flags — system clean</div>
            ) : flags.map((f, i) => (
              <div key={i} className="rounded p-2 text-[10px] font-mono flex gap-2"
                style={{ background: 'rgba(0,0,0,0.3)', border: `1px solid ${LEVEL_COLOR[f.level]}22` }}>
                <TriangleAlert size={10} style={{ color: LEVEL_COLOR[f.level], flexShrink: 0, marginTop: 1 }} />
                <div>
                  <span style={{ color: LEVEL_COLOR[f.level] }}>[{f.level.toUpperCase()}]</span>
                  <span className="opacity-50 ml-1">{f.agent}</span>
                  <div className="opacity-70 mt-0.5 leading-relaxed">{f.details}</div>
                  <div className="opacity-30 text-[8px] mt-0.5">{f.timestamp?.slice(0, 19)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Activity Log */}
      <div className="glass rounded-lg overflow-hidden" style={{ border: '1px solid rgba(6,182,212,0.12)' }}>
        <button onClick={() => setShowLog(v => !v)}
          className="w-full panel-header flex items-center justify-between px-4 py-2.5"
          style={{ borderBottom: showLog ? '1px solid rgba(6,182,212,0.10)' : 'none' }}>
          <div className="flex items-center gap-2">
            <Bot size={12} style={{ color: 'var(--cyan)' }} />
            <span className="text-[10px] font-bold tracking-widest uppercase neon-cyan">Activity Log</span>
          </div>
          {showLog
            ? <ChevronDown size={11} style={{ color: 'rgba(255,255,255,0.3)' }} />
            : <ChevronRight size={11} style={{ color: 'rgba(255,255,255,0.3)' }} />}
        </button>
        {showLog && (
          <div className="p-3">
            <pre className="text-[9px] font-mono leading-relaxed opacity-60 max-h-64 overflow-y-auto custom-scrollbar whitespace-pre-wrap"
              style={{ color: '#a5f3fc' }}>
              {log || 'No log entries yet.'}
            </pre>
          </div>
        )}
      </div>

      {/* Latest Report */}
      {status?.latest_report && (
        <div className="glass rounded-lg overflow-hidden" style={{ border: '1px solid rgba(168,85,247,0.18)' }}>
          <div className="panel-header flex items-center gap-2 px-4 py-2.5" style={{ borderBottom: '1px solid rgba(168,85,247,0.10)' }}>
            <MessageSquareCode size={12} style={{ color: 'var(--purple)' }} />
            <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: 'var(--purple)' }}>Latest Report</span>
          </div>
          <div className="p-3">
            <pre className="text-[9px] font-mono leading-relaxed opacity-70 whitespace-pre-wrap max-h-48 overflow-y-auto custom-scrollbar"
              style={{ color: '#e9d5ff' }}>
              {JSON.stringify(status.latest_report, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default SwarmPanel;
