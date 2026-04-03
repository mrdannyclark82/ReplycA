import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Brain, Zap, Droplets, Globe, Eye } from 'lucide-react';

const METERS = [
  { key: 'dopamine',       label: 'Dopamine',       icon: Zap,      hex: '#f59e0b' },
  { key: 'serotonin',      label: 'Serotonin',      icon: Droplets, hex: '#06b6d4' },
  { key: 'norepinephrine', label: 'Norepinephrine', icon: Brain,    hex: '#f43f5e' },
];

const HUD: React.FC = () => {
  const [data, setData] = useState<Record<string,any>>({
    dopamine: 0.5, serotonin: 0.5, norepinephrine: 0.2,
    sense: 'synesthetic', google_auth: false, atp_energy: 100,
  });

  useEffect(() => {
    const fetch = () => axios.get('/api/neuro').then(r => setData(prev => ({ ...prev, ...(r.data.state ?? r.data) }))).catch(() => {});
    fetch();
    const id = setInterval(fetch, 5000);
    return () => clearInterval(id);
  }, []);

  const toggleSense = async () => {
    const next = data.sense === 'synesthetic' ? 'optical' : 'synesthetic';
    try { await axios.post('/api/sense', { sense: next }); setData(d => ({ ...d, sense: next })); } catch (_) {}
  };

  const handleGoogleLogin = async () => {
    try { const r = await axios.get('/api/oauth/login'); window.location.href = r.data.url; } catch (_) {}
  };

  const Meter = ({ label, value, icon: Icon, hex }: { label: string; value: number; icon: any; hex: string }) => (
    <div className="space-y-1.5">
      <div className="flex justify-between text-[10px] font-mono">
        <div className="flex items-center gap-1.5 opacity-60">
          <Icon size={11} style={{ color: hex }} />
          <span className="uppercase tracking-wider">{label}</span>
        </div>
        <span className="font-bold" style={{ color: hex, textShadow: `0 0 8px ${hex}88` }}>
          {(value * 100).toFixed(0)}
        </span>
      </div>
      {/* Track */}
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${value * 100}%`,
            background: `linear-gradient(90deg, ${hex}66, ${hex})`,
            boxShadow: `0 0 8px ${hex}99`,
            transition: 'width 1s ease-out',
          }}
        />
      </div>
    </div>
  );

  const atpPct = typeof data.atp_energy === 'number' ? data.atp_energy : 100;

  return (
    <div className="glass glass-cyan cyber-corners rounded-lg overflow-hidden">
      {/* Header */}
      <div className="panel-header px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={13} style={{ color: 'var(--cyan)' }} />
          <span className="text-[10px] font-bold tracking-[0.25em] uppercase neon-cyan">Neural Vitals</span>
        </div>
        <div
          className="text-[9px] font-mono px-2 py-0.5 rounded"
          style={{
            color: data.google_auth ? 'var(--green)' : '#f43f5e',
            border: `1px solid ${data.google_auth ? 'rgba(34,197,94,0.4)' : 'rgba(244,63,94,0.4)'}`,
            background: data.google_auth ? 'rgba(34,197,94,0.07)' : 'rgba(244,63,94,0.07)',
          }}
        >
          G-SYNC: {data.google_auth ? 'READY' : 'OFF'}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Meters */}
        {METERS.map(m => (
          <Meter key={m.key} label={m.label} value={data[m.key] ?? 0} icon={m.icon} hex={m.hex} />
        ))}

        {/* ATP Energy bar */}
        <div className="pt-1 space-y-1.5">
          <div className="flex justify-between text-[10px] font-mono opacity-50">
            <span className="uppercase tracking-wider">ATP Energy</span>
            <span>{atpPct}%</span>
          </div>
          <div className="h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${atpPct}%`,
                background: atpPct > 60 ? 'linear-gradient(90deg,#06b6d466,#06b6d4)' : 'linear-gradient(90deg,#f43f5e66,#f43f5e)',
                transition: 'width 1s ease-out',
              }}
            />
          </div>
        </div>

        {/* Controls */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={toggleSense}
            className="cyber-btn rounded px-2 py-2 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5"
            style={data.sense === 'optical' ? { color: 'var(--purple)', borderColor: 'rgba(168,85,247,0.4)', background: 'rgba(168,85,247,0.08)' } : {}}
          >
            {data.sense === 'synesthetic' ? <Brain size={11} /> : <Eye size={11} />}
            {data.sense.slice(0,5)}
          </button>

          {!data.google_auth && (
            <button onClick={handleGoogleLogin} className="cyber-btn rounded px-2 py-2 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5">
              <Globe size={11} />
              G-Sync
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="pt-2 border-t text-[9px] font-mono opacity-25 text-center uppercase tracking-[0.3em]"
          style={{ borderColor: 'rgba(6,182,212,0.12)', color: 'var(--cyan)' }}>
          Forever Morth · Stable
        </div>
      </div>
    </div>
  );
};

export default HUD;
