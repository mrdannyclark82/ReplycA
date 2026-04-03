import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import RayneOS from './os/RayneOS';

// Auth all API calls with the internal key (set at build time via env)
const AXIOM_KEY = import.meta.env.VITE_AXIOM_KEY ?? '';
const AXIOM_USER = import.meta.env.VITE_AXIOM_USER ?? 'dannyrayclark';
if (AXIOM_KEY) {
  axios.defaults.headers.common['x-internal-key'] = AXIOM_KEY;
  axios.defaults.headers.common['x-user-id'] = AXIOM_USER;
}

// Sandbox mode: /axiom-rayne/?os=1 renders RayneOS shell
const OS_MODE = new URLSearchParams(window.location.search).get('os') === '1';
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
import {
  Shield,
  Terminal as TerminalIcon,
  Package,
  Clock,
  Tv,
  Calendar,
  Cpu,
  Database,
  Mic,
  Activity,
  User,
  LayoutGrid as _LayoutGrid,
  Mail,
  Zap,
  Eye,
  ArrowUpCircle,
  BookOpen,
  Box,
  BarChart2,
  FileText,
  FolderOpen,
  GitBranch,
  Archive,
  Bell,
  Search as SearchIcon,
  X,
  Bot,
  Radar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import InstallPWA from './components/InstallPWA';
import './App.css';

type RightPanel =
  | 'console'
  | 'skills'
  | 'cron'
  | 'cast'
  | 'calendar'
  | 'models'
  | 'memory'
  | 'voice'
  | 'feed'
  | 'persona'
  | 'gmail'
  | 'neuro'
  | 'vision'
  | 'updates'
  | 'brief'
  | 'docker'
  | 'stats'
  | 'logs'
  | 'files'
  | 'git'
  | 'backup'
  | 'swarm'
  | 'radar';

interface Alert {
  type: string;
  source: string;
  text: string;
}

interface SearchResult {
  source: string;
  id: string | number;
  text: string;
  meta: string;
}

const WS_SERVER = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

const panelDetails: Record<
  RightPanel,
  {
    label: string;
    short: string;
    summary: string;
    group: string;
    icon: React.ReactNode;
    color: string;
  }
> = {
  console: {
    label: 'Console',
    short: 'Shell and chat',
    summary: 'Interactive shell, terminal output, and direct operator chat.',
    group: 'Core',
    icon: <TerminalIcon size={12} />,
    color: 'var(--green)',
  },
  skills: {
    label: 'Skills',
    short: 'Capability registry',
    summary: 'Installed capabilities, execution hooks, and active workflow assets.',
    group: 'Core',
    icon: <Package size={12} />,
    color: 'var(--purple)',
  },
  cron: {
    label: 'Cron',
    short: 'Scheduled jobs',
    summary: 'Time-based automation, cadence tracking, and background task control.',
    group: 'Automation',
    icon: <Clock size={12} />,
    color: 'var(--amber)',
  },
  cast: {
    label: 'Cast',
    short: 'Broadcast control',
    summary: 'Screen, stream, and external display management.',
    group: 'Connect',
    icon: <Tv size={12} />,
    color: 'var(--cyan)',
  },
  calendar: {
    label: 'Calendar',
    short: 'Schedule view',
    summary: 'Upcoming events, availability, and time coordination.',
    group: 'Connect',
    icon: <Calendar size={12} />,
    color: '#2f5fe8',
  },
  models: {
    label: 'Models',
    short: 'Runtime routing',
    summary: 'Provider switching, model selection, and execution posture.',
    group: 'Core',
    icon: <Cpu size={12} />,
    color: '#ff7ab6',
  },
  memory: {
    label: 'Memory',
    short: 'Recall and storage',
    summary: 'Persistent records, retrieval surfaces, and historical context.',
    group: 'Core',
    icon: <Database size={12} />,
    color: '#4ade80',
  },
  voice: {
    label: 'Voice',
    short: 'Audio operations',
    summary: 'Voice session control, capture, and conversational monitoring.',
    group: 'Core',
    icon: <Mic size={12} />,
    color: '#ff8b7b',
  },
  feed: {
    label: 'Feed',
    short: 'Agent activity',
    summary: 'Live task flow, runtime behavior, and agent-side state changes.',
    group: 'Automation',
    icon: <Activity size={12} />,
    color: '#3a6df0',
  },
  persona: {
    label: 'Persona',
    short: 'Identity tuning',
    summary: 'Behavioral framing, role presets, and authored voice definitions.',
    group: 'Core',
    icon: <User size={12} />,
    color: '#f08bff',
  },
  gmail: {
    label: 'Gmail',
    short: 'Inbox bridge',
    summary: 'Mail visibility, outbound actions, and account-linked workflow state.',
    group: 'Connect',
    icon: <Mail size={12} />,
    color: '#ff7d70',
  },
  neuro: {
    label: 'Neuro',
    short: 'State controls',
    summary: 'Behavior signals, internal balance, and live system condition.',
    group: 'Core',
    icon: <Zap size={12} />,
    color: '#f7c94b',
  },
  vision: {
    label: 'Vision',
    short: 'Scene analysis',
    summary: 'Image-aware processing, capture handling, and visual inference.',
    group: 'Automation',
    icon: <Eye size={12} />,
    color: '#b194ff',
  },
  updates: {
    label: 'Updates',
    short: 'System refresh',
    summary: 'Upgrade paths, package work, and applied platform changes.',
    group: 'System',
    icon: <ArrowUpCircle size={12} />,
    color: '#4ade80',
  },
  brief: {
    label: 'Brief',
    short: 'Daily context',
    summary: 'Condensed events, priorities, and what changed since last check-in.',
    group: 'Automation',
    icon: <BookOpen size={12} />,
    color: '#3a6df0',
  },
  docker: {
    label: 'Docker',
    short: 'Container control',
    summary: 'Running containers, orchestration status, and local service lifecycle.',
    group: 'System',
    icon: <Box size={12} />,
    color: '#47c5ff',
  },
  stats: {
    label: 'Stats',
    short: 'Performance telemetry',
    summary: 'Host metrics, resource pressure, and runtime load visibility.',
    group: 'System',
    icon: <BarChart2 size={12} />,
    color: '#ff9a57',
  },
  logs: {
    label: 'Logs',
    short: 'Event history',
    summary: 'Recent system traces, runtime output, and incident breadcrumbs.',
    group: 'System',
    icon: <FileText size={12} />,
    color: '#a3b2c7',
  },
  files: {
    label: 'Files',
    short: 'Workspace access',
    summary: 'Project navigation, direct file inspection, and path-level operations.',
    group: 'System',
    icon: <FolderOpen size={12} />,
    color: '#f1d18a',
  },
  git: {
    label: 'Git',
    short: 'Repo state',
    summary: 'Branch context, commit flow, and local repository activity.',
    group: 'System',
    icon: <GitBranch size={12} />,
    color: '#b194ff',
  },
  backup: {
    label: 'Backup',
    short: 'Recovery surface',
    summary: 'Snapshots, retention checks, and restore readiness.',
    group: 'System',
    icon: <Archive size={12} />,
    color: '#55d88d',
  },
  swarm: {
    label: 'Swarm',
    short: 'Multi-agent fabric',
    summary: 'Distributed task flow, node coordination, and execution fan-out.',
    group: 'Automation',
    icon: <Bot size={12} />,
    color: '#ff5c86',
  },
  radar: {
    label: 'Radar',
    short: 'Upgrade horizon',
    summary: 'Signals worth attention, scan outcomes, and near-term system risk.',
    group: 'System',
    icon: <Radar size={12} />,
    color: 'var(--cyan)',
  },
};

const groupedPanels: { title: string; items: RightPanel[] }[] = [
  { title: 'Core', items: ['console', 'voice', 'models', 'persona', 'neuro', 'memory'] },
  { title: 'Automation', items: ['skills', 'cron', 'swarm', 'feed', 'vision', 'brief'] },
  { title: 'Connect', items: ['cast', 'calendar', 'gmail'] },
  { title: 'System', items: ['stats', 'logs', 'files', 'git', 'docker', 'backup', 'updates', 'radar'] },
];

function App() {
  const [unlocked, setUnlocked] = useState(() => localStorage.getItem('axiom_auth') === '1');
  const [pwInput, setPwInput] = useState('');
  const [pwError, setPwError] = useState(false);

  const handleUnlock = () => {
    if (pwInput === 'jamesbond') {
      localStorage.setItem('axiom_auth', '1');
      setUnlocked(true);
      setPwError(false);
    } else {
      setPwError(true);
      setPwInput('');
    }
  };

  if (!unlocked) {
    // OS mode shares the same auth gate
    if (OS_MODE) {
      return (
        <div style={{
          position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: 'radial-gradient(ellipse at 60% 40%, #0d1117 0%, #050709 100%)',
          gap: '1rem', fontFamily: "'JetBrains Mono', monospace",
        }}>
          <div style={{ color: '#06b6d4', fontSize: '1.2rem', letterSpacing: '0.4em' }}>RAYNE OS</div>
          <input
            type="password" value={pwInput} onChange={e => setPwInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleUnlock()}
            placeholder="access code"
            style={{
              background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.3)',
              color: '#06b6d4', padding: '8px 16px', borderRadius: '6px',
              fontFamily: 'inherit', fontSize: '13px', outline: 'none',
              textAlign: 'center', letterSpacing: '0.2em',
            }}
            autoFocus
          />
          {pwError && <div style={{ color: '#f43f5e', fontSize: '10px', letterSpacing: '0.2em' }}>ACCESS DENIED</div>}
        </div>
      );
    }
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', background: '#000', zIndex: 99999,
        gap: '1rem'
      }}>
        <div style={{ color: '#f59e0b', fontSize: '1.5rem', letterSpacing: '0.3em', fontFamily: 'monospace' }}>
          AXIOM
        </div>
        <input
          type="password"
          autoFocus
          value={pwInput}
          onChange={e => { setPwInput(e.target.value); setPwError(false); }}
          onKeyDown={e => e.key === 'Enter' && handleUnlock()}
          placeholder="access code"
          style={{
            background: 'transparent', border: `1px solid ${pwError ? '#ef4444' : '#f59e0b44'}`,
            color: '#f59e0b', padding: '0.5rem 1rem', fontFamily: 'monospace',
            fontSize: '1rem', outline: 'none', textAlign: 'center', letterSpacing: '0.2em',
            width: '220px', borderRadius: '2px'
          }}
        />
        {pwError && <div style={{ color: '#ef4444', fontFamily: 'monospace', fontSize: '0.75rem' }}>ACCESS DENIED</div>}
      </div>
    );
  }

  return OS_MODE ? <RayneOS /> : <AxiomDashboard />;
}

