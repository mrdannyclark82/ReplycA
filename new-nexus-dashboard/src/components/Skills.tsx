import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Package, Download, Play, Trash2, ToggleLeft, ToggleRight, RefreshCw, Github, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, Wand2 } from 'lucide-react';

interface SkillMeta {
  name: string;
  description: string;
  version: string;
  author: string;
  commands: string[];
  requires: string[];
  origin: string;
  enabled: boolean;
  loaded: boolean;
}

interface RunResult {
  ok: boolean;
  result?: unknown;
  error?: string;
}

export default function Skills() {
  const [skills, setSkills]         = useState<SkillMeta[]>([]);
  const [installUrl, setInstallUrl] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [expanded, setExpanded]     = useState<string | null>(null);
  const [payloads, setPayloads]     = useState<Record<string, string>>({});
  const [runResults, setRunResults] = useState<Record<string, RunResult>>({});
  const [running, setRunning]       = useState<string | null>(null);
  const [loading, setLoading]       = useState(false);

  // Forge state
  const [forgeDesc, setForgeDesc]   = useState('');
  const [forging, setForging]       = useState(false);
  const [forgeMsg, setForgeMsg]     = useState<{ ok: boolean; text: string } | null>(null);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get('/api/skills');
      setSkills(data.skills || []);
    } catch { /* server offline */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchSkills(); }, [fetchSkills]);

  const handleForge = async () => {
    if (!forgeDesc.trim()) return;
    setForging(true);
    setForgeMsg(null);
    try {
      const { data } = await axios.post('/api/skills/forge', { description: forgeDesc.trim() });
      const ok = !data.output?.startsWith('[Forge Error]');
      setForgeMsg({ ok, text: data.output || 'Done' });
      if (ok) { setForgeDesc(''); fetchSkills(); }
    } catch (e: unknown) {
      setForgeMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    }
    setForging(false);
  };

  const handleInstall = async () => {
    if (!installUrl.trim()) return;
    setInstalling(true);
    setInstallMsg(null);
    try {
      const { data } = await axios.post('/api/skills/install', { url: installUrl.trim() });
      setInstallMsg({ ok: data.ok, text: data.message || data.error || 'Done' });
      if (data.ok) { setInstallUrl(''); fetchSkills(); }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setInstallMsg({ ok: false, text: msg });
    }
    setInstalling(false);
  };

  const handleToggle = async (skill: SkillMeta) => {
    try {
      await axios.put(`/api/skills/${skill.name}/toggle`, { enabled: !skill.enabled });
      fetchSkills();
    } catch { /* ignore */ }
  };

  const handleUninstall = async (name: string) => {
    if (!confirm(`Uninstall skill "${name}"?`)) return;
    try {
      await axios.delete(`/api/skills/${name}`);
      fetchSkills();
    } catch { /* ignore */ }
  };

  const handleRun = async (name: string) => {
    setRunning(name);
    let payload: Record<string, unknown> = {};
    try { payload = JSON.parse(payloads[name] || '{}'); } catch { /* use empty */ }
    try {
      const { data } = await axios.post(`/api/skills/${name}/run`, { payload });
      setRunResults(r => ({ ...r, [name]: data }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setRunResults(r => ({ ...r, [name]: { ok: false, error: msg } }));
    }
    setRunning(null);
  };

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto p-1">

      {/* Skill Forge — AI generates skills */}
      <div className="glass rounded-lg p-4" style={{ border: '1px solid rgba(6,182,212,0.18)', background: 'rgba(6,182,212,0.03)' }}>
        <div className="flex items-center gap-2 mb-3">
          <Wand2 size={13} style={{ color: 'var(--cyan)' }} />
          <span className="text-[9px] uppercase tracking-[0.3em] font-bold" style={{ color: 'var(--cyan)' }}>Skill Forge</span>
          <span className="text-[8px] px-2 py-0.5 rounded ml-1" style={{ background: 'rgba(6,182,212,0.12)', color: 'rgba(6,182,212,0.6)', border: '1px solid rgba(6,182,212,0.2)' }}>
            AI-GENERATED
          </span>
        </div>
        <div className="flex gap-2">
          <input
            value={forgeDesc}
            onChange={e => setForgeDesc(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleForge()}
            placeholder="Describe a skill in plain English… e.g. fetch weather for a city"
            className="flex-1 px-3 py-2 rounded text-xs font-mono outline-none transition-all"
            style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(6,182,212,0.22)', color: '#a5f3fc' }}
          />
          <button
            onClick={handleForge}
            disabled={forging || !forgeDesc.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded text-xs font-bold uppercase tracking-widest transition-all disabled:opacity-40"
            style={{ background: forging ? 'rgba(6,182,212,0.08)' : 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.35)', color: 'var(--cyan)' }}
          >
            {forging ? <RefreshCw size={12} className="animate-spin" /> : <Wand2 size={12} />}
            {forging ? 'Forging…' : 'Forge'}
          </button>
        </div>
        {forgeMsg && (
          <div className={`mt-3 flex items-start gap-2 text-xs px-3 py-2 rounded ${
            forgeMsg.ok ? 'bg-green-950/40 border border-green-500/30' : 'bg-red-950/40 border border-red-500/30'
          }`}>
            {forgeMsg.ok
              ? <CheckCircle size={12} className="mt-0.5 shrink-0" style={{ color: 'var(--green)' }} />
              : <AlertTriangle size={12} className="mt-0.5 shrink-0" style={{ color: 'var(--red)' }} />}
            <span className="font-mono text-[10px] whitespace-pre-wrap" style={{ color: forgeMsg.ok ? 'var(--green)' : 'var(--red)' }}>
              {forgeMsg.text}
            </span>
          </div>
        )}
      </div>

      {/* Header — GitHub install */}
      <div className="glass glass-purple cyber-corners rounded-lg p-4">
        <div className="panel-header -mx-4 -mt-4 px-4 py-2.5 rounded-t-lg mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package size={13} style={{ color: 'var(--purple)' }} />
            <span className="text-[9px] uppercase tracking-[0.3em]" style={{ color: 'var(--purple)' }}>
              Skill Registry
            </span>
          </div>
          <button onClick={fetchSkills} disabled={loading}
            className="p-1 rounded opacity-60 hover:opacity-100 transition-opacity"
            style={{ color: 'var(--cyan)' }}>
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Install row */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Github size={12} className="absolute left-3 top-1/2 -translate-y-1/2 opacity-40" style={{ color: 'var(--cyan)' }} />
            <input
              value={installUrl}
              onChange={e => setInstallUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleInstall()}
              placeholder="user/repo/skill.py  or  github.com/user/repo/blob/main/skill.py"
              className="w-full pl-8 pr-3 py-2 rounded text-xs font-mono bg-black/40 border outline-none transition-all"
              style={{
                borderColor: 'rgba(168,85,247,0.3)',
                color: 'var(--purple)',
              }}
            />
          </div>
          <button
            onClick={handleInstall}
            disabled={installing || !installUrl.trim()}
            className="cyber-btn flex items-center gap-2 px-4 py-2 rounded text-xs font-bold uppercase tracking-widest disabled:opacity-40"
            style={{ borderColor: 'var(--purple)', color: 'var(--purple)' }}
          >
            {installing
              ? <RefreshCw size={12} className="animate-spin" />
              : <Download size={12} />}
            {installing ? 'Installing…' : 'Install'}
          </button>
        </div>

        {/* Install status */}
        {installMsg && (
          <div className={`mt-3 flex items-center gap-2 text-xs px-3 py-2 rounded ${
            installMsg.ok ? 'bg-green-950/40 border border-green-500/30' : 'bg-red-950/40 border border-red-500/30'
          }`}>
            {installMsg.ok
              ? <CheckCircle size={12} style={{ color: 'var(--green)' }} />
              : <AlertTriangle size={12} style={{ color: 'var(--red)' }} />}
            <span style={{ color: installMsg.ok ? 'var(--green)' : 'var(--red)' }}>
              {installMsg.text}
            </span>
          </div>
        )}

        {/* Help text */}
        <p className="mt-3 text-[10px] opacity-30 leading-relaxed" style={{ color: 'var(--cyan)' }}>
          Skill files must export <code>register()</code> → metadata dict and <code>execute(payload)</code> → result dict.
        </p>
      </div>

      {/* Skill cards */}
      {skills.length === 0 ? (
        <div className="glass rounded-lg p-8 text-center">
          <Package size={32} className="mx-auto mb-3 opacity-20" style={{ color: 'var(--purple)' }} />
          <p className="text-xs opacity-40 uppercase tracking-widest" style={{ color: 'var(--purple)' }}>
            No skills installed
          </p>
          <p className="text-[10px] opacity-20 mt-1" style={{ color: 'var(--cyan)' }}>
            Paste a GitHub URL above to install one
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {skills.map(skill => {
            const isExpanded = expanded === skill.name;
            const runResult  = runResults[skill.name];
            return (
              <div key={skill.name}
                className={`glass cyber-corners rounded-lg overflow-hidden transition-all ${
                  skill.enabled ? 'glass-purple' : 'opacity-50'
                }`}>

                {/* Skill header row */}
                <div className="px-4 py-3 flex items-center gap-3">
                  {/* Status dot */}
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    skill.loaded ? 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.8)]'
                                 : skill.enabled ? 'bg-yellow-400' : 'bg-gray-600'
                  }`} />

                  {/* Name + meta */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold font-mono uppercase tracking-wider"
                        style={{ color: 'var(--purple)' }}>
                        {skill.name}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded border"
                        style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.3)', background: 'rgba(6,182,212,0.05)' }}>
                        v{skill.version}
                      </span>
                      {skill.commands.length > 0 && skill.commands.map(cmd => (
                        <span key={cmd} className="text-[9px] px-1.5 py-0.5 rounded border"
                          style={{ color: 'var(--amber)', borderColor: 'rgba(245,158,11,0.3)', background: 'rgba(245,158,11,0.05)' }}>
                          {cmd}
                        </span>
                      ))}
                    </div>
                    <p className="text-[10px] mt-0.5 opacity-60 truncate" style={{ color: 'var(--cyan)' }}>
                      {skill.description}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {/* Toggle */}
                    <button onClick={() => handleToggle(skill)}
                      className="p-1.5 rounded hover:bg-white/5 transition-colors"
                      title={skill.enabled ? 'Disable' : 'Enable'}>
                      {skill.enabled
                        ? <ToggleRight size={16} style={{ color: 'var(--green)' }} />
                        : <ToggleLeft size={16} className="opacity-40" style={{ color: 'var(--cyan)' }} />}
                    </button>
                    {/* Run */}
                    <button onClick={() => handleRun(skill.name)}
                      disabled={!skill.enabled || running === skill.name}
                      className="p-1.5 rounded hover:bg-white/5 transition-colors disabled:opacity-30"
                      title="Run skill">
                      <Play size={13} className={running === skill.name ? 'animate-pulse' : ''}
                        style={{ color: 'var(--amber)' }} />
                    </button>
                    {/* Expand */}
                    <button onClick={() => setExpanded(isExpanded ? null : skill.name)}
                      className="p-1.5 rounded hover:bg-white/5 transition-colors"
                      style={{ color: 'var(--cyan)' }}>
                      {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </button>
                    {/* Delete */}
                    <button onClick={() => handleUninstall(skill.name)}
                      className="p-1.5 rounded hover:bg-red-950/30 transition-colors"
                      style={{ color: 'var(--red)' }} title="Uninstall">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Expanded panel */}
                {isExpanded && (
                  <div className="border-t px-4 py-3 space-y-3"
                    style={{ borderColor: 'rgba(168,85,247,0.15)' }}>

                    {/* Info row */}
                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                      <div><span className="opacity-40 uppercase tracking-widest" style={{ color: 'var(--cyan)' }}>Author </span>
                        <span style={{ color: 'var(--cyan)' }}>{skill.author}</span></div>
                      {skill.requires.length > 0 && (
                        <div><span className="opacity-40 uppercase tracking-widest" style={{ color: 'var(--cyan)' }}>Deps </span>
                          <span style={{ color: 'var(--cyan)' }}>{skill.requires.join(', ')}</span></div>
                      )}
                      <div className="col-span-2 truncate">
                        <span className="opacity-40 uppercase tracking-widest" style={{ color: 'var(--cyan)' }}>Source </span>
                        <a href={skill.origin} target="_blank" rel="noreferrer"
                          className="hover:underline opacity-60" style={{ color: 'var(--purple)' }}>
                          {skill.origin}
                        </a>
                      </div>
                    </div>

                    {/* Payload input */}
                    <div>
                      <label className="text-[9px] uppercase tracking-widest opacity-40 mb-1 block"
                        style={{ color: 'var(--amber)' }}>Payload JSON</label>
                      <textarea
                        rows={3}
                        value={payloads[skill.name] || '{}'}
                        onChange={e => setPayloads(p => ({ ...p, [skill.name]: e.target.value }))}
                        className="w-full px-3 py-2 rounded text-xs font-mono bg-black/40 border outline-none resize-none"
                        style={{ borderColor: 'rgba(245,158,11,0.2)', color: 'var(--amber)' }}
                      />
                    </div>

                    {/* Run result */}
                    {runResult && (
                      <div className={`rounded px-3 py-2 text-[10px] font-mono whitespace-pre-wrap break-all ${
                        runResult.ok ? 'bg-green-950/30 border border-green-500/20' : 'bg-red-950/30 border border-red-500/20'
                      }`} style={{ color: runResult.ok ? 'var(--green)' : 'var(--red)' }}>
                        {runResult.ok
                          ? JSON.stringify(runResult.result, null, 2)
                          : `Error: ${runResult.error}`}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
