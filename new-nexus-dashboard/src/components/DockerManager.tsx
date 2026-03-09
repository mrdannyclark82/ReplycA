import { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Play, Square, RotateCcw, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react';

const API = '';

interface Container {
  id: string;
  name: string;
  image: string;
  status: string;
  state: string;
  ports: string;
}

export default function DockerManager() {
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<Record<string, string>>({});
  const [logOpen, setLogOpen] = useState<Record<string, boolean>>({});
  const [acting, setActing] = useState<Record<string, boolean>>({});

  const fetchContainers = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/docker/list`);
      setContainers(res.data.containers || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchContainers(); }, []);

  const act = async (action: 'start' | 'stop' | 'restart', name: string) => {
    setActing(prev => ({ ...prev, [name]: true }));
    try {
      await axios.post(`${API}/api/docker/${action}`, { container: name });
      await fetchContainers();
    } catch { /* ignore */ }
    setActing(prev => ({ ...prev, [name]: false }));
  };

  const fetchLogs = async (name: string) => {
    const isOpen = logOpen[name];
    setLogOpen(prev => ({ ...prev, [name]: !isOpen }));
    if (!isOpen) {
      try {
        const res = await axios.get(`${API}/api/docker/${name}/logs`, { params: { tail: 30 } });
        setLogs(prev => ({ ...prev, [name]: res.data.logs || '[no logs]' }));
      } catch { /* ignore */ }
    }
  };

  const stateStyle = (state: string) => {
    if (state === 'running') return 'text-green-400 bg-green-400/10 border-green-400/20';
    if (state === 'exited') return 'text-gray-500 bg-gray-800 border-gray-700';
    if (state === 'paused') return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    return 'text-gray-400 bg-gray-800 border-gray-700';
  };

  const running = containers.filter(c => c.state === 'running').length;

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <Box size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Docker</span>
          <span className="text-[10px] text-gray-500">{running}/{containers.length} running</span>
        </div>
        <button onClick={fetchContainers} className={`p-1 text-gray-500 hover:text-white ${loading ? 'animate-spin' : ''}`}>
          <RefreshCw size={13} />
        </button>
      </div>

      {loading && containers.length === 0 && (
        <div className="text-center text-gray-600 text-xs py-8 animate-pulse">scanning containers…</div>
      )}

      {!loading && containers.length === 0 && (
        <div className="text-center text-gray-600 text-xs py-8">No containers found.</div>
      )}

      <div className="flex flex-col gap-2 max-h-[520px] overflow-y-auto pr-1">
        {containers.map(c => (
          <div key={c.id} className="bg-gray-900/60 border border-gray-800 rounded overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2.5">
              {/* State badge */}
              <span className={`text-[9px] px-1.5 py-0.5 rounded border font-bold uppercase shrink-0 ${stateStyle(c.state)}`}>
                {c.state}
              </span>

              {/* Name + image */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-white truncate">{c.name}</p>
                <p className="text-[10px] text-gray-500 truncate">{c.image}</p>
              </div>

              {/* Actions */}
              <div className="flex gap-1 shrink-0">
                {c.state !== 'running' && (
                  <button onClick={() => act('start', c.name)} disabled={acting[c.name]}
                    className="p-1.5 text-green-400 hover:bg-green-400/10 rounded disabled:opacity-40" title="Start">
                    <Play size={12} />
                  </button>
                )}
                {c.state === 'running' && (
                  <button onClick={() => act('stop', c.name)} disabled={acting[c.name]}
                    className="p-1.5 text-red-400 hover:bg-red-400/10 rounded disabled:opacity-40" title="Stop">
                    <Square size={12} />
                  </button>
                )}
                <button onClick={() => act('restart', c.name)} disabled={acting[c.name]}
                  className="p-1.5 text-amber-400 hover:bg-amber-400/10 rounded disabled:opacity-40" title="Restart">
                  <RotateCcw size={12} />
                </button>
                <button onClick={() => fetchLogs(c.name)}
                  className="p-1.5 text-gray-400 hover:text-white rounded" title="Logs">
                  {logOpen[c.name] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                </button>
              </div>
            </div>

            {/* Ports row */}
            {c.ports && (
              <div className="px-3 pb-1.5 text-[10px] text-gray-600">{c.ports}</div>
            )}

            {/* Log view */}
            {logOpen[c.name] && (
              <div className="border-t border-gray-800 bg-black/60 px-3 py-2">
                <pre className="text-[10px] text-gray-400 whitespace-pre-wrap max-h-40 overflow-y-auto leading-relaxed">
                  {logs[c.name] || 'Loading…'}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
