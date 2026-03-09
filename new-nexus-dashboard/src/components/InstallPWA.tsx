import { useState, useEffect } from 'react';
import { X, Smartphone } from 'lucide-react';

declare global {
  interface Window {
    __pwaInstallPrompt: any;
  }
}

type Mode = 'native' | 'manual-android' | 'manual-ios' | 'hidden';

function detectMode(): Mode {
  // Already installed
  if (window.matchMedia('(display-mode: standalone)').matches) return 'hidden';
  // Native prompt available (HTTPS + Chrome/Edge)
  if (window.__pwaInstallPrompt) return 'native';
  const ua = navigator.userAgent;
  if (/iPhone|iPad|iPod/.test(ua)) return 'manual-ios';
  if (/Android/.test(ua)) return 'manual-android';
  return 'hidden';
}

export default function InstallPWA() {
  const [mode, setMode] = useState<Mode>('hidden');
  const [showGuide, setShowGuide] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check immediately (prompt may already be captured globally)
    setMode(detectMode());
    // Also listen for the custom event fired when prompt arrives later
    const onReady = () => setMode(detectMode());
    window.addEventListener('pwaInstallReady', onReady);
    return () => window.removeEventListener('pwaInstallReady', onReady);
  }, []);

  if (dismissed || mode === 'hidden') return null;

  const installNative = async () => {
    const p = window.__pwaInstallPrompt;
    if (!p) return;
    await p.prompt();
    const { outcome } = await p.userChoice;
    if (outcome === 'accepted') { window.__pwaInstallPrompt = null; setMode('hidden'); }
    else setDismissed(true);
  };

  return (
    <div className="glass glass-amber cyber-corners rounded-lg px-3 py-2 flex items-center gap-3" style={{ flexShrink: 0 }}>
      <Smartphone size={12} style={{ color: 'var(--amber)', flexShrink: 0 }} />
      <div className="flex-1 min-w-0 hidden sm:block">
        <p className="text-[9px] uppercase tracking-[0.3em] neon-amber">Install App</p>
        <p className="text-[8px] opacity-40 truncate" style={{ color: 'var(--cyan)' }}>Add to home screen</p>
      </div>

      {mode === 'native' ? (
        <button onClick={installNative}
          className="text-[9px] px-2 py-1 rounded border uppercase tracking-widest font-bold whitespace-nowrap"
          style={{ color: 'var(--amber)', borderColor: 'rgba(245,158,11,0.4)' }}>
          Install ↓
        </button>
      ) : (
        <button onClick={() => setShowGuide(g => !g)}
          className="text-[9px] px-2 py-1 rounded border uppercase tracking-widest font-bold whitespace-nowrap"
          style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.4)' }}>
          How?
        </button>
      )}

      <button onClick={() => setDismissed(true)} className="opacity-30 hover:opacity-70 ml-1">
        <X size={10} style={{ color: 'var(--cyan)' }} />
      </button>

      {/* Manual guide popup */}
      {showGuide && (
        <div className="absolute top-16 right-4 z-50 glass glass-amber rounded-lg p-4 text-left w-72"
             style={{ border: '1px solid rgba(245,158,11,0.3)' }}>
          <p className="text-[10px] neon-amber uppercase tracking-[0.3em] mb-3">
            {mode === 'manual-ios' ? '⊕ iOS Install Guide' : '⊕ Android Install Guide'}
          </p>
          {mode === 'manual-ios' ? (
            <ol className="text-[10px] opacity-70 space-y-2 list-none" style={{ color: 'var(--cyan)' }}>
              <li>1. Open <span className="neon-amber">Safari</span> (must be Safari)</li>
              <li>2. Tap the <span className="neon-amber">Share ⎋</span> button</li>
              <li>3. Scroll down → <span className="neon-amber">"Add to Home Screen"</span></li>
              <li>4. Tap <span className="neon-amber">Add</span></li>
            </ol>
          ) : (
            <ol className="text-[10px] opacity-70 space-y-2 list-none" style={{ color: 'var(--cyan)' }}>
              <li>1. Open <span className="neon-amber">Chrome</span> browser</li>
              <li>2. Tap <span className="neon-amber">⋮ Menu</span> (top right)</li>
              <li>3. Tap <span className="neon-amber">"Add to Home screen"</span></li>
              <li>4. Confirm — icon appears on home screen</li>
              <li style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(245,158,11,0.2)' }}>
                ⚠ Use <span className="neon-amber">https://</span> URL for native install banner
              </li>
            </ol>
          )}
          <button onClick={() => setShowGuide(false)} className="mt-3 text-[9px] opacity-40 hover:opacity-80 uppercase tracking-widest">
            Close ✕
          </button>
        </div>
      )}
    </div>
  );
}
