import { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, RefreshCw, ChevronDown, ChevronRight, Terminal } from 'lucide-react';

const API = 'http://100.89.122.112:8000';

interface FeedItem {
  source: string;
  content: string;
  job_id?: string;
}

export default function AgentFeed() {
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const fetchFeed = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/agent/feed`, { params: { lines: 40 } });
      setFeed(res.data.feed || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchFeed(); }, []);

  const toggle = (key: string) => setExpanded(prev => ({ ...prev, [key]: !prev[key] }));

  const sourceStyle = (src: string) => {
    if (src.startsWith('cron:')) return { icon: '⚙', color: 'text-cyan-400', border: 'border-cyan-400/20' };
    if (src === 'Dreams') return { icon: '✦', color: 'text-purple-400', border: 'border-purple-400/20' };
    if (src === 'Stream') return { icon: '〜', color: 'text-blue-400', border: 'border-blue-400/20' };
    if (src === 'Upgrade Radar') return { icon: '↑', color: 'text-green-400', border: 'border-green-400/20' };
    if (src === 'Last Error') return { icon: '⚠', color: 'text-red-400', border: 'border-red-400/20' };
    return { icon: '·', color: 'text-gray-400', border: 'border-gray-700' };
  };

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <Activity size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Agent Feed</span>
          <span className="text-xs text-gray-600">({feed.length} sources)</span>
        </div>
        <button onClick={fetchFeed} className={`p-1 text-gray-500 hover:text-white ${loading ? 'animate-spin' : ''}`}>
          <RefreshCw size={13} />
        </button>
      </div>

      {loading && <div className="text-center text-gray-600 text-xs py-6 animate-pulse">scanning agent logs…</div>}

      <div className="flex flex-col gap-2 max-h-[520px] overflow-y-auto pr-1">
        {feed.length === 0 && !loading && (
          <div className="text-center text-gray-600 text-xs py-8">No agent activity found.</div>
        )}
        {feed.map((item, i) => {
          const key = `${item.source}-${i}`;
          const style = sourceStyle(item.source);
          const isOpen = expanded[key] !== false; // default open
          const label = item.source.replace('cron:', '');
          const lines = item.content.trim().split('\n');
          const preview = lines.slice(-3).join('\n');

          return (
            <div key={key} className={`bg-gray-900/70 border ${style.border} rounded overflow-hidden`}>
              <button
                onClick={() => toggle(key)}
                className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-800/50 text-left"
              >
                {item.source.startsWith('cron:') ? <Terminal size={11} className={style.color} /> : <span className={`text-xs ${style.color}`}>{style.icon}</span>}
                <span className={`text-xs font-bold tracking-wider uppercase ${style.color}`}>{label}</span>
                <span className="ml-auto text-[9px] text-gray-600">{lines.length} lines</span>
                {isOpen ? <ChevronDown size={11} className="text-gray-600" /> : <ChevronRight size={11} className="text-gray-600" />}
              </button>
              {isOpen && (
                <div className="border-t border-gray-800 bg-black/40 px-3 py-2">
                  <pre className="text-[10px] text-gray-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                    {preview}
                  </pre>
                  {lines.length > 3 && (
                    <p className="text-[9px] text-gray-600 mt-1">showing last 3 of {lines.length} lines</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
