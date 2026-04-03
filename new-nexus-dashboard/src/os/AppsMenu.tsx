import { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Search } from 'lucide-react';
import type { WindowDef } from './WindowManager';

// Lazy imports — components are only resolved when opened
import Chat from '../components/Chat';
import Terminal from '../components/Terminal';
import NeuroEditor from '../components/NeuroEditor';
import SystemStats from '../components/SystemStats';
import MemoryBrowser from '../components/MemoryBrowser';
import CastControl from '../components/CastControl';
import AgentFeed from '../components/AgentFeed';
import BackupPanel from '../components/BackupPanel';
import CalendarPanel from '../components/CalendarPanel';
import CronManager from '../components/CronManager';
import DailyBrief from '../components/DailyBrief';
import DockerManager from '../components/DockerManager';
import FileBrowser from '../components/FileBrowser';
import GitPanel from '../components/GitPanel';
import GmailPanel from '../components/GmailPanel';
import LogViewer from '../components/LogViewer';
import ModelSwitcher from '../components/ModelSwitcher';
import PersonaEditor from '../components/PersonaEditor';
import Skills from '../components/Skills';
import SwarmPanel from '../components/SwarmPanel';
import SystemUpdater from '../components/SystemUpdater';
import UpgradeRadar from '../components/UpgradeRadar';
import VisionPanel from '../components/VisionPanel';
import VoiceChat from '../components/VoiceChat';
import YouTubePanel from '../components/YouTubePanel';

export interface AppDef {
  id: string;
  title: string;
  icon: string;
  category: 'core' | 'system' | 'connect' | 'tools';
  component: React.ReactNode;
  defaultSize?: { width: number; height: number };
  dockDefault?: boolean; // shown in main dock
}

export const ALL_APPS: AppDef[] = [
  // Core
  { id: 'chat',     title: 'Milla',       icon: '✦', category: 'core',    component: <Chat />,          defaultSize: { width: 420, height: 560 }, dockDefault: true },
  { id: 'terminal', title: 'Terminal',    icon: '⬡', category: 'core',    component: <Terminal />,      defaultSize: { width: 560, height: 400 }, dockDefault: true },
  { id: 'youtube',  title: 'YouTube',     icon: '▶', category: 'core',    component: <YouTubePanel />,  defaultSize: { width: 480, height: 360 }, dockDefault: true },
  { id: 'voice',    title: 'Voice',       icon: '◎', category: 'core',    component: <VoiceChat />,     defaultSize: { width: 340, height: 300 } },
  { id: 'vision',   title: 'Vision',      icon: '◉', category: 'core',    component: <VisionPanel />,   defaultSize: { width: 520, height: 420 } },
  { id: 'brief',    title: 'Daily Brief', icon: '◈', category: 'core',    component: <DailyBrief />,    defaultSize: { width: 400, height: 480 } },
  // System
  { id: 'stats',    title: 'Stats',       icon: '⬟', category: 'system',  component: <SystemStats />,   defaultSize: { width: 480, height: 460 }, dockDefault: true },
  { id: 'neuro',    title: 'Neuro',       icon: '⬠', category: 'system',  component: <NeuroEditor />,   defaultSize: { width: 340, height: 420 }, dockDefault: true },
  { id: 'logs',     title: 'Logs',        icon: '≡',  category: 'system',  component: <LogViewer />,     defaultSize: { width: 540, height: 400 } },
  { id: 'updater',  title: 'Updater',     icon: '↑',  category: 'system',  component: <SystemUpdater />, defaultSize: { width: 400, height: 360 } },
  { id: 'backup',   title: 'Backup',      icon: '◷',  category: 'system',  component: <BackupPanel />,   defaultSize: { width: 400, height: 380 } },
  { id: 'cron',     title: 'Cron',        icon: '⏲',  category: 'system',  component: <CronManager />,   defaultSize: { width: 440, height: 400 } },
  { id: 'docker',   title: 'Docker',      icon: '⬡', category: 'system',  component: <DockerManager />, defaultSize: { width: 500, height: 460 } },
  { id: 'upgrade',  title: 'Upgrade',     icon: '⬆', category: 'system',  component: <UpgradeRadar />,  defaultSize: { width: 440, height: 400 } },
  // Connect
  { id: 'cast',     title: 'Cast',        icon: '⊙',  category: 'connect', component: <CastControl />,   defaultSize: { width: 380, height: 360 }, dockDefault: true },
  { id: 'gmail',    title: 'Gmail',       icon: '✉',  category: 'connect', component: <GmailPanel />,    defaultSize: { width: 480, height: 520 } },
  { id: 'calendar', title: 'Calendar',    icon: '▦',  category: 'connect', component: <CalendarPanel />, defaultSize: { width: 480, height: 480 } },
  { id: 'swarm',    title: 'Swarm',       icon: '⬡', category: 'connect', component: <SwarmPanel />,    defaultSize: { width: 500, height: 440 } },
  { id: 'agents',   title: 'Agents',      icon: '⊕',  category: 'connect', component: <AgentFeed />,     defaultSize: { width: 460, height: 480 } },
  // Tools
  { id: 'memory',   title: 'Memory',      icon: '◌',  category: 'tools',   component: <MemoryBrowser />, defaultSize: { width: 500, height: 500 } },
  { id: 'files',    title: 'Files',       icon: '▣',  category: 'tools',   component: <FileBrowser />,   defaultSize: { width: 480, height: 500 } },
  { id: 'git',      title: 'Git',         icon: '⌥',  category: 'tools',   component: <GitPanel />,      defaultSize: { width: 460, height: 460 } },
  { id: 'skills',   title: 'Skills',      icon: '⚡', category: 'tools',   component: <Skills />,        defaultSize: { width: 440, height: 480 } },
  { id: 'model',    title: 'Model',       icon: '⊛',  category: 'tools',   component: <ModelSwitcher />, defaultSize: { width: 360, height: 320 } },
  { id: 'persona',  title: 'Persona',     icon: '⊜',  category: 'tools',   component: <PersonaEditor />, defaultSize: { width: 400, height: 440 } },
];

