import { useState, useEffect } from 'react';
import axios from 'axios';
import { Check, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

interface CloudModel { id: string; name: string; tags: string[] }
interface LocalModel  { id: string; name: string }
interface ModelStatus { model: string; provider: string; cloud_host: string; cloud_configured: boolean }

const PROVIDER_INFO = {
  xai:          { label: 'xAI / Grok',       color: 'var(--amber)',  icon: '⚡', desc: 'Grok-4 cloud — primary' },
  ollama_cloud: { label: 'Ollama Cloud',      color: 'var(--cyan)',   icon: '☁', desc: 'Remote Ollama server' },
  ollama:       { label: 'Local Ollama',      color: 'var(--green)',  icon: '⬡', desc: 'On-device models' },
};

export default function ModelSwitcher() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [cloudModels, setCloudModels] = useState<CloudModel[]>([]);
  const [localModels, setLocalModels] = useState<LocalModel[]>([]);
  const [showCloud, setShowCloud] = useState(false);

  // Cloud config form
  const [cloudHost, setCloudHost] = useState('');
  const [cloudKey, setCloudKey]   = useState('');
  const [selectedCloudModel, setSelectedCloudModel] = useState('llama3.3:70b');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchStatus = () => {
    axios.get('/api/model').then(r => setStatus(r.data)).catch(() => {});
    axios.get('/api/model/cloud-models').then(r => setCloudModels(r.data.models || [])).catch(() => {});
    axios.get('/api/model/local-models').then(r => setLocalModels(r.data.models || [])).catch(() => {});
  };

  useEffect(() => { fetchStatus(); }, []);

  const switchProvider = async (provider: string, model?: string) => {
    setSaving(true); setMsg('');
    try {
      const r = await axios.post('/api/model/provider', {
        provider,
        host: provider === 'ollama_cloud' ? cloudHost : '',
        key: provider === 'ollama_cloud' ? cloudKey : '',
        model: model || (provider === 'ollama_cloud' ? selectedCloudModel : ''),
      });
      setStatus(prev => prev ? { ...prev, provider: r.data.provider, model: r.data.model } : prev);
      setMsg(`✓ Switched to ${r.data.provider} / ${r.data.model}`);
      fetchStatus();
    } catch (e: any) {
      setMsg('✗ ' + (e?.response?.data?.detail || e.message));
    }
    setSaving(false);
  };

  const switchModel = async (model: string) => {
    await axios.post('/api/model', { model });
    fetchStatus();
  };

  const providerColor = (p: string) => (PROVIDER_INFO as any)[p]?.color || 'var(--cyan)';

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto">

      {/* Current status */}
      {status && (
        <div className="glass rounded-lg px-3 py-2.5" style={{ border: `1px solid ${providerColor(status.provider)}40` }}>
          <p className="text-[8px] uppercase tracking-[0.4em] mb-1 opacity-40" style={{ color: 'var(--cyan)' }}>Active</p>
          <div className="flex items-center gap-2">
            <span className="text-base">{(PROVIDER_INFO as any)[status.provider]?.icon || '?'}</span>
            <div>
              <p className="text-[12px] font-bold" style={{ color: providerColor(status.provider) }}>
                {status.model}
              </p>
              <p className="text-[8px] opacity-50" style={{ color: 'var(--cyan)' }}>
                {(PROVIDER_INFO as any)[status.provider]?.label || status.provider}
                {status.cloud_configured && status.provider === 'ollama_cloud' && ` · ${status.cloud_host}`}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Provider selector */}
      <div className="flex flex-col gap-2">
        <p className="text-[9px] uppercase tracking-[0.4em] opacity-40" style={{ color: 'var(--cyan)' }}>Switch Provider</p>

        {Object.entries(PROVIDER_INFO).map(([id, info]) => (
          <div key={id}>
            <button
              onClick={() => { if (id !== 'ollama_cloud') switchProvider(id); else setShowCloud(c => !c); }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left"
              style={{
                background: status?.provider === id ? `color-mix(in srgb, ${info.color} 8%, transparent)` : 'rgba(255,255,255,0.02)',
                border: `1px solid ${status?.provider === id ? info.color + '50' : 'rgba(255,255,255,0.06)'}`,
              }}>
              <span className="text-sm">{info.icon}</span>
              <div className="flex-1">
                <p className="text-[11px] font-semibold" style={{ color: info.color }}>{info.label}</p>
                <p className="text-[8px] opacity-40" style={{ color: 'var(--cyan)' }}>{info.desc}</p>
              </div>
              {status?.provider === id && <Check size={11} style={{ color: info.color }} />}
              {id === 'ollama_cloud' && (
                showCloud ? <ChevronUp size={11} className="opacity-40" style={{ color: info.color }} />
                          : <ChevronDown size={11} className="opacity-40" style={{ color: info.color }} />
              )}
            </button>

            {/* Ollama Cloud config panel */}
            {id === 'ollama_cloud' && showCloud && (
              <div className="mt-1 rounded-lg p-3 flex flex-col gap-2"
                style={{ background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>

                <div className="flex items-center gap-2 text-[9px] opacity-60 mb-1" style={{ color: 'var(--cyan)' }}>
                  <ExternalLink size={9} />
                  <span>Get a key at <strong>ollama.com</strong> or use any remote Ollama server</span>
                </div>

                <input value={cloudHost} onChange={e => setCloudHost(e.target.value)}
                  placeholder="Host URL — e.g. https://api.ollama.com"
                  className="w-full px-2 py-1.5 rounded text-[10px] font-mono bg-transparent border"
                  style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.3)', outline: 'none' }} />

                <input value={cloudKey} onChange={e => setCloudKey(e.target.value)}
                  type="password"
                  placeholder="API key (if required)"
                  className="w-full px-2 py-1.5 rounded text-[10px] font-mono bg-transparent border"
                  style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.3)', outline: 'none' }} />

                {/* Model picker */}
                <div className="flex flex-col gap-1 max-h-40 overflow-y-auto">
                  {cloudModels.map(m => (
                    <button key={m.id} onClick={() => setSelectedCloudModel(m.id)}
                      className="flex items-center gap-2 px-2 py-1 rounded text-left"
                      style={{
                        background: selectedCloudModel === m.id ? 'rgba(6,182,212,0.08)' : 'transparent',
                        border: `1px solid ${selectedCloudModel === m.id ? 'rgba(6,182,212,0.4)' : 'rgba(6,182,212,0.1)'}`,
                      }}>
                      <span className="text-[10px] flex-1" style={{ color: 'var(--cyan)' }}>{m.name}</span>
                      <div className="flex gap-1">
                        {m.tags.map(t => (
                          <span key={t} className="text-[7px] px-1 rounded opacity-50"
                            style={{ background: 'rgba(6,182,212,0.15)', color: 'var(--cyan)' }}>
                            {t}
                          </span>
                        ))}
                      </div>
                      {selectedCloudModel === m.id && <Check size={9} style={{ color: 'var(--cyan)' }} />}
                    </button>
                  ))}
                </div>

                <button onClick={() => switchProvider('ollama_cloud', selectedCloudModel)}
                  disabled={saving || !cloudHost}
                  className="px-3 py-1.5 rounded border text-[10px] uppercase tracking-widest font-bold"
                  style={{
                    color: cloudHost ? 'var(--cyan)' : 'rgba(6,182,212,0.3)',
                    borderColor: cloudHost ? 'rgba(6,182,212,0.4)' : 'rgba(6,182,212,0.15)',
                  }}>
                  {saving ? 'Connecting...' : 'Connect & Use Cloud'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Local model list */}
      {localModels.length > 0 && (
        <div>
          <p className="text-[9px] uppercase tracking-[0.4em] opacity-40 mb-2" style={{ color: 'var(--green)' }}>
            Local Models
          </p>
          <div className="flex flex-col gap-1">
            {localModels.map(m => (
              <button key={m.id} onClick={() => { switchProvider('ollama'); switchModel(m.id); }}
                className="flex items-center gap-2 px-2 py-1.5 rounded text-left"
                style={{
                  background: status?.model === m.id ? 'rgba(34,197,94,0.06)' : 'transparent',
                  border: `1px solid ${status?.model === m.id ? 'rgba(34,197,94,0.35)' : 'rgba(34,197,94,0.1)'}`,
                }}>
                <span className="text-[10px] flex-1 font-mono" style={{ color: 'var(--green)' }}>{m.name}</span>
                {status?.model === m.id && <Check size={9} style={{ color: 'var(--green)' }} />}
              </button>
            ))}
          </div>
        </div>
      )}

      {msg && (
        <p className="text-[9px] font-mono px-1" style={{ color: msg.startsWith('✓') ? 'var(--green)' : '#ef4444' }}>
          {msg}
        </p>
      )}
    </div>
  );
}
