import { useState } from 'react';
import axios from 'axios';
import { Tv, Search, Volume2, Youtube } from 'lucide-react';

export default function CastControl() {
  const [devices, setDevices] = useState<string[]>([]);
  const [scanning, setScanning] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [deviceIp, setDeviceIp] = useState('');
  const [videoId, setVideoId] = useState('');
  const [volume, setVolume] = useState(0.5);
  const [status, setStatus] = useState('');
  const [castAvailable, setCastAvailable] = useState(true);

  const scan = async () => {
    setScanning(true);
    setStatus('Scanning...');
    try {
      const r = await axios.get('/api/cast/discover');
      if (!r.data.ok) { setCastAvailable(false); setStatus(r.data.error); return; }
      setDevices(r.data.devices || []);
      setStatus(r.data.devices?.length ? `Found ${r.data.devices.length} device(s)` : 'No devices found');
    } catch (e) {
      setStatus('Scan failed');
    }
    setScanning(false);
  };

  const playYouTube = async () => {
    if (!videoId.trim()) return;
    setStatus('Casting...');
    try {
      const r = await axios.post('/api/cast/youtube', { video_id: videoId, device_name: selectedDevice, ip: deviceIp });
      setStatus(r.data.ok ? `▶ Playing ${videoId}` : r.data.error);
    } catch { setStatus('Cast failed'); }
  };

  const setVol = async () => {
    setStatus('Setting volume...');
    try {
      const r = await axios.post('/api/cast/volume', { level: volume, device_name: selectedDevice, ip: deviceIp });
      setStatus(r.data.ok ? `Vol: ${Math.round(volume * 100)}%` : r.data.error);
    } catch { setStatus('Volume failed'); }
  };

  // Extract YouTube video ID from URL or bare ID
  const parseVideoId = (input: string) => {
    const match = input.match(/(?:v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : input.trim();
  };

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto">
      <div className="flex items-center justify-between">
        <p className="text-[9px] uppercase tracking-[0.4em] opacity-40" style={{ color: 'var(--cyan)' }}>
          📺 Cast Control
        </p>
      </div>

      {!castAvailable && (
        <div className="glass rounded p-3 text-[10px]" style={{ color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)', border: '1px solid' }}>
          pychromecast not installed — run: pip install pychromecast
        </div>
      )}

      {/* Device scan */}
      <div className="glass rounded-lg p-3" style={{ border: '1px solid rgba(6,182,212,0.2)' }}>
        <p className="text-[9px] uppercase tracking-[0.3em] mb-2 opacity-60" style={{ color: 'var(--cyan)' }}>Devices</p>
        <button onClick={scan} disabled={scanning}
          className="flex items-center gap-2 text-[10px] px-3 py-1.5 rounded border uppercase tracking-widest mb-2"
          style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.4)' }}>
          <Search size={10} /> {scanning ? 'Scanning...' : 'Scan Network'}
        </button>
        {devices.length > 0 && (
          <div className="flex flex-col gap-1">
            {devices.map((d, i) => (
              <button key={i} onClick={() => setSelectedDevice(d)}
                className="text-left text-[10px] px-2 py-1 rounded"
                style={{
                  color: selectedDevice === d ? 'var(--amber)' : 'var(--cyan)',
                  background: selectedDevice === d ? 'rgba(245,158,11,0.08)' : 'transparent',
                  border: `1px solid ${selectedDevice === d ? 'rgba(245,158,11,0.4)' : 'rgba(6,182,212,0.2)'}`,
                }}>
                <Tv size={9} className="inline mr-1.5" /> {d}
              </button>
            ))}
          </div>
        )}
        {/* Manual IP */}
        <input value={deviceIp} onChange={e => setDeviceIp(e.target.value)}
          placeholder="or enter device IP directly..."
          className="w-full mt-2 px-2 py-1.5 rounded text-[10px] font-mono bg-transparent border"
          style={{ color: 'var(--cyan)', borderColor: 'rgba(6,182,212,0.3)', outline: 'none' }} />
      </div>

      {/* YouTube cast */}
      <div className="glass rounded-lg p-3" style={{ border: '1px solid rgba(245,158,11,0.2)' }}>
        <p className="text-[9px] uppercase tracking-[0.3em] mb-2 opacity-60" style={{ color: 'var(--amber)' }}>
          <Youtube size={9} className="inline mr-1" /> YouTube
        </p>
        <div className="flex gap-2">
          <input value={videoId} onChange={e => setVideoId(e.target.value)}
            onBlur={e => setVideoId(parseVideoId(e.target.value))}
            placeholder="Video ID or YouTube URL..."
            className="flex-1 px-2 py-1.5 rounded text-[10px] font-mono bg-transparent border"
            style={{ color: 'var(--cyan)', borderColor: 'rgba(245,158,11,0.3)', outline: 'none' }} />
          <button onClick={playYouTube}
            className="px-3 py-1.5 rounded border text-[10px] uppercase tracking-widest flex items-center gap-1"
            style={{ color: 'var(--amber)', borderColor: 'rgba(245,158,11,0.4)' }}>
            ▶
          </button>
        </div>
      </div>

      {/* Volume */}
      <div className="glass rounded-lg p-3" style={{ border: '1px solid rgba(34,197,94,0.2)' }}>
        <p className="text-[9px] uppercase tracking-[0.3em] mb-2 opacity-60" style={{ color: 'var(--green)' }}>
          <Volume2 size={9} className="inline mr-1" /> Volume — {Math.round(volume * 100)}%
        </p>
        <div className="flex gap-2 items-center">
          <input type="range" min={0} max={1} step={0.05} value={volume}
            onChange={e => setVolume(parseFloat(e.target.value))}
            className="flex-1 accent-amber-500" />
          <button onClick={setVol}
            className="px-3 py-1.5 rounded border text-[10px] uppercase tracking-widest"
            style={{ color: 'var(--green)', borderColor: 'rgba(34,197,94,0.4)' }}>
            Set
          </button>
        </div>
      </div>

      {status && (
        <p className="text-[9px] font-mono px-1" style={{ color: 'var(--amber)' }}>» {status}</p>
      )}
    </div>
  );
}