const CATEGORY_LABELS: Record<AppDef['category'], string> = {
  core: 'Core',
  system: 'System',
  connect: 'Connect',
  tools: 'Tools',
};

const CATEGORIES: AppDef['category'][] = ['core', 'system', 'connect', 'tools'];

interface Props {
  onOpen: (def: WindowDef) => void;
}

export default function AppsMenu({ onOpen }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<AppDef['category'] | 'all'>('all');

  const filtered = ALL_APPS.filter(app => {
    const matchesSearch = !query.trim() || app.title.toLowerCase().includes(query.toLowerCase());
    const matchesCat = activeCategory === 'all' || app.category === activeCategory;
    return matchesSearch && matchesCat;
  });

  const launch = (app: AppDef) => {
    onOpen({ id: app.id, title: app.title, icon: app.icon, component: app.component, defaultSize: app.defaultSize });
    setOpen(false);
    setQuery('');
  };

  return (
    <>
      {/* Dock trigger button */}
      <button
        onClick={() => setOpen(o => !o)}
        title="All Apps"
        style={{
          width: '44px', height: '44px', borderRadius: '12px',
          background: open ? 'rgba(168,85,247,0.2)' : 'rgba(168,85,247,0.06)',
          border: `1px solid ${open ? 'rgba(168,85,247,0.5)' : 'rgba(168,85,247,0.15)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '20px', cursor: 'pointer', color: open ? '#a855f7' : 'rgba(168,85,247,0.4)',
          boxShadow: open ? '0 0 14px rgba(168,85,247,0.25)' : 'none',
          transition: 'transform 0.15s cubic-bezier(.34,1.56,.64,1), background 0.15s ease',
          fontFamily: 'inherit',
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(-12px) scale(1.22)';
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLElement).style.transform = 'translateY(0) scale(1)';
        }}
      >
        ⊞
      </button>

      {/* Overlay — rendered via portal to escape dock's transform stacking context */}
      {open && createPortal(
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 99990,
            background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)',
          }}
          onClick={() => setOpen(false)}
        >
          <div
          onClick={e => e.stopPropagation()}
          style={{
            position: 'fixed',
            top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 'min(680px, 92vw)',
            height: 'min(580px, 80vh)',
            background: 'rgba(8,10,16,0.97)', backdropFilter: 'blur(24px)',
            border: '1px solid rgba(168,85,247,0.2)', borderRadius: '18px',
            boxShadow: '0 32px 80px rgba(0,0,0,0.9), 0 0 0 1px rgba(168,85,247,0.06)',
            display: 'flex', flexDirection: 'column',
            overflow: 'hidden',
            fontFamily: "'JetBrains Mono', monospace",
            zIndex: 99991,
          }}
          >
            {/* Header */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '16px 20px 12px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}>
              <Search size={13} style={{ color: 'rgba(168,85,247,0.5)', flexShrink: 0 }} />
              <input
                autoFocus
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search apps..."
                style={{
                  flex: 1, background: 'none', border: 'none', outline: 'none',
                  fontSize: '13px', color: 'rgba(255,255,255,0.8)',
                  letterSpacing: '0.03em', fontFamily: 'inherit',
                }}
              />
              <button onClick={() => setOpen(false)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'rgba(255,255,255,0.2)', padding: '2px',
              }}>
                <X size={14} />
              </button>
            </div>

            {/* Category tabs */}
            {!query.trim() && (
              <div style={{
                display: 'flex', gap: '4px', padding: '10px 20px 6px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
              }}>
                {(['all', ...CATEGORIES] as const).map(cat => (
                  <button
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    style={{
                      padding: '3px 12px', borderRadius: '20px', fontSize: '9px',
                      letterSpacing: '0.15em', textTransform: 'uppercase', cursor: 'pointer',
                      fontFamily: 'inherit',
                      background: activeCategory === cat ? 'rgba(168,85,247,0.18)' : 'transparent',
                      border: `1px solid ${activeCategory === cat ? 'rgba(168,85,247,0.4)' : 'rgba(255,255,255,0.08)'}`,
                      color: activeCategory === cat ? '#a855f7' : 'rgba(255,255,255,0.3)',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {cat === 'all' ? 'All' : CATEGORY_LABELS[cat]}
                  </button>
                ))}
                <span style={{ marginLeft: 'auto', fontSize: '9px', color: 'rgba(255,255,255,0.15)', alignSelf: 'center' }}>
                  {filtered.length} apps
                </span>
              </div>
            )}

            {/* App grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
              gap: '8px', padding: '16px 20px 20px',
              overflowY: 'auto',
              flex: 1,
            }}>
              {filtered.map(app => (
                <button
                  key={app.id}
                  onClick={() => launch(app)}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                    padding: '14px 8px', borderRadius: '14px', cursor: 'pointer',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    transition: 'background 0.15s ease, border-color 0.15s ease, transform 0.1s ease',
                    fontFamily: 'inherit',
                  }}
                  onMouseEnter={e => {
                    const el = e.currentTarget as HTMLElement;
                    el.style.background = 'rgba(168,85,247,0.1)';
                    el.style.borderColor = 'rgba(168,85,247,0.3)';
                    el.style.transform = 'scale(1.05)';
                  }}
                  onMouseLeave={e => {
                    const el = e.currentTarget as HTMLElement;
                    el.style.background = 'rgba(255,255,255,0.03)';
                    el.style.borderColor = 'rgba(255,255,255,0.06)';
                    el.style.transform = 'scale(1)';
                  }}
                >
                  <span style={{ fontSize: '26px', lineHeight: 1 }}>{app.icon}</span>
                  <span style={{
                    fontSize: '9px', color: 'rgba(255,255,255,0.55)',
                    letterSpacing: '0.08em', textTransform: 'uppercase', textAlign: 'center',
                  }}>
                    {app.title}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      , document.body)}
    </>
  );
}
