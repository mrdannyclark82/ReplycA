import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import Chat from './components/Chat';
import Terminal from './components/Terminal';
import HUD from './components/HUD';
import Skills from './components/Skills';
import CronManager from './components/CronManager';
import CastControl from './components/CastControl';
import CalendarPanel from './components/CalendarPanel';
import ModelSwitcher from './components/ModelSwitcher';
import MemoryBrowser from './components/MemoryBrowser';
import VoiceChat from './components/VoiceChat';
import AgentFeed from './components/AgentFeed';
import PersonaEditor from './components/PersonaEditor';
import GmailPanel from './components/GmailPanel';
import NeuroEditor from './components/NeuroEditor';
import VisionPanel from './components/VisionPanel';
import SystemUpdater from './components/SystemUpdater';
import DailyBrief from './components/DailyBrief';
import DockerManager from './components/DockerManager';
import SystemStats from './components/SystemStats';
import LogViewer from './components/LogViewer';
import FileBrowser from './components/FileBrowser';
import GitPanel from './components/GitPanel';
import BackupPanel from './components/BackupPanel';
import SwarmPanel from './components/SwarmPanel';
import UpgradeRadar from './components/UpgradeRadar';
import { Shield, Terminal as TerminalIcon, Package, Clock, Tv, Calendar, Cpu, Database, Mic, Activity, User, LayoutGrid, Mail, Zap, Eye, ArrowUpCircle, BookOpen, Box, BarChart2, FileText, FolderOpen, GitBranch, Archive, Bell, Search as SearchIcon, X, Bot, Radar, ChevronLeft, ChevronRight } from 'lucide-react';
import InstallPWA from './components/InstallPWA';

type RightPanel = 'console' | 'skills' | 'cron' | 'cast' | 'calendar' | 'models' | 'memory' | 'voice' | 'feed' | 'persona' | 'gmail' | 'neuro' | 'vision' | 'updates' | 'brief' | 'docker' | 'stats' | 'logs' | 'files' | 'git' | 'backup' | 'swarm' | 'radar';

interface Alert { type: string; source: string; text: string; }
interface SearchResult { source: string; id: string | number; text: string; meta: string; }

const SERVER = '';
const WS_SERVER = SERVER.replace(/^http/, 'ws');

