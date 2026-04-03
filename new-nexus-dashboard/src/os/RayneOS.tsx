import { Shield } from 'lucide-react';
import { WindowManager, useWindowManager, type WindowDef } from './WindowManager';
import NeuroHud from './NeuroHud';
import DesktopCanvas from './DesktopCanvas';
import CommandPalette, { type PaletteCommand } from './CommandPalette';
import AppsMenu, { ALL_APPS } from './AppsMenu';

const DOCK_APPS = ALL_APPS.filter(a => a.dockDefault);

export default function RayneOS() {
  const wm = useWindowManager();

  const paletteCommands: PaletteCommand[] = [
    ...ALL_APPS.map(app => ({
      id: `open-${app.id}`,
      label: `Open ${app.title}`,
      icon: app.icon,
      description: app.category,
      keywords: [app.id, 'open', 'launch', app.category],
      action: () => wm.open(app as WindowDef),
    })),
    ...wm.windows.filter(w => !w.minimized).map(w => ({
      id: `close-${w.id}`,
      label: `Close ${w.title}`,
      icon: '✕',
      keywords: ['close', 'dismiss', w.id],
      action: () => wm.close(w.id),
    })),
    {
      id: 'close-all', label: 'Close All Windows', icon: '⊠',
      keywords: ['close', 'all', 'clear'],
      action: () => [...wm.windows].forEach(w => wm.close(w.id)),
    },
    {
      id: 'classic', label: 'Switch to Classic Mode', icon: '←',
      keywords: ['classic', 'back', 'axiom'],
      action: () => { window.location.href = '/axiom-rayne/'; },
    },
  ];

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
        <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <kbd style={{ fontSize: '8px', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '3px', padding: '1px 4px', fontFamily: 'inherit' }}>⌃K</kbd>
          palette
        </span>
        {wm.windows.filter(w => !w.minimized).length > 0 && (
          <span style={{ fontSize: '9px', color: 'rgba(6,182,212,0.4)', letterSpacing: '0.1em', marginLeft: '8px' }}>
            {wm.windows.filter(w => !w.minimized).length} open
          </span>
        )}
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginLeft: '8px' }}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Desktop */}
      <div id="rayne-desktop" style={{ position: 'absolute', top: '28px', left: 0, right: 0, bottom: '80px' }}>
        <DesktopCanvas hasWindows={wm.windows.length > 0} />
        <WindowManager
          windows={wm.windows}
          onClose={wm.close} onFocus={wm.focus} onMinimize={wm.minimize}
          onDock={wm.toggleDock} onPin={wm.togglePin} onPip={wm.togglePip} onMove={wm.move} onResize={wm.resize}
        />
        <NeuroHud />
      </div>

      {/* Cairo dock */}
      <div style={{
        position: 'absolute', bottom: '12px', left: '50%', transform: 'translateX(-50%)',
        display: 'flex', alignItems: 'flex-end', gap: '6px',
        padding: '10px 16px 8px',
        background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(24px)',
        borderRadius: '20px', border: '1px solid rgba(255,255,255,0.07)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.05)',
        zIndex: 9998,
      }}>
        {/* Reflection line */}
        <div style={{
          position: 'absolute', bottom: 0, left: '10%', right: '10%', height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(6,182,212,0.12), transparent)',
        }} />

        {/* Dock app icons */}
        {DOCK_APPS.map(app => {
          const isOpen = wm.windows.some(w => w.id === app.id && !w.minimized);
          const isMin  = wm.windows.some(w => w.id === app.id && w.minimized);
          return (
            <div key={app.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              <button
                onClick={() => wm.open(app as WindowDef)}
                title={app.title}
                style={{
                  width: '44px', height: '44px', borderRadius: '12px',
                  background: isOpen ? 'rgba(6,182,212,0.15)' : 'rgba(6,182,212,0.05)',
                  border: `1px solid ${isOpen ? 'rgba(6,182,212,0.35)' : 'rgba(6,182,212,0.12)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '18px', cursor: 'pointer',
                  transition: 'transform 0.15s cubic-bezier(.34,1.56,.64,1), background 0.15s ease',
                  color: isOpen ? '#06b6d4' : 'rgba(6,182,212,0.35)',
                  boxShadow: isOpen ? '0 0 14px rgba(6,182,212,0.2)' : 'none',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(-12px) scale(1.22)';
                  (e.currentTarget as HTMLElement).style.background = 'rgba(6,182,212,0.2)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.transform = 'translateY(0) scale(1)';
                  (e.currentTarget as HTMLElement).style.background = isOpen ? 'rgba(6,182,212,0.15)' : 'rgba(6,182,212,0.05)';
                }}
              >
                {app.icon}
              </button>
              <div style={{
                width: '4px', height: '4px', borderRadius: '50%',
                background: isOpen ? '#06b6d4' : isMin ? 'rgba(245,158,11,0.6)' : 'transparent',
                boxShadow: isOpen ? '0 0 4px #06b6d4' : 'none',
                transition: 'all 0.2s ease',
              }} />
            </div>
          );
        })}

        {/* Divider */}
        <div style={{ width: '1px', height: '32px', background: 'rgba(255,255,255,0.08)', margin: '0 4px', alignSelf: 'center' }} />

        {/* Apps menu button */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
          <AppsMenu onOpen={wm.open} />
          <div style={{ width: '4px', height: '4px', borderRadius: '50%' }} />
        </div>
      </div>

      {/* Minimized tray */}
      <div style={{ position: 'absolute', bottom: '86px', right: '16px', display: 'flex', flexDirection: 'column', gap: '4px', zIndex: 9997 }}>
        {wm.windows.filter(w => w.minimized).map(w => (
          <button key={w.id}
            onClick={() => wm.open({ id: w.id, title: w.title, icon: w.icon, component: w.component })}
            style={{
              background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)',
              borderRadius: '6px', padding: '3px 9px', fontSize: '9px',
              color: 'rgba(245,158,11,0.6)', cursor: 'pointer',
              letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'inherit',
            }}
          >{w.icon} {w.title}</button>
        ))}
      </div>

      <a href="/axiom-rayne/" style={{
        position: 'absolute', top: '4px', right: '80px',
        fontSize: '9px', color: 'rgba(255,255,255,0.12)',
        textDecoration: 'none', letterSpacing: '0.15em', lineHeight: '20px', zIndex: 10000,
      }}>← classic</a>

      <CommandPalette commands={paletteCommands} />
    </div>
  );
}
