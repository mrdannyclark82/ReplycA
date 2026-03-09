import { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Save, RotateCcw, Edit3, CheckCircle, AlertCircle } from 'lucide-react';

const API = '';

export default function PersonaEditor() {
  const [prompt, setPrompt] = useState('');
  const [original, setOriginal] = useState('');
  const [isOverride, setIsOverride] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [editing, setEditing] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/persona`);
      setPrompt(res.data.prompt || '');
      setOriginal(res.data.prompt || '');
      setIsOverride(res.data.is_override || false);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const save = async () => {
    setSaving(true);
    setStatus(null);
    try {
      await axios.post(`${API}/api/persona`, { prompt });
      setOriginal(prompt);
      setIsOverride(true);
      setEditing(false);
      setStatus({ type: 'success', msg: 'Persona updated — Milla will use this on next response.' });
    } catch (e: any) {
      setStatus({ type: 'error', msg: e.message });
    }
    setSaving(false);
  };

  const reset = async () => {
    if (!confirm('Reset to default Milla persona? Your override will be deleted.')) return;
    try {
      await axios.delete(`${API}/api/persona`);
      setIsOverride(false);
      setEditing(false);
      setStatus({ type: 'success', msg: 'Reset to default persona.' });
      load();
    } catch (e: any) {
      setStatus({ type: 'error', msg: e.message });
    }
  };

  const isDirty = prompt !== original;

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <User size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Persona Core</span>
          {isOverride && <span className="text-[9px] px-1.5 py-0.5 bg-amber-400/20 border border-amber-400/30 text-amber-400 rounded">OVERRIDE ACTIVE</span>}
        </div>
        <div className="flex gap-2">
          {!editing && (
            <button onClick={() => setEditing(true)} className="px-2 py-1 text-xs bg-gray-800 border border-gray-600 text-gray-300 hover:text-white rounded flex items-center gap-1">
              <Edit3 size={11} /> Edit
            </button>
          )}
          {isOverride && (
            <button onClick={reset} className="px-2 py-1 text-xs bg-red-400/10 border border-red-400/30 text-red-400 hover:bg-red-400/20 rounded flex items-center gap-1">
              <RotateCcw size={11} /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Status */}
      {status && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded text-xs border ${
          status.type === 'success' ? 'bg-green-400/10 border-green-400/30 text-green-400' : 'bg-red-400/10 border-red-400/30 text-red-400'
        }`}>
          {status.type === 'success' ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
          {status.msg}
        </div>
      )}

      {/* Prompt display/editor */}
      {loading ? (
        <div className="text-center text-gray-600 text-xs py-8 animate-pulse">loading persona…</div>
      ) : editing ? (
        <>
          <div className="text-[10px] text-gray-500 px-1">Editing system prompt — this shapes Milla's entire identity and behavior.</div>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            className="w-full bg-black border border-amber-400/40 rounded p-3 text-xs text-gray-200 leading-relaxed resize-none focus:border-amber-400 outline-none"
            style={{ minHeight: '420px', fontFamily: 'monospace' }}
          />
          <div className="flex gap-2 items-center">
            <button
              onClick={save}
              disabled={saving || !isDirty}
              className="px-4 py-2 text-xs bg-amber-500 text-black font-bold rounded hover:bg-amber-400 disabled:opacity-40 flex items-center gap-1"
            >
              <Save size={12} /> {saving ? 'Saving…' : 'Save & Apply'}
            </button>
            <button onClick={() => { setPrompt(original); setEditing(false); setStatus(null); }} className="px-3 py-2 text-xs text-gray-500 hover:text-white">
              Cancel
            </button>
            {isDirty && <span className="text-[9px] text-amber-500 animate-pulse ml-auto">● unsaved changes</span>}
          </div>
        </>
      ) : (
        <div className="bg-black/50 border border-gray-800 rounded p-3 max-h-[480px] overflow-y-auto">
          <pre className="text-[11px] text-gray-300 whitespace-pre-wrap leading-relaxed">{prompt}</pre>
        </div>
      )}

      <p className="text-[9px] text-gray-700 text-center px-2">
        Changes apply to the next conversation turn. The override is saved to disk and persists across restarts. Reset restores the compiled-in default.
      </p>
    </div>
  );
}
