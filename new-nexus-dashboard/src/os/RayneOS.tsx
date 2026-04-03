import { Shield } from 'lucide-react';
import { WindowManager, useWindowManager } from './WindowManager';
import Chat from '../components/Chat';
import Terminal from '../components/Terminal';
import NeuroEditor from '../components/NeuroEditor';
import SystemStats from '../components/SystemStats';
import MemoryBrowser from '../components/MemoryBrowser';
import CastControl from '../components/CastControl';

const DOCK_APPS = [
  { id: 'chat',    title: 'Milla',    icon: '✦', component: <Chat />,          size: { width: 420, height: 560 } },
  { id: 'terminal',title: 'Terminal', icon: '⬡', component: <Terminal />,      size: { width: 560, height: 400 } },
  { id: 'neuro',   title: 'Neuro',    icon: '◈', component: <NeuroEditor />,   size: { width: 340, height: 420 } },
  { id: 'stats',   title: 'Stats',    icon: '◉', component: <SystemStats />,   size: { width: 480, height: 460 } },
  { id: 'memory',  title: 'Memory',   icon: '◎', component: <MemoryBrowser />, size: { width: 500, height: 500 } },
  { id: 'cast',    title: 'Cast',     icon: '▶', component: <CastControl />,   size: { width: 380, height: 360 } },
];

export default function RayneOS() {
  const wm = useWindowManager();

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'radial-gradient(ellipse at 60% 40%, #0d1117 0%, #050709 100%)',
      overflow: 'hidden', fontFamily: "'JetBrains Mono', monospace",
    }}>
      {/* Grid overlay */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `linear-gradient(rgba(6,182,212,0.03) 1px, transparent 1px),linear-gradient(90deg, rgba(6,182,212,0.03) 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
      }} />

      {/* Status bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '28px',
        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(6,182,212,0.12)',
        display: 'flex', alignItems: 'center', padding: '0 16px', gap: '8px', zIndex: 9999,
      }}>
        <Shield size={11} style={{ color: '#06b6d4' }} />
        <span style={{ fontSize: '10px', color: 'rgba(6,182,212,0.7)', letterSpacing: '0.2em', textTransform: 'uppercase' }}>Rayne OS</span>
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', marginLeft: '4px' }}>· sandbox</span>
        <div style={{ flex: 1 }} />
        {wm.windows.filter(w => !w.minimized).length > 0 && (
          <span style={{ fontSize: '9px', color: 'rgba(6,182,212,0.4)', letterSpacing: '0.1em' }}>
            {wm.windows.filter(w => !w.minimized).length} open
          </span>
        )}
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)' }}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Desktop */}
      <div id="rayne-desktop" style={{ position: 'absolute', top: '28px', left: 0, right: 0, bottom: '80px' }}>
        <WindowManager
          windows={wm.windows}
          onClose={wm.close} onFocus={wm.focus} onMinimize={wm.minimize}
          onDock={wm.toggleDock} onPin={wm.togglePin} onMove={wm.move} onResize={wm.resize}
        />
        {wm.windows.length === 0 && (
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -60%)', textAlign: 'center', pointerEvents: 'none' }}>
            <div style={{ fontSize: '11px', color: 'rgba(6,182,212,0.2)', letterSpacing: '0.4em', textTransform: 'uppercase', marginBottom: '8px' }}>Rayne OS</div>
            <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.1)', letterSpacing: '0.2em' }}>click an icon to open</div>
          </div>
        )}
      </div>

      {/* Cairo dock */}
      <div style={{
        position: 'absolute', bottom: '12px', left: '50%', transform: 'translateX(-50%)',
        display: 'flex', alignItems: 'flex-end', gap: '6px',
        padding: '10px 20px 8px',
        background: 'rgba(255,255,255,0.04)', backdropFilter: 'blur(20px)',
        borderRadius: '20px', border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
        zIndex: 9998,
      }}>
        {DOCK_APPS.map(app => {
          const isOpen = wm.windows.some(w => w.id === app.id && !w.minimized);
          const isMin  = wm.windows.some(w => w.id === app.id && w.minimized);
          return (
            <div key={app.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={() => wm.open({ id: app.id, title: app.title, icon: app.icon, component: app.component, defaultSize: app.size })}
                title={app.title}
                style={{
                  width: '44px', height: '44px', borderRadius: '12px',
                  background: isOpen ? 'rgba(6,182,212,0.18)' : 'rgba(6,182,212,0.06)',
                  border: `1px solid ${isOpen ? 'rgba(6,182,212,0.4)' : 'rgba(6,182,212,0.15)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '18px', cursor: 'pointer',
                  transition: 'transform 0.15s ease, background 0.15s ease',
                  color: isOpen ? '#06b6d4' : 'rgba(6,182,212,0.4)',
                  boxShadow: isOpen ? '0 0 12px rgba(6,182,212,0.25)' : 'none',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(-10px) scale(1.2)';
                  (e.currentTarget as HTMLElement).style.background = 'rgba(6,182,212,0.22)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(0) scale(1)';
                  (e.currentTarget as HTMLElement).style.background = isOpen ? 'rgba(6,182,212,0.18)' : 'rgba(6,182,212,0.06)';
                }}
              >
                {app.icon}
              </button>
              <div style={{
                width: '4px', height: '4px', borderRadius: '50%',
                background: isOpen ? '#06b6d4' : isMin ? 'rgba(245,158,11,0.6)' : 'transparent',
                transition: 'background 0.2s ease',
              }} />
            </div>
          );
        })}
      </div>

      {/* Minimized tray */}
      <div style={{ position: 'absolute', bottom: '86px', right: '16px', display: 'flex', flexDirection: 'column', gap: '4px', zIndex: 9997 }}>
        {wm.windows.filter(w => w.minimized).map(w => (
          <button
            key={w.id}
            onClick={() => wm.open({ id: w.id, title: w.title, icon: w.icon, component: w.component })}
            style={{
              background: 'rgba(245,158,11,0.12)', border: '1px solid rgba(245,158,11,0.3)',
              borderRadius: '6px', padding: '2px 8px',
              fontSize: '9px', color: 'rgba(245,158,11,0.7)', cursor: 'pointer',
              letterSpacing: '0.1em', textTransform: 'uppercase',
            }}
          >
            {w.icon} {w.title}
          </button>
        ))}
      </div>

      <a href="/axiom-rayne/" style={{
        position: 'absolute', top: '4px', right: '80px',
        fontSize: '9px', color: 'rgba(255,255,255,0.15)',
        textDecoration: 'none', letterSpacing: '0.15em', lineHeight: '20px', zIndex: 10000,
      }}>← classic</a>
    </div>
  );
}
