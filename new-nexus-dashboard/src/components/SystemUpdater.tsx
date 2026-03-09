import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ArrowUpCircle, RefreshCw, Play, CheckCircle, AlertCircle } from 'lucide-react';

const API = '';

interface Update { pkg: string; from: string; to: string; raw: string; }

function parseUpdate(line: string): Update {
  // format: "pkgname current -> new"
  const parts = line.trim().split(/\s+/);
  return { pkg: parts[0] || line, from: parts[1] || '', to: parts[3] || '', raw: line };
}

export default function SystemUpdater() {
  const [updates, setUpdates] = useState<Update[]>([]);
  const [count, setCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const checkUpdates = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/system/updates`);
      setCount(res.data.count);
      setUpdates((res.data.updates || []).map(parseUpdate));
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { checkUpdates(); }, []);
  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' }); }, [log]);

  const startUpgrade = () => {
    setLog([]); setDone(false); setExitCode(null); setUpgrading(true);
    const es = new EventSource(`${API}/api/system/upgrade`);
    es.onmessage = e => {
      const line = e.data;
      if (line.startsWith('[EXIT:')) {
        const code = parseInt(line.match(/\[EXIT:(\d+)\]/)?.[1] || '0');
        setExitCode(code); setDone(true); setUpgrading(false);
        es.close();
        if (code === 0) checkUpdates();
      } else {
        setLog(prev => [...prev, line]);
      }
    };
    es.onerror = () => { setUpgrading(false); setDone(true); es.close(); };
  };

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <ArrowUpCircle size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">System Updater</span>
          {count !== null && (
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${count > 0 ? 'text-amber-400 border-amber-400/30 bg-amber-400/10' : 'text-green-400 border-green-400/30 bg-green-400/10'}`}>
              {count > 0 ? `${count} updates` : '✓ up to date'}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={checkUpdates} className={`p-1 text-gray-500 hover:text-white ${loading ? 'animate-spin' : ''}`}><RefreshCw size={13} /></button>
          {count !== null && count > 0 && !upgrading && (
            <button onClick={startUpgrade}
              className="px-3 py-1 text-xs bg-amber-500 text-black font-bold rounded hover:bg-amber-400 flex items-center gap-1">
              <Play size={11} /> Run Upgrade
            </button>
          )}
        </div>
      </div>

      {/* Upgrade log */}
      {(log.length > 0 || upgrading) && (
        <div className="bg-black border border-gray-800 rounded">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-800">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">Upgrade Output</span>
            {done && (
              <div className={`flex items-center gap-1 text-[10px] ${exitCode === 0 ? 'text-green-400' : 'text-red-400'}`}>
                {exitCode === 0 ? <CheckCircle size={11} /> : <AlertCircle size={11} />}
                {exitCode === 0 ? 'Complete' : `Failed (exit ${exitCode})`}
              </div>
            )}
            {upgrading && <span className="text-[10px] text-amber-400 animate-pulse">upgrading…</span>}
          </div>
          <div ref={logRef} className="p-2 max-h-48 overflow-y-auto">
            {log.map((l, i) => (
              <div key={i} className={`text-[10px] leading-relaxed ${
                l.includes('error') || l.includes('Error') ? 'text-red-400' :
                l.includes('warning') ? 'text-yellow-400' :
                l.startsWith('::') || l.startsWith('==>') ? 'text-cyan-400' :
                'text-gray-400'
              }`}>{l}</div>
            ))}
          </div>
        </div>
      )}

      {/* Update list */}
      {!upgrading && updates.length > 0 && (
        <div className="flex flex-col gap-1 max-h-80 overflow-y-auto pr-1">
          <div className="text-[10px] text-gray-600 px-1 pb-1 uppercase tracking-wider">Pending Updates</div>
          {updates.map((u, i) => (
            <div key={i} className="flex items-center gap-2 px-2 py-1.5 bg-gray-900/60 border border-gray-800 rounded text-xs">
              <span className="font-bold text-white flex-1 truncate">{u.pkg}</span>
              {u.from && <span className="text-gray-600 text-[10px] shrink-0">{u.from} → <span className="text-green-400">{u.to}</span></span>}
            </div>
          ))}
        </div>
      )}

      {!loading && count === 0 && !upgrading && (
        <div className="text-center py-8 text-green-400 text-xs">
          <CheckCircle size={24} className="mx-auto mb-2 opacity-50" />
          System is fully up to date.
        </div>
      )}
    </div>
  );
}
