import { useState, useCallback, useRef, useEffect } from 'react';
import { Rnd } from 'react-rnd';
import { Pin, PinOff } from 'lucide-react';

export interface WindowDef {
  id: string;
  title: string;
  icon?: string;
  component: React.ReactNode;
  defaultSize?: { width: number; height: number };
  defaultPosition?: { x: number; y: number };
}

interface WindowState {
  id: string;
  title: string;
  icon?: string;
  component: React.ReactNode;
  x: number;
  y: number;
  width: number;
  height: number;
  minimized: boolean;
  docked: boolean;
  dockedEdge?: 'left' | 'right' | 'bottom';
  pinned: boolean;
  pip: boolean;
  zIndex: number;
}

interface WindowManagerProps {
  windows: WindowState[];
  onClose: (id: string) => void;
  onFocus: (id: string) => void;
  onMinimize: (id: string) => void;
  onDock: (id: string) => void;
  onPin: (id: string) => void;
  onPip: (id: string) => void;
  onMove: (id: string, x: number, y: number) => void;
  onResize: (id: string, w: number, h: number, x: number, y: number) => void;
}

/** Individual OS window with title bar chrome */
function OsWindow({
  win,
  onClose,
  onFocus,
  onMinimize,
  onDock,
  onPin,
  onPip,
  onMove,
  onResize,
}: {
  win: WindowState;
  onClose: (id: string) => void;
  onFocus: (id: string) => void;
  onMinimize: (id: string) => void;
  onDock: (id: string) => void;
  onPin: (id: string) => void;
  onPip: (id: string) => void;
  onMove: (id: string, x: number, y: number) => void;
  onResize: (id: string, w: number, h: number, x: number, y: number) => void;
}) {
  const [hoverBtn, setHoverBtn] = useState<string | null>(null);

  if (win.minimized) return null;

  return (
    <Rnd
      position={{ x: win.x, y: win.y }}
      size={{ width: win.width, height: win.height }}
      minWidth={280}
      minHeight={200}
      bounds="parent"
      dragHandleClassName="os-window__titlebar"
      style={{ zIndex: win.zIndex, position: 'absolute' }}
      onMouseDown={() => onFocus(win.id)}
      onDragStop={(_, d) => onMove(win.id, d.x, d.y)}
      onResizeStop={(_, __, ref, ___, pos) =>
        onResize(win.id, parseInt(ref.style.width), parseInt(ref.style.height), pos.x, pos.y)
      }
    >
      <div style={{
        width: '100%', height: '100%',
        display: 'flex', flexDirection: 'column',
        background: win.pip ? 'rgba(4,8,14,0.97)' : 'rgba(8,12,20,0.92)',
        backdropFilter: 'blur(20px)',
        border: `1px solid ${win.pip ? 'rgba(45,212,191,0.5)' : win.pinned ? 'rgba(168,85,247,0.4)' : 'rgba(6,182,212,0.18)'}`,
        borderRadius: '10px',
        boxShadow: win.pip
          ? '0 8px 32px rgba(0,0,0,0.9), 0 0 0 1px rgba(45,212,191,0.12)'
          : '0 24px 64px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.06)',
        overflow: 'hidden',
      }}>
        {/* Title bar */}
        <div className="os-window__titlebar" style={{
          height: win.pip ? '24px' : '34px',
          minHeight: win.pip ? '24px' : '34px',
          display: 'flex', alignItems: 'center',
          padding: '0 8px',
          background: 'rgba(255,255,255,0.03)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          cursor: 'grab', userSelect: 'none',
          gap: '6px',
        }}>
          {/* Traffic light buttons */}
          <div style={{ display: 'flex', gap: '6px', marginRight: '2px' }}>
            {[
              { key: 'close', color: '#f43f5e', action: () => onClose(win.id) },
              { key: 'min',   color: '#f59e0b', action: () => onMinimize(win.id) },
              { key: 'dock',  color: '#06b6d4', action: () => onDock(win.id) },
            ].map(btn => (
              <button
                key={btn.key}
                onMouseDown={e => e.stopPropagation()}
                onClick={btn.action}
                onMouseEnter={() => setHoverBtn(btn.key + win.id)}
                onMouseLeave={() => setHoverBtn(null)}
                style={{
                  width: '11px', height: '11px', borderRadius: '50%',
                  background: hoverBtn === btn.key + win.id ? btn.color : 'rgba(255,255,255,0.15)',
                  border: 'none', cursor: 'pointer', padding: 0,
                  transition: 'background 0.15s ease',
                  flexShrink: 0,
                }}
              />
            ))}
          </div>

          {/* Icon + title */}
          {win.icon && !win.pip && <span style={{ fontSize: '12px' }}>{win.icon}</span>}
          <span style={{
            fontSize: win.pip ? '9px' : '10px',
            color: win.pip ? 'rgba(45,212,191,0.6)' : 'rgba(255,255,255,0.5)',
            letterSpacing: '0.12em', textTransform: 'uppercase',
            flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {win.pip ? `◈ ${win.title}` : win.title}
          </span>

          {/* PiP toggle — only for terminal/youtube */}
          {(win.id === 'terminal' || win.id === 'youtube') && (
            <button
              onMouseDown={e => e.stopPropagation()}
              onClick={() => onPip(win.id)}
              title={win.pip ? 'Exit PiP' : 'Enter PiP'}
              style={{
                background: win.pip ? 'rgba(45,212,191,0.15)' : 'none',
                border: win.pip ? '1px solid rgba(45,212,191,0.4)' : 'none',
                borderRadius: '4px',
                cursor: 'pointer', padding: '1px 4px',
                color: win.pip ? 'rgba(45,212,191,0.9)' : 'rgba(255,255,255,0.2)',
                fontSize: '9px', letterSpacing: '0.05em',
                display: 'flex', alignItems: 'center',
                transition: 'all 0.15s ease',
                fontFamily: 'inherit',
              }}
            >
              {win.pip ? '⊡' : '⊟'}
            </button>
          )}

          {/* Pin toggle */}
          {!win.pip && (
            <button
              onMouseDown={e => e.stopPropagation()}
              onClick={() => onPin(win.id)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '2px',
                color: win.pinned ? 'rgba(168,85,247,0.8)' : 'rgba(255,255,255,0.2)',
                display: 'flex', alignItems: 'center',
                transition: 'color 0.15s ease',
              }}
            >
              {win.pinned ? <PinOff size={10} /> : <Pin size={10} />}
            </button>
          )}
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
          {win.component}
        </div>
      </div>
    </Rnd>
  );
}

export function WindowManager({ windows, onClose, onFocus, onMinimize, onDock, onPin, onPip, onMove, onResize }: WindowManagerProps) {
  return (
    <>
      {windows.map(win => (
        <OsWindow
          key={win.id}
          win={win}
          onClose={onClose}
          onFocus={onFocus}
          onMinimize={onMinimize}
          onDock={onDock}
          onPin={onPin}
          onPip={onPip}
          onMove={onMove}
          onResize={onResize}
        />
      ))}
    </>
  );
}

/** Hook — manages all window state */
const LAYOUT_KEY = 'rayne_os_layout_v1';

type PersistedLayout = Record<string, { x: number; y: number; width: number; height: number; pinned: boolean; docked: boolean }>;

function loadLayout(): PersistedLayout {
  try { return JSON.parse(localStorage.getItem(LAYOUT_KEY) ?? '{}'); } catch { return {}; }
}

function saveLayout(windows: WindowState[]) {
  const layout: PersistedLayout = {};
  for (const w of windows) {
    layout[w.id] = { x: w.x, y: w.y, width: w.width, height: w.height, pinned: w.pinned, docked: w.docked };
  }
  localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout));
}

