import { useState } from 'react';
import { Shield } from 'lucide-react';

/**
 * RayneOS — sandbox shell (/?os=1)
 * Window manager, Cairo dock, and desktop canvas live here.
 * Panels from AxiomClassic are dropped in as windows progressively.
 */

export default function RayneOS() {
  const [_ready] = useState(true);

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'radial-gradient(ellipse at 60% 40%, #0d1117 0%, #050709 100%)',
      overflow: 'hidden',
      fontFamily: "'JetBrains Mono', monospace",
    }}>
      {/* Desktop grid overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(rgba(6,182,212,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(6,182,212,0.03) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        pointerEvents: 'none',
      }} />

      {/* Top status bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        height: '28px',
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(6,182,212,0.12)',
        display: 'flex', alignItems: 'center',
        padding: '0 16px', gap: '8px',
        zIndex: 9999,
      }}>
        <Shield size={11} style={{ color: 'var(--cyan, #06b6d4)' }} />
        <span style={{ fontSize: '10px', color: 'rgba(6,182,212,0.7)', letterSpacing: '0.2em', textTransform: 'uppercase' }}>
          Rayne OS
        </span>
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', letterSpacing: '0.1em', marginLeft: '4px' }}>
          · sandbox
        </span>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)', letterSpacing: '0.05em' }}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Desktop workspace — windows mount here */}
      <div id="rayne-desktop" style={{
        position: 'absolute',
        top: '28px',
        left: 0, right: 0,
        bottom: '80px',
      }}>
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -60%)',
          textAlign: 'center', pointerEvents: 'none',
        }}>
          <div style={{ fontSize: '11px', color: 'rgba(6,182,212,0.25)', letterSpacing: '0.4em', textTransform: 'uppercase', marginBottom: '8px' }}>
            Rayne OS
          </div>
          <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.1)', letterSpacing: '0.2em' }}>
            Window manager loading
          </div>
        </div>
      </div>

      {/* Cairo dock placeholder */}
      <div style={{
        position: 'absolute', bottom: '12px',
        left: '50%', transform: 'translateX(-50%)',
        display: 'flex', alignItems: 'flex-end', gap: '6px',
        padding: '10px 20px 8px',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(20px)',
        borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
        zIndex: 9998,
      }}>
        {['⬡','⬡','⬡','⬡','⬡'].map((icon, i) => (
          <div key={i} style={{
            width: '44px', height: '44px',
            borderRadius: '12px',
            background: 'rgba(6,182,212,0.08)',
            border: '1px solid rgba(6,182,212,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '18px', color: 'rgba(6,182,212,0.3)',
            cursor: 'pointer',
            transition: 'transform 0.15s ease, background 0.15s ease',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.transform = 'translateY(-8px) scale(1.15)';
            (e.currentTarget as HTMLElement).style.background = 'rgba(6,182,212,0.18)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.transform = 'translateY(0) scale(1)';
            (e.currentTarget as HTMLElement).style.background = 'rgba(6,182,212,0.08)';
          }}>
            {icon}
          </div>
        ))}
      </div>

      {/* Back to Classic */}
      <a href="/axiom-rayne/" style={{
        position: 'absolute', top: '4px', right: '80px',
        fontSize: '9px', color: 'rgba(255,255,255,0.2)',
        textDecoration: 'none', letterSpacing: '0.15em',
        lineHeight: '20px',
        zIndex: 10000,
      }}>
        ← classic
      </a>
    </div>
  );
}
