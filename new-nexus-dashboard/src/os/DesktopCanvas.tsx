import { useEffect, useRef } from 'react';

const CUBE_CSS = `
@keyframes rayne-cube-spin {
  0%   { transform: rotateX(0deg)   rotateY(0deg)   rotateZ(0deg); }
  33%  { transform: rotateX(120deg) rotateY(180deg) rotateZ(60deg); }
  66%  { transform: rotateX(240deg) rotateY(300deg) rotateZ(120deg); }
  100% { transform: rotateX(360deg) rotateY(360deg) rotateZ(360deg); }
}
@keyframes rayne-cube-glow {
  0%, 100% { opacity: 0.12; }
  50%       { opacity: 0.22; }
}
@keyframes rayne-particle-drift {
  0%   { transform: translateY(0px)   translateX(0px);   opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.6; }
  100% { transform: translateY(-80px) translateX(20px);  opacity: 0; }
}
.rayne-cube-scene {
  width: 100px; height: 100px;
  perspective: 400px;
}
.rayne-cube {
  width: 100%; height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: rayne-cube-spin 18s cubic-bezier(0.4,0,0.6,1) infinite;
}
.rayne-cube-face {
  position: absolute;
  width: 100px; height: 100px;
  border: 1px solid rgba(6,182,212,0.25);
  background: rgba(6,182,212,0.03);
  backdrop-filter: blur(2px);
  animation: rayne-cube-glow 4s ease-in-out infinite;
}
.rayne-cube-face::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(6,182,212,0.08) 0%, transparent 60%);
}
.rayne-cube-face.f  { transform: rotateY(0deg)   translateZ(50px); }
.rayne-cube-face.b  { transform: rotateY(180deg) translateZ(50px); }
.rayne-cube-face.l  { transform: rotateY(-90deg) translateZ(50px); }
.rayne-cube-face.r  { transform: rotateY(90deg)  translateZ(50px); }
.rayne-cube-face.t  { transform: rotateX(90deg)  translateZ(50px); animation-delay: 0.5s; }
.rayne-cube-face.bt { transform: rotateX(-90deg) translateZ(50px); animation-delay: 1s; }
`;

function injectStyles() {
  if (document.getElementById('rayne-cube-styles')) return;
  const el = document.createElement('style');
  el.id = 'rayne-cube-styles';
  el.textContent = CUBE_CSS;
  document.head.appendChild(el);
}

interface Particle { x: number; y: number; size: number; delay: number; duration: number; color: string; }

const COLORS = ['rgba(6,182,212,0.6)', 'rgba(168,85,247,0.5)', 'rgba(45,212,191,0.5)', 'rgba(6,182,212,0.3)'];

function makeParticles(count: number): Particle[] {
  return Array.from({ length: count }, () => ({
    x: Math.random() * 100,
    y: 30 + Math.random() * 70,
    size: 1 + Math.random() * 2,
    delay: Math.random() * 8,
    duration: 5 + Math.random() * 8,
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
  }));
}

interface Props {
  hasWindows: boolean;
}

export default function DesktopCanvas({ hasWindows }: Props) {
  const particlesRef = useRef<Particle[]>(makeParticles(24));

  useEffect(() => { injectStyles(); }, []);

  return (
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden',
      opacity: hasWindows ? 0.4 : 1,
      transition: 'opacity 0.8s ease',
    }}>
      {/* Ambient corner glow */}
      <div style={{
        position: 'absolute', top: '-80px', left: '-80px',
        width: '320px', height: '320px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)',
      }} />
      <div style={{
        position: 'absolute', bottom: '-60px', right: '-60px',
        width: '280px', height: '280px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%)',
      }} />

      {/* Floating particles */}
      {particlesRef.current.map((p, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: `${p.x}%`, top: `${p.y}%`,
          width: `${p.size}px`, height: `${p.size}px`,
          borderRadius: '50%', background: p.color,
          boxShadow: `0 0 ${p.size * 3}px ${p.color}`,
          animation: `rayne-particle-drift ${p.duration}s ease-in-out ${p.delay}s infinite`,
        }} />
      ))}

      {/* Spinning cube — centered, only prominent when desktop is empty */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -60%)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px',
      }}>
        <div className="rayne-cube-scene">
          <div className="rayne-cube">
            <div className="rayne-cube-face f" />
            <div className="rayne-cube-face b" />
            <div className="rayne-cube-face l" />
            <div className="rayne-cube-face r" />
            <div className="rayne-cube-face t" />
            <div className="rayne-cube-face bt" />
          </div>
        </div>

        {!hasWindows && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: 'rgba(6,182,212,0.25)', letterSpacing: '0.4em', textTransform: 'uppercase' }}>
              Rayne OS
            </div>
            <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.1)', letterSpacing: '0.2em', marginTop: '4px' }}>
              click icon or <span style={{ color: 'rgba(6,182,212,0.3)' }}>⌃K</span> to open
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