function AxiomDashboard() {
  const [nodes, setNodes] = useState({ termux: false, google: false, swarm: false });
  const [rightPanel, setRightPanel] = useState<RightPanel>('console');
  const tabScrollRef = useRef<HTMLDivElement>(null);
  const [neuro, setNeuro] = useState({ dopamine: 0.5, serotonin: 0.5, atp_energy: 100 });
  const neuroWs = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_SERVER}/ws/neuro`);
        neuroWs.current = ws;
        ws.onmessage = (e) => {
          try {
            setNeuro(JSON.parse(e.data));
          } catch {
            // ignore malformed payloads
          }
        };
        ws.onclose = () => setTimeout(connect, 5000);
        ws.onerror = () => ws.close();
      } catch {
        setTimeout(connect, 5000);
      }
    };

    connect();
    return () => neuroWs.current?.close();
  }, []);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [bellOpen, setBellOpen] = useState(false);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    const poll = () => {
      axios
        .get('/api/notifications')
        .then((r) => {
          if (r.data.ok) {
            setAlerts(r.data.alerts);
            setAlertCount(r.data.count);
          }
        })
        .catch(() => {});
    };

    poll();
    const iv = setInterval(poll, 30000);
    return () => clearInterval(iv);
  }, []);

  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const r = await axios.get(`/api/search?q=${encodeURIComponent(q)}`);
      if (r.data.ok) {
        setSearchResults(r.data.results);
      }
    } catch {
      // ignore search failures
    }
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
        setSearchOpen((open) => !open);
        setSearchQuery('');
        setSearchResults([]);
      }

      if (e.key === 'Escape') {
        setSearchOpen(false);
        setBellOpen(false);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (searchOpen) {
      setTimeout(() => searchRef.current?.focus(), 50);
    }
  }, [searchOpen]);

  useEffect(() => {
    const fetchNodes = () =>
      axios
        .get('/api/nodes')
        .then((r) => setNodes(r.data))
        .catch(() => {});

    fetchNodes();
    const interval = setInterval(fetchNodes, 10000);
    return () => clearInterval(interval);
  }, []);

  const activePanel = panelDetails[rightPanel];
  const liveSignals = [
    { key: 'dopamine', label: 'Dopamine', value: neuro.dopamine, color: '#f7c94b' },
    { key: 'serotonin', label: 'Serotonin', value: neuro.serotonin, color: '#6be7ff' },
    { key: 'atp', label: 'ATP', value: neuro.atp_energy / 100, color: '#63f2a1' },
  ];
  const nodeStatus = [
    { label: 'Termux Bridge', active: nodes.termux, color: '#63f2a1' },
    { label: 'Google OAuth', active: nodes.google, color: nodes.google ? '#63f2a1' : '#f7c94b' },
    { label: 'Swarm Sync', active: nodes.swarm, color: '#6be7ff' },
  ];

  const renderActivePanel = () => {
    switch (rightPanel) {
      case 'console':
        return (
          <div className="console-stack">
            <section className="console-stage">
              <div className="console-stage__bar">
                <div className="console-stage__label">
                  <TerminalIcon size={12} />
                  <span>Interactive shell</span>
                </div>
                <div className="console-stage__lights">
                  {['#f43f5e', '#f59e0b', '#22c55e'].map((color) => (
                    <span key={color} style={{ backgroundColor: color }} />
                  ))}
                </div>
              </div>
              <div className="console-stage__body">
                <Terminal />
              </div>
            </section>
            <section className="chat-stage">
              <Chat />
            </section>
          </div>
        );
      case 'skills':
        return <Skills />;
      case 'cron':
        return <CronManager />;
      case 'cast':
        return <CastControl />;
      case 'calendar':
        return <CalendarPanel />;
      case 'models':
        return <ModelSwitcher />;
      case 'memory':
        return <MemoryBrowser />;
      case 'voice':
        return <VoiceChat />;
      case 'feed':
        return <AgentFeed />;
      case 'persona':
        return <PersonaEditor />;
      case 'gmail':
        return <GmailPanel />;
      case 'neuro':
        return <NeuroEditor />;
      case 'vision':
        return <VisionPanel />;
      case 'updates':
        return <SystemUpdater />;
      case 'brief':
        return <DailyBrief />;
      case 'docker':
        return <DockerManager />;
      case 'stats':
        return <SystemStats />;
      case 'logs':
        return <LogViewer />;
      case 'files':
        return <FileBrowser />;
      case 'git':
        return <GitPanel />;
      case 'backup':
        return <BackupPanel />;
      case 'swarm':
        return <SwarmPanel />;
      case 'radar':
        return <UpgradeRadar />;
      default:
        return null;
    }
  };

  return (
    <div className="app-shell">
      <div className="app-shell__aurora app-shell__aurora--left" />
      <div className="app-shell__aurora app-shell__aurora--right" />
      <div className="app-shell__grid" />

      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-lockup__mark">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <p className="brand-lockup__eyebrow">Command deck</p>
            <h1 className="brand-lockup__title">Nexus Kingdom</h1>
          </div>
        </div>

        <div className="app-header__meta">
          <div className="header-chip">
            <span className="header-chip__label">Mode</span>
            <span className="header-chip__value">Forever Morth Platform</span>
          </div>
          <div className="header-chip">
            <span className="header-chip__label">Architect</span>
            <span className="header-chip__value">Storm · D-Ray</span>
          </div>
        </div>

        <div className="app-header__actions">
          <button
            onClick={() => {
              setSearchOpen(true);
              setSearchQuery('');
              setSearchResults([]);
            }}
            className="header-action"
            title="Search (Ctrl+K)"
          >
            <SearchIcon size={14} />
            <span>Search</span>
            <kbd>Ctrl K</kbd>
          </button>

          <div className="header-bell">
            <button
              onClick={() => setBellOpen((open) => !open)}
              className={`header-action ${alertCount > 0 ? 'header-action--alert' : ''}`}
              title="Alerts"
            >
              <Bell size={14} />
              <span>Alerts</span>
              {alertCount > 0 && <strong>{alertCount}</strong>}
            </button>

            {bellOpen && (
              <div className="bell-popover">
                <div className="bell-popover__header">Alerts</div>
                {alerts.length === 0 ? (
                  <div className="bell-popover__empty">All clear</div>
                ) : (
                  alerts.map((alert, index) => (
                    <div key={`${alert.source}-${index}`} className="bell-item">
                      <div className="bell-item__source">{alert.source}</div>
                      <div className="bell-item__text">{alert.text}</div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          <InstallPWA />
        </div>
      </header>

      {searchOpen && (
        <div
          className="search-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setSearchOpen(false);
            }
          }}
        >
          <div className="search-dialog">
            <div className="search-dialog__bar">
              <SearchIcon size={16} />
              <input
                ref={searchRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search memory, skills, feed..."
              />
              {searching && <span className="search-dialog__status">searching...</span>}
              <button onClick={() => setSearchOpen(false)} className="search-dialog__close">
                <X size={14} />
              </button>
            </div>
            <div className="search-dialog__results">
              {searchResults.length === 0 && searchQuery.length >= 2 && !searching && (
                <div className="search-dialog__empty">No results for "{searchQuery}"</div>
              )}
              {searchQuery.length < 2 && (
                <div className="search-dialog__empty">Type to search memories, skills, and feed.</div>
              )}
              {searchResults.map((result, index) => {
                const sourceColors: Record<string, string> = {
                  memory: '#4ade80',
                  skill: '#f7c94b',
                  feed: '#2f5fe8',
                };
                return (
                  <button
                    key={`${result.source}-${result.id}-${index}`}
                    className="search-result"
                    onClick={() => {
                      if (result.source === 'memory') {
                        setRightPanel('memory');
                      } else if (result.source === 'skill') {
                        setRightPanel('skills');
                      } else {
                        setRightPanel('feed');
                      }
                      setSearchOpen(false);
                    }}
                  >
                    <div className="search-result__meta">
                      <span
                        className="search-result__source"
                        style={{ color: sourceColors[result.source] || '#c8d5f0' }}
                      >
                        {result.source}
                      </span>
                      <span>{result.meta}</span>
                    </div>
                    <div className="search-result__text">{result.text}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <main className="command-layout">
        <aside className="command-rail">
          <section className="rail-panel rail-panel--hud">
            <div className="rail-panel__eyebrow">Live shell</div>
            <HUD />
          </section>

          <section className="rail-panel">
            <div className="rail-panel__eyebrow">Systems online</div>
            <div className="status-list">
              {nodeStatus.map((item) => (
                <div key={item.label} className="status-list__item">
                  <span>{item.label}</span>
                  <span
                    className={`status-list__dot ${item.active ? 'is-active' : ''}`}
                    style={{ '--status-color': item.color } as React.CSSProperties}
                  />
                </div>
              ))}
            </div>
          </section>

          <section className="rail-panel">
            <div className="rail-panel__eyebrow">Navigation</div>
            <div className="nav-groups">
              {groupedPanels.map((group) => (
                <div key={group.title} className="nav-group">
                  <p className="nav-group__title">{group.title}</p>
                  <div className="nav-group__list">
                    {group.items.map((panelId) => {
                      const panel = panelDetails[panelId];
                      const isActive = rightPanel === panelId;
                      return (
                        <button
                          key={panelId}
                          onClick={() => setRightPanel(panelId)}
                          className={`nav-item ${isActive ? 'is-active' : ''}`}
                          style={
                            {
                              '--panel-color': panel.color,
                            } as React.CSSProperties
                          }
                        >
                          <span className="nav-item__icon">{panel.icon}</span>
                          <span>
                            <strong>{panel.label}</strong>
                            <small>{panel.short}</small>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <section className="workspace-shell">
          <section className="mission-strip">
            <div className="mission-strip__copy">
              <p className="mission-strip__eyebrow">Current workspace</p>
              <div className="mission-strip__headline">
                <span className="mission-strip__title">{activePanel.label}</span>
                <span
                  className="mission-strip__pill"
                  style={{ '--panel-color': activePanel.color } as React.CSSProperties}
                >
                  {activePanel.group}
                </span>
              </div>
              <p className="mission-strip__summary">{activePanel.summary}</p>
            </div>

            <div className="mission-strip__metrics">
              <div className="metric-block">
                <span className="metric-block__label">Neuro state</span>
                <div className="signal-list">
                  {liveSignals.map((signal) => (
                    <div key={signal.key} className="signal-list__item">
                      <div className="signal-list__head">
                        <span>{signal.label}</span>
                        <span>{Math.round(signal.value * 100)}%</span>
                      </div>
                      <div className="signal-list__track">
                        <div
                          className="signal-list__fill"
                          style={{ width: `${Math.min(100, signal.value * 100)}%`, background: signal.color }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="metric-block">
                <span className="metric-block__label">Mission pulse</span>
                <div className="mission-pulse">
                  <div>
                    <strong>{nodeStatus.filter((item) => item.active).length}/3</strong>
                    <span>linked systems</span>
                  </div>
                  <div>
                    <strong>{alertCount}</strong>
                    <span>open alerts</span>
                  </div>
                  <div>
                    <strong>{activePanel.group}</strong>
                    <span>active track</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div className="workspace-nav">
            <button
              onClick={() => tabScrollRef.current?.scrollBy({ left: -180, behavior: 'smooth' })}
              className="workspace-nav__arrow"
            >
              <ChevronLeft size={14} />
            </button>

            <div ref={tabScrollRef} className="workspace-nav__tabs">
              {groupedPanels.map((group) => (
                <div key={group.title} className="workspace-nav__group">
                  <span className="workspace-nav__group-label">{group.title}</span>
                  {group.items.map((panelId) => {
                    const panel = panelDetails[panelId];
                    const isActive = rightPanel === panelId;
                    return (
                      <button
                        key={panelId}
                        onClick={() => setRightPanel(panelId)}
                        className={`workspace-tab ${isActive ? 'is-active' : ''}`}
                        style={
                          {
                            '--panel-color': panel.color,
                          } as React.CSSProperties
                        }
                      >
                        {panel.icon}
                        <span>{panel.label}</span>
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>

            <button
              onClick={() => tabScrollRef.current?.scrollBy({ left: 180, behavior: 'smooth' })}
              className="workspace-nav__arrow"
            >
              <ChevronRight size={14} />
            </button>
          </div>

          <section
            className={`workspace-stage ${rightPanel === 'console' ? 'workspace-stage--console' : ''}`}
            style={{ '--panel-color': activePanel.color } as React.CSSProperties}
          >
            {renderActivePanel()}
          </section>
        </section>
      </main>
    </div>
  );
}

export default App;
