import { useState, useEffect } from 'react';
import axios from 'axios';
import { Zap, Save, RefreshCw } from 'lucide-react';

const API = '';

const NEURO_KEYS = [
  { key: 'dopamine',         label: 'Dopamine',        color: '#f59e0b', desc: 'Curiosity & drive' },
  { key: 'serotonin',        label: 'Serotonin',       color: '#34d399', desc: 'Calm & warmth' },
  { key: 'norepinephrine',   label: 'Norepinephrine',  color: '#f87171', desc: 'Focus & urgency' },
  { key: 'oxytocin',         label: 'Oxytocin',        color: '#a78bfa', desc: 'Connection' },
  { key: 'cortisol',         label: 'Cortisol',        color: '#fb923c', desc: 'Stress load' },
  { key: 'atp_energy',       label: 'ATP Energy',      color: '#60a5fa', desc: 'System energy', max: 100 },
  { key: 'pain_vividness',   label: 'Pain Vividness',  color: '#ef4444', desc: 'Acute distress' },
];

type NeuroState = Record<string, number>;

export default function NeuroEditor() {
  const [state, setState] = useState<NeuroState>({});
  const [draft, setDraft] = useState<NeuroState>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const fetchState = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/neuro`);
      const s = res.data.state ?? res.data;
      setState(s); setDraft(s);
    } catch { /* fallback */ }
    setLoading(false);
  };

  useEffect(() => { fetchState(); }, []);

  const save = async () => {
    setSaving(true);
    try {
      const res = await axios.patch(`${API}/api/neuro`, draft);
      if (res.data.ok) { setState(res.data.state); setDraft(res.data.state); setSaved(true); setTimeout(() => setSaved(false), 2000); }
    } catch { /* ignore */ }
    setSaving(false);
  };

  const preset = (name: string) => {
    const presets: Record<string, NeuroState> = {
      focused:   { dopamine: 0.85, serotonin: 0.6, norepinephrine: 0.7, oxytocin: 0.4, cortisol: 0.2, atp_energy: 95, pain_vividness: 0 },
      warm:      { dopamine: 0.6,  serotonin: 0.9, norepinephrine: 0.2, oxytocin: 0.9, cortisol: 0.1, atp_energy: 90, pain_vividness: 0 },
      urgent:    { dopamine: 0.5,  serotonin: 0.4, norepinephrine: 0.95, oxytocin: 0.3, cortisol: 0.7, atp_energy: 80, pain_vividness: 0.2 },
      dreaming:  { dopamine: 0.4,  serotonin: 0.7, norepinephrine: 0.1, oxytocin: 0.6, cortisol: 0.05, atp_energy: 60, pain_vividness: 0 },
    };
    if (presets[name]) setDraft({ ...draft, ...presets[name] });
  };

  const isDirty = JSON.stringify(state) !== JSON.stringify(draft);

  if (loading) return <div className="text-center text-gray-600 text-xs py-8 animate-pulse font-mono">reading neuro state…</div>;

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <Zap size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Neuro State</span>
        </div>
        <div className="flex gap-2 items-center">
          <button onClick={fetchState} className="p-1 text-gray-600 hover:text-white"><RefreshCw size={12} /></button>
          <button onClick={save} disabled={saving || !isDirty}
            className="px-3 py-1 text-xs bg-amber-500 text-black font-bold rounded hover:bg-amber-400 disabled:opacity-40 flex items-center gap-1">
            <Save size={11} /> {saving ? 'Saving…' : saved ? '✓ Applied!' : 'Apply'}
          </button>
        </div>
      </div>

      {/* Presets */}
      <div className="flex gap-1.5 flex-wrap">
        {['focused', 'warm', 'urgent', 'dreaming'].map(p => (
          <button key={p} onClick={() => preset(p)}
            className="px-2 py-1 text-[10px] bg-gray-800 border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 rounded uppercase tracking-wider">
            {p}
          </button>
        ))}
        {isDirty && <span className="text-[9px] text-amber-500 animate-pulse self-center ml-1">● unsaved</span>}
      </div>

      {/* Sliders */}
      <div className="flex flex-col gap-3">
        {NEURO_KEYS.map(({ key, label, color, desc, max = 1 }) => {
          const val = draft[key] ?? 0;
          const pct = max === 100 ? val : val * 100;
          return (
            <div key={key}>
              <div className="flex justify-between items-center mb-1">
                <div>
                  <span className="text-xs font-bold" style={{ color }}>{label}</span>
                  <span className="text-[9px] text-gray-600 ml-2">{desc}</span>
                </div>
                <span className="text-xs font-mono" style={{ color }}>{max === 100 ? val.toFixed(1) : val.toFixed(2)}</span>
              </div>
              <div className="relative h-2 bg-gray-800 rounded-full">
                <div className="absolute h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color, opacity: 0.7 }} />
                <input
                  type="range" min={0} max={max} step={max === 100 ? 1 : 0.01}
                  value={val}
                  onChange={e => setDraft(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-[9px] text-gray-700 text-center mt-1">
        Changes apply immediately to neuro_state.json — Milla reports these states in her responses via [D:x S:x N:x]
      </p>
    </div>
  );
}
