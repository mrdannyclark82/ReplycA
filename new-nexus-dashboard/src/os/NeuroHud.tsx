import { useState, useEffect } from 'react';
import axios from 'axios';

interface NeuroState {
  dopamine: number;
  serotonin: number;
  cortisol: number;
  oxytocin: number;
  atp_energy: number;
}

const VITALS = [
  { key: 'dopamine',   label: 'DOP', prime: [0.4, 0.85] },
  { key: 'serotonin',  label: 'SER', prime: [0.5, 1.0]  },
  { key: 'cortisol',   label: 'COR', prime: [0.0, 0.45] }, // low is good for cortisol
  { key: 'oxytocin',   label: 'OXY', prime: [0.3, 1.0]  },
  { key: 'atp_energy', label: 'ATP', prime: [40, 100],  scale: 100 },
] as const;

function getColor(key: string, value: number): string {
  const v = key === 'atp_energy' ? value / 100 : value;
  if (key === 'cortisol') {
    if (v > 0.7) return '#f43f5e'; // danger
    if (v > 0.45) return '#f59e0b';
    return '#06b6d4';
  }
  if (v < 0.2) return '#f43f5e';
  if (v < 0.35) return '#f59e0b';
  const colors = ['#06b6d4', '#a855f7', '#2dd4bf'];
  return colors[['dopamine','serotonin','oxytocin','atp_energy'].indexOf(key) % 3];
}

export default function NeuroHud() {
  const [state, setState] = useState<NeuroState>({ dopamine: 0.5, serotonin: 0.5, cortisol: 0.2, oxytocin: 0.3, atp_energy: 100 });
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const load = () =>
      axios.get('/api/neuro').then(r => {
        const s = r.data.state ?? r.data;
        setState(prev => ({ ...prev, ...s }));
      }).catch(() => {});
    load();
    const id = setInterval(load, 6000);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      onClick={() => setExpanded(e => !e)}
      style={{
        position: 'absolute', top: '40px', right: '14px',
        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,255,255,0.07)', borderRadius: '10px',
        padding: expanded ? '8px 12px' : '6px 10px',
        cursor: 'pointer', zIndex: 900,
        transition: 'all 0.2s ease',
        minWidth: expanded ? '140px' : 'unset',
      }}
    >
      {expanded ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '8px', color: 'rgba(6,182,212,0.5)', letterSpacing: '0.25em', textTransform: 'uppercase', marginBottom: '2px' }}>
            Neural Vitals
          </div>
          {VITALS.map(v => {
            const raw = state[v.key as keyof NeuroState] as number;
            const pct = v.key === 'atp_energy' ? raw : raw * 100;
            const color = getColor(v.key, raw);
            return (
              <div key={v.key} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '6px', height: '6px', borderRadius: '50%',
                  background: color, boxShadow: `0 0 6px ${color}`,
                  flexShrink: 0,
                }} />
                <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.1em', width: '28px' }}>{v.label}</span>
                <div style={{ flex: 1, height: '2px', borderRadius: '1px', background: 'rgba(255,255,255,0.06)' }}>
                  <div style={{
                    height: '100%', borderRadius: '1px',
                    width: `${pct}%`, background: color,
                    boxShadow: `0 0 4px ${color}88`,
                    transition: 'width 1.2s ease-out',
                  }} />
                </div>
                <span style={{ fontSize: '9px', color, fontVariantNumeric: 'tabular-nums', width: '26px', textAlign: 'right' }}>
                  {pct.toFixed(0)}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        /* Collapsed: just 5 dots */
        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
          {VITALS.map(v => {
            const raw = state[v.key as keyof NeuroState] as number;
            const color = getColor(v.key, raw);
            return (
              <div key={v.key} style={{
                width: '7px', height: '7px', borderRadius: '50%',
                background: color, boxShadow: `0 0 5px ${color}`,
                transition: 'background 0.8s ease, box-shadow 0.8s ease',
              }} title={v.label} />
            );
          })}
        </div>
      )}
    </div>
  );
}
