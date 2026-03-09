import { useEffect, useRef, useState } from 'react';
import { NEXUS_WS } from '../config';

export interface NeuroState {
  dopamine: number;
  serotonin: number;
  norepinephrine: number;
  cortisol: number;
  oxytocin: number;
  atp_energy: number;
  sense: string;
  google_auth: boolean;
}

const DEFAULT: NeuroState = {
  dopamine: 0.5, serotonin: 0.5, norepinephrine: 0.2,
  cortisol: 0.2, oxytocin: 0.3, atp_energy: 100,
  sense: 'default', google_auth: false,
};

export function useNeuro() {
  const [state, setState] = useState<NeuroState>(DEFAULT);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        const socket = new WebSocket(`${NEXUS_WS}/ws/neuro`);
        ws.current = socket;

        socket.onopen  = () => setConnected(true);
        socket.onclose = () => { setConnected(false); timeout = setTimeout(connect, 4000); };
        socket.onerror = () => socket.close();
        socket.onmessage = (e) => {
          try { setState(JSON.parse(e.data)); } catch { /* ignore */ }
        };
      } catch { timeout = setTimeout(connect, 4000); }
    };

    connect();
    return () => { clearTimeout(timeout); ws.current?.close(); };
  }, []);

  return { state, connected };
}