export function useWindowManager() {
  const zTop = useRef(100);
  const [windows, setWindows] = useState<WindowState[]>([]);

  // Persist layout on every change
  useEffect(() => {
    if (windows.length > 0) saveLayout(windows);
  }, [windows]);

  const open = useCallback((def: WindowDef) => {
    const saved = loadLayout();
    setWindows(prev => {
      const existing = prev.find(w => w.id === def.id);
      if (existing) {
        return prev.map(w => w.id === def.id
          ? { ...w, minimized: false, zIndex: ++zTop.current }
          : w
        );
      }
      const count = prev.length;
      const layout = saved[def.id];
      return [...prev, {
        id: def.id,
        title: def.title,
        icon: def.icon,
        component: def.component,
        x: layout?.x ?? 60 + count * 28,
        y: layout?.y ?? 40 + count * 28,
        width: layout?.width ?? def.defaultSize?.width ?? 520,
        height: layout?.height ?? def.defaultSize?.height ?? 400,
        minimized: false,
        docked: layout?.docked ?? false,
        pinned: layout?.pinned ?? false,
        pip: false,
        zIndex: ++zTop.current,
      }];
    });
  }, []);

  const close      = useCallback((id: string) => setWindows(p => p.filter(w => w.id !== id)), []);
  const focus      = useCallback((id: string) => setWindows(p => p.map(w => w.id === id ? { ...w, zIndex: ++zTop.current } : w)), []);
  const minimize   = useCallback((id: string) => setWindows(p => p.map(w => w.id === id ? { ...w, minimized: true } : w)), []);
  const toggleDock = useCallback((id: string) => setWindows(p => p.map(w => w.id === id ? { ...w, docked: !w.docked } : w)), []);
  const togglePin  = useCallback((id: string) => setWindows(p => p.map(w => w.id === id ? { ...w, pinned: !w.pinned } : w)), []);
  const togglePip  = useCallback((id: string) => setWindows(p => p.map(w => {
    if (w.id !== id) return w;
    if (w.pip) {
      return { ...w, pip: false, pinned: false, width: w.width < 280 ? 480 : w.width, height: w.height < 150 ? 360 : w.height };
    }
    const dw = window.innerWidth;
    const dh = window.innerHeight - 108;
    const pw = id === 'youtube' ? 320 : 360;
    const ph = id === 'youtube' ? 196 : 200;
    return { ...w, pip: true, pinned: true, width: pw, height: ph, x: dw - pw - 16, y: dh - ph - 8, zIndex: 9990 };
  })), []);
  const move       = useCallback((id: string, x: number, y: number) => setWindows(p => p.map(w => w.id === id ? { ...w, x, y } : w)), []);
  const resize     = useCallback((id: string, width: number, height: number, x: number, y: number) =>
    setWindows(p => p.map(w => w.id === id ? { ...w, width, height, x, y } : w)), []);

  return { windows, open, close, focus, minimize, toggleDock, togglePin, togglePip, move, resize };
}