function App() {
  const [nodes, setNodes]           = useState({ termux: false, google: false, swarm: false });
  const [rightPanel, setRightPanel] = useState<RightPanel>('console');
  const tabScrollRef                = useRef<HTMLDivElement>(null);

  // Live neuro state via WebSocket for header bars
  const [neuro, setNeuro] = useState({ dopamine: 0.5, serotonin: 0.5, atp_energy: 100 });
  const neuroWs = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_SERVER}/ws/neuro`);
        neuroWs.current = ws;
        ws.onmessage = (e) => { try { setNeuro(JSON.parse(e.data)); } catch { /* ignore */ } };
        ws.onclose = () => setTimeout(connect, 5000);
        ws.onerror = () => ws.close();
      } catch { setTimeout(connect, 5000); }
    };
    connect();
    return () => neuroWs.current?.close();
  }, []);

  // Notifications bell
  const [alerts, setAlerts]         = useState<Alert[]>([]);
  const [bellOpen, setBellOpen]     = useState(false);
  const [alertCount, setAlertCount] = useState(0);
  useEffect(() => {
    const poll = () => {
      axios.get('/api/notifications').then(r => {
        if (r.data.ok) { setAlerts(r.data.alerts); setAlertCount(r.data.count); }
      }).catch(() => {});
    };
    poll();
    const iv = setInterval(poll, 30000);
    return () => clearInterval(iv);
  }, []);

  // Global search
  const [searchOpen, setSearchOpen]     = useState(false);
  const [searchQuery, setSearchQuery]   = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching]       = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const r = await axios.get(`/api/search?q=${encodeURIComponent(q)}`);
      if (r.data.ok) setSearchResults(r.data.results);
    } catch { /* ignore */ }
    setSearching(false);
  }, []);

  useEffect(() => {
    const t = setTimeout(() => doSearch(searchQuery), 300);
    return () => clearTimeout(t);
  }, [searchQuery, doSearch]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(s => !s);
        setSearchQuery('');
        setSearchResults([]);
      }
      if (e.key === 'Escape') { setSearchOpen(false); setBellOpen(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (searchOpen) setTimeout(() => searchRef.current?.focus(), 50);
  }, [searchOpen]);

  useEffect(() => {
    const fetchNodes = () => axios.get('/api/nodes').then(r => setNodes(r.data)).catch(() => {});
    fetchNodes();
    const interval = setInterval(fetchNodes, 10000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: RightPanel; label: string; icon: React.ReactNode; color: string }[] = [
    { id: 'console',  label: 'Console',  icon: <TerminalIcon size={11} />, color: 'var(--green)' },
    { id: 'skills',   label: 'Skills',   icon: <Package size={11} />,      color: 'var(--purple)' },
    { id: 'cron',     label: 'Cron',     icon: <Clock size={11} />,        color: 'var(--amber)' },
    { id: 'cast',     label: 'Cast',     icon: <Tv size={11} />,           color: 'var(--cyan)' },
    { id: 'calendar', label: 'Calendar', icon: <Calendar size={11} />,     color: '#a78bfa' },
    { id: 'models',   label: 'Models',   icon: <Cpu size={11} />,          color: '#f472b6' },
    { id: 'memory',   label: 'Memory',   icon: <Database size={11} />,     color: '#34d399' },
    { id: 'voice',    label: 'Voice',    icon: <Mic size={11} />,          color: '#f87171' },
    { id: 'feed',     label: 'Feed',     icon: <Activity size={11} />,     color: '#60a5fa' },
    { id: 'persona',  label: 'Persona',  icon: <User size={11} />,         color: '#e879f9' },
    { id: 'gmail',    label: 'Gmail',    icon: <Mail size={11} />,         color: '#f87171' },
    { id: 'neuro',    label: 'Neuro',    icon: <Zap size={11} />,          color: '#fbbf24' },
    { id: 'vision',   label: 'Vision',   icon: <Eye size={11} />,          color: '#a78bfa' },
    { id: 'updates',  label: 'Updates',  icon: <ArrowUpCircle size={11} />,color: '#34d399' },
    { id: 'brief',    label: 'Brief',    icon: <BookOpen size={11} />,     color: '#60a5fa' },
    { id: 'docker',   label: 'Docker',   icon: <Box size={11} />,          color: '#38bdf8' },
    { id: 'stats',    label: 'Stats',    icon: <BarChart2 size={11} />,    color: '#fb923c' },
    { id: 'logs',     label: 'Logs',     icon: <FileText size={11} />,     color: '#94a3b8' },
    { id: 'files',    label: 'Files',    icon: <FolderOpen size={11} />,   color: '#fde68a' },
    { id: 'git',      label: 'Git',      icon: <GitBranch size={11} />,    color: '#a78bfa' },
    { id: 'backup',   label: 'Backup',   icon: <Archive size={11} />,      color: '#34d399' },
    { id: 'swarm',    label: 'Swarm',    icon: <Bot size={11} />,           color: '#f43f5e' },
    { id: 'radar',    label: 'Radar',    icon: <Radar size={11} />,         color: 'var(--cyan)' },
  ];

  return (
    <div className="min-h-screen p-4 font-mono selection:bg-cyan-500 selection:text-black">

      {/* Top Header */}
      <header className="flex items-center justify-between mb-5 px-1">
        <div className="flex items-center gap-4">
          <div className="relative p-2.5 glass glass-cyan cyber-corners rounded-lg">
            <Shield className="w-5 h-5" style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 6px rgba(6,182,212,0.8))' }} />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-[0.15em] uppercase italic neon-cyan flicker">
              Nexus Kingdom
            </h1>
            <p className="text-[9px] opacity-40 uppercase tracking-[0.4em] mt-0.5" style={{ color: 'var(--cyan)' }}>
              Forever Morth Platform · v1.0
            </p>
          </div>
        </div>

        {/* Right: architect tag + install prompt */}
        <div className="flex items-center gap-3">
          {/* Live neuro bars */}
          <div className="hidden lg:flex items-center gap-2" title="Live neuro state">
            {[
              { key: 'dopamine', v: neuro.dopamine, color: '#fbbf24' },
              { key: 'serotonin', v: neuro.serotonin, color: '#06b6d4' },
              { key: 'atp', v: neuro.atp_energy / 100, color: '#34d399' },
            ].map(n => (
              <div key={n.key} style={{ width: 30, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                <div style={{ fontSize: '7px', color: 'rgba(255,255,255,0.3)', letterSpacing: '1px' }}>{n.key.slice(0,3).toUpperCase()}</div>
                <div style={{ width: '100%', height: 3, background: 'rgba(255,255,255,0.07)', borderRadius: 2 }}>
                  <div style={{ width: `${Math.min(100, n.v * 100)}%`, height: '100%', background: n.color, borderRadius: 2, transition: 'width 1s ease', boxShadow: `0 0 4px ${n.color}88` }} />
                </div>
              </div>
            ))}
          </div>

          {/* Search button */}
          <button
            onClick={() => { setSearchOpen(true); setSearchQuery(''); setSearchResults([]); }}
            className="flex items-center gap-1.5 px-2 py-1 rounded text-[9px] uppercase tracking-widest"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.4)', cursor: 'pointer' }}
            title="Search (Ctrl+K)"
          >
            <SearchIcon size={10} />
            <span className="hidden md:inline">Search</span>
            <kbd style={{ fontSize: '8px', opacity: 0.5, background: 'rgba(255,255,255,0.06)', padding: '1px 4px', borderRadius: 2 }}>⌘K</kbd>
          </button>

          {/* Notification bell */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setBellOpen(o => !o)}
              style={{ background: alertCount > 0 ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.04)', border: `1px solid ${alertCount > 0 ? 'rgba(251,191,36,0.3)' : 'rgba(255,255,255,0.08)'}`, borderRadius: 6, padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, position: 'relative' }}
            >
              <Bell size={12} style={{ color: alertCount > 0 ? '#fbbf24' : 'rgba(255,255,255,0.4)' }} />
              {alertCount > 0 && (
                <span style={{ position: 'absolute', top: -4, right: -4, background: '#f87171', color: '#000', fontSize: 8, fontWeight: 900, width: 14, height: 14, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{alertCount}</span>
              )}
            </button>
            {bellOpen && (
              <div style={{ position: 'absolute', right: 0, top: '110%', width: 280, background: '#0d1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, zIndex: 999, padding: '8px', boxShadow: '0 8px 32px rgba(0,0,0,0.8)' }}>
                <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: 6, padding: '0 4px' }}>Alerts</div>
                {alerts.length === 0
                  ? <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 10, padding: '8px 4px' }}>All clear ✓</div>
                  : alerts.map((a, i) => (
                    <div key={i} style={{ padding: '6px 8px', borderRadius: 4, marginBottom: 2, background: a.type === 'warn' ? 'rgba(248,113,113,0.06)' : 'rgba(52,211,153,0.06)', border: `1px solid ${a.type === 'warn' ? 'rgba(248,113,113,0.2)' : 'rgba(52,211,153,0.15)'}` }}>
                      <div style={{ fontSize: 9, color: a.type === 'warn' ? '#f87171' : '#34d399', letterSpacing: '1px' }}>{a.source.toUpperCase()}</div>
                      <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)', marginTop: 2 }}>{a.text}</div>
                    </div>
                  ))
                }
              </div>
            )}
          </div>

          <InstallPWA />
          <div className="scan-line w-24 hidden lg:block" />
          <div className="glass glass-cyan rounded px-3 py-1.5 text-right">
            <div className="text-[9px] uppercase tracking-[0.3em] opacity-40" style={{ color: 'var(--cyan)' }}>Architect</div>
            <div className="text-[11px] font-bold uppercase tracking-wider neon-cyan">Storm · D-Ray</div>
          </div>
        </div>
      </header>

      {/* Search Modal */}
      {searchOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 9999, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', paddingTop: '15vh' }}
          onClick={(e) => { if (e.target === e.currentTarget) setSearchOpen(false); }}
        >
          <div style={{ width: '100%', maxWidth: 600, background: '#0d1117', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 12, overflow: 'hidden', boxShadow: '0 24px 80px rgba(0,0,0,0.9)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <SearchIcon size={14} style={{ color: 'rgba(255,255,255,0.4)', flexShrink: 0 }} />
              <input
                ref={searchRef}
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search memory, skills, feed…"
                style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: 14, fontFamily: 'monospace' }}
              />
              {searching && <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>searching…</span>}
              <button onClick={() => setSearchOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.3)', padding: 2 }}><X size={14} /></button>
            </div>
            <div style={{ maxHeight: 400, overflowY: 'auto', padding: 8 }}>
              {searchResults.length === 0 && searchQuery.length >= 2 && !searching && (
                <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, padding: '12px 8px', textAlign: 'center' }}>No results for "{searchQuery}"</div>
              )}
              {searchQuery.length < 2 && (
                <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: 10, padding: '12px 8px', textAlign: 'center', fontFamily: 'monospace', letterSpacing: '2px' }}>TYPE TO SEARCH MEMORIES · SKILLS · FEED</div>
              )}
              {searchResults.map((r, i) => {
                const srcColor: Record<string, string> = { memory: '#34d399', skill: '#fbbf24', feed: '#a78bfa' };
                return (
                  <div key={i} style={{ padding: '8px 10px', borderRadius: 6, marginBottom: 2, cursor: 'pointer', background: 'rgba(255,255,255,0.02)' }}
                    onClick={() => {
                      if (r.source === 'memory') setRightPanel('memory');
                      else if (r.source === 'skill') setRightPanel('skills');
                      else setRightPanel('feed');
                      setSearchOpen(false);
                    }}>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 3 }}>
                      <span style={{ fontSize: 8, background: `${srcColor[r.source] || '#888'}22`, color: srcColor[r.source] || '#888', padding: '1px 5px', borderRadius: 3, letterSpacing: '1px', textTransform: 'uppercase' }}>{r.source}</span>
                      <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)' }}>{r.meta}</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', lineHeight: '1.4' }}>{r.text}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Divider */}
      <div className="scan-line mb-5" />

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-4 h-[calc(100vh-130px)]">

        {/* Left Column */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          <HUD />

          {/* System Nodes */}
          <div className="glass glass-cyan cyber-corners rounded-lg p-4">
            <div className="panel-header -mx-4 -mt-4 px-4 py-2.5 rounded-t-lg mb-4 flex items-center gap-2">
              <LayoutGrid size={13} style={{ color: 'var(--cyan)' }} />
              <span className="text-[10px] font-bold tracking-[0.25em] uppercase neon-cyan">System Nodes</span>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Termux Bridge', active: nodes.termux,  color: 'var(--green)' },
                { label: 'Google OAuth',  active: nodes.google,  color: nodes.google ? 'var(--green)' : 'var(--amber)' },
                { label: 'Swarm Sync',    active: nodes.swarm,   color: 'var(--cyan)' },
              ].map(({ label, active, color }) => (
                <div key={label} className="flex items-center justify-between px-3 py-2 rounded"
                  style={{ background: 'rgba(6,182,212,0.03)', border: '1px solid rgba(6,182,212,0.08)' }}>
                  <span className="text-[10px] font-mono uppercase tracking-wider opacity-60">{label}</span>
                  <div
                    className={active ? 'animate-pulse-dot' : ''}
                    style={{
                      width: 8, height: 8, borderRadius: '50%',
                      backgroundColor: active ? color : 'rgba(255,255,255,0.12)',
                      boxShadow: active ? `0 0 8px ${color}` : 'none',
                    }}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Quick nav */}
          <div className="glass rounded-lg p-3 space-y-1">
            <p className="text-[8px] uppercase tracking-[0.4em] opacity-30 px-2 mb-2" style={{ color: 'var(--cyan)' }}>Navigation</p>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setRightPanel(t.id)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded text-left transition-all"
                style={{
                  background: rightPanel === t.id ? `color-mix(in srgb, ${t.color} 10%, transparent)` : 'transparent',
                  border: `1px solid ${rightPanel === t.id ? t.color + '40' : 'transparent'}`,
                  color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.4)',
                }}>
                <span style={{ color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.3)' }}>{t.icon}</span>
                <span className="text-[10px] uppercase tracking-widest font-bold">{t.label}</span>
                {rightPanel === t.id && (
                  <div className="ml-auto w-1 h-3 rounded-full" style={{ background: t.color, boxShadow: `0 0 6px ${t.color}` }} />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Center/Right Panel */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-4 min-h-0">

          {/* Tab bar — horizontally scrollable */}
          <div className="flex items-center gap-1 relative" style={{ borderBottom: '1px solid rgba(6,182,212,0.10)' }}>
            {/* Scroll left */}
            <button
              onClick={() => tabScrollRef.current?.scrollBy({ left: -160, behavior: 'smooth' })}
              className="shrink-0 p-1 rounded transition-all"
              style={{ color: 'rgba(6,182,212,0.4)', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(6,182,212,0.12)' }}
            ><ChevronLeft size={12} /></button>

            {/* Scrollable tab strip */}
            <div ref={tabScrollRef}
              className="flex items-center gap-0.5 overflow-x-auto flex-1"
              style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>

              {/* Group: AI */}
              {(['console','voice','models','persona','neuro','memory'] as RightPanel[]).map(id => {
                const t = tabs.find(x => x.id === id)!;
                return (
                  <button key={t.id} onClick={() => setRightPanel(t.id)}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] font-bold transition-all"
                    style={{
                      color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.28)',
                      borderBottom: rightPanel === t.id ? `2px solid ${t.color}` : '2px solid transparent',
                      background: rightPanel === t.id ? `color-mix(in srgb, ${t.color} 9%, transparent)` : 'transparent',
                      whiteSpace: 'nowrap',
                    }}>{t.icon} {t.label}
                  </button>
                );
              })}

              <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)', flexShrink: 0, margin: '0 4px' }} />

              {/* Group: Platform */}
              {(['skills','cron','swarm','feed','vision','brief'] as RightPanel[]).map(id => {
                const t = tabs.find(x => x.id === id)!;
                return (
                  <button key={t.id} onClick={() => setRightPanel(t.id)}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] font-bold transition-all"
                    style={{
                      color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.28)',
                      borderBottom: rightPanel === t.id ? `2px solid ${t.color}` : '2px solid transparent',
                      background: rightPanel === t.id ? `color-mix(in srgb, ${t.color} 9%, transparent)` : 'transparent',
                      whiteSpace: 'nowrap',
                    }}>{t.icon} {t.label}
                  </button>
                );
              })}

              <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)', flexShrink: 0, margin: '0 4px' }} />

              {/* Group: Connect */}
              {(['cast','calendar','gmail'] as RightPanel[]).map(id => {
                const t = tabs.find(x => x.id === id)!;
                return (
                  <button key={t.id} onClick={() => setRightPanel(t.id)}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] font-bold transition-all"
                    style={{
                      color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.28)',
                      borderBottom: rightPanel === t.id ? `2px solid ${t.color}` : '2px solid transparent',
                      background: rightPanel === t.id ? `color-mix(in srgb, ${t.color} 9%, transparent)` : 'transparent',
                      whiteSpace: 'nowrap',
                    }}>{t.icon} {t.label}
                  </button>
                );
              })}

              <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)', flexShrink: 0, margin: '0 4px' }} />

              {/* Group: System */}
              {(['stats','logs','files','git','docker','backup','updates','radar'] as RightPanel[]).map(id => {
                const t = tabs.find(x => x.id === id)!;
                return (
                  <button key={t.id} onClick={() => setRightPanel(t.id)}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] font-bold transition-all"
                    style={{
                      color: rightPanel === t.id ? t.color : 'rgba(255,255,255,0.28)',
                      borderBottom: rightPanel === t.id ? `2px solid ${t.color}` : '2px solid transparent',
                      background: rightPanel === t.id ? `color-mix(in srgb, ${t.color} 9%, transparent)` : 'transparent',
                      whiteSpace: 'nowrap',
                    }}>{t.icon} {t.label}
                  </button>
                );
              })}
            </div>

            {/* Scroll right */}
            <button
              onClick={() => tabScrollRef.current?.scrollBy({ left: 160, behavior: 'smooth' })}
              className="shrink-0 p-1 rounded transition-all"
              style={{ color: 'rgba(6,182,212,0.4)', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(6,182,212,0.12)' }}
            ><ChevronRight size={12} /></button>

            {/* Active tab breadcrumb */}
            {(() => { const t = tabs.find(x => x.id === rightPanel); return t ? (
              <span className="shrink-0 ml-2 text-[8px] uppercase tracking-[0.3em] font-bold px-2 py-0.5 rounded"
                style={{ color: t.color, background: `color-mix(in srgb, ${t.color} 10%, transparent)`, border: `1px solid ${t.color}30` }}>
                {t.label}
              </span>
            ) : null; })()}
          </div>

          {/* Console panel */}
          {rightPanel === 'console' && (
            <div className="flex-1 grid grid-rows-2 gap-4 min-h-0">
              <div className="relative glass glass-green cyber-corners cyber-corners-green rounded-lg overflow-hidden">
                <div className="panel-header-green absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2 pointer-events-none">
                  <div className="flex items-center gap-2">
                    <TerminalIcon size={11} style={{ color: 'var(--green)' }} />
                    <span className="text-[9px] uppercase tracking-[0.3em] neon-green">Interactive Shell</span>
                  </div>
                  <div className="flex gap-1.5">
                    {['#f43f5e','#f59e0b','#22c55e'].map(c => (
                      <div key={c} style={{ width:8, height:8, borderRadius:'50%', backgroundColor: c, opacity:0.7 }} />
                    ))}
                  </div>
                </div>
                <div className="pt-8 h-full">
                  <Terminal />
                </div>
              </div>
              <div className="relative min-h-0">
                <Chat />
              </div>
            </div>
          )}

          {/* Skills panel */}
          {rightPanel === 'skills' && (
            <div className="flex-1 overflow-y-auto min-h-0">
              <Skills />
            </div>
          )}

          {/* Cron panel */}
          {rightPanel === 'cron' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <CronManager />
            </div>
          )}

          {/* Cast panel */}
          {rightPanel === 'cast' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <CastControl />
            </div>
          )}

          {/* Calendar panel */}
          {rightPanel === 'calendar' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <CalendarPanel />
            </div>
          )}

          {/* Models panel */}
          {rightPanel === 'models' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <ModelSwitcher />
            </div>
          )}

          {/* Memory Browser panel */}
          {rightPanel === 'memory' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <MemoryBrowser />
            </div>
          )}

          {/* Voice Chat panel */}
          {rightPanel === 'voice' && (
            <div className="flex-1 flex flex-col min-h-0 p-1">
              <VoiceChat />
            </div>
          )}

          {/* Agent Feed panel */}
          {rightPanel === 'feed' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <AgentFeed />
            </div>
          )}

          {/* Persona Editor panel */}
          {rightPanel === 'persona' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <PersonaEditor />
            </div>
          )}

          {/* Gmail panel */}
          {rightPanel === 'gmail' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <GmailPanel />
            </div>
          )}

          {/* Neuro editor panel */}
          {rightPanel === 'neuro' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <NeuroEditor />
            </div>
          )}

          {/* Vision panel */}
          {rightPanel === 'vision' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <VisionPanel />
            </div>
          )}

          {/* System updater panel */}
          {rightPanel === 'updates' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <SystemUpdater />
            </div>
          )}

          {/* Daily brief panel */}
          {rightPanel === 'brief' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <DailyBrief />
            </div>
          )}

          {/* Docker manager panel */}
          {rightPanel === 'docker' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <DockerManager />
            </div>
          )}

          {/* System Stats panel */}
          {rightPanel === 'stats' && (
            <div className="flex-1 min-h-0">
              <SystemStats />
            </div>
          )}

          {/* Log Viewer panel */}
          {rightPanel === 'logs' && (
            <div className="flex-1 min-h-0">
              <LogViewer />
            </div>
          )}

          {/* File Browser panel */}
          {rightPanel === 'files' && (
            <div className="flex-1 min-h-0">
              <FileBrowser />
            </div>
          )}

          {/* Git Panel */}
          {rightPanel === 'git' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <GitPanel />
            </div>
          )}

          {/* Backup Panel */}
          {rightPanel === 'backup' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <BackupPanel />
            </div>
          )}
          {rightPanel === 'swarm' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <SwarmPanel />
            </div>
          )}
          {rightPanel === 'radar' && (
            <div className="flex-1 overflow-y-auto min-h-0 p-1">
              <UpgradeRadar />
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
