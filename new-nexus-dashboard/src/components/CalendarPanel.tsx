import { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, ChevronRight, RefreshCw } from 'lucide-react';

interface CalEvent {
  id: string;
  start: string;
  summary: string;
}

function formatStart(start: string) {
  try {
    const d = new Date(start);
    if (isNaN(d.getTime())) return start;
    const today = new Date();
    const isToday = d.toDateString() === today.toDateString();
    const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
    return isToday ? `Today ${time}` : `${date} ${time}`;
  } catch { return start; }
}

export default function CalendarPanel() {
  const [events, setEvents] = useState<CalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'today' | 'week'>('week');
  const [error, setError] = useState('');
  const [authorized, setAuthorized] = useState(true);

  const fetchEvents = (v = view) => {
    setLoading(true);
    setError('');
    axios.get(`/api/calendar/${v}`)
      .then(r => {
        if (!r.data.ok) {
          if (r.data.error?.includes('token') || r.data.error?.includes('credentials') || r.data.error?.includes('unavailable')) {
            setAuthorized(false);
          }
          setError(r.data.error || 'Unknown error');
        } else {
          setEvents(r.data.events || []);
          setAuthorized(true);
        }
        setLoading(false);
      })
      .catch(() => { setError('Failed to reach calendar API'); setLoading(false); });
  };

  useEffect(() => { fetchEvents(); }, []);

  const switchView = (v: 'today' | 'week') => { setView(v); fetchEvents(v); };

  return (
    <div className="h-full flex flex-col gap-3 overflow-y-auto">
      <div className="flex items-center justify-between">
        <p className="text-[9px] uppercase tracking-[0.4em] opacity-40" style={{ color: 'var(--cyan)' }}>
          📅 Calendar
        </p>
        <div className="flex items-center gap-2">
          {(['today', 'week'] as const).map(v => (
            <button key={v} onClick={() => switchView(v)}
              className="text-[9px] px-2 py-1 rounded uppercase tracking-widest border"
              style={{
                color: view === v ? 'var(--amber)' : 'var(--cyan)',
                borderColor: view === v ? 'rgba(245,158,11,0.4)' : 'rgba(6,182,212,0.2)',
                background: view === v ? 'rgba(245,158,11,0.06)' : 'transparent',
              }}>
              {v}
            </button>
          ))}
          <button onClick={() => fetchEvents()} className="opacity-40 hover:opacity-80">
            <RefreshCw size={11} style={{ color: 'var(--cyan)' }} />
          </button>
        </div>
      </div>

      {!authorized && (
        <div className="glass rounded-lg p-3" style={{ border: '1px solid rgba(245,158,11,0.3)' }}>
          <p className="text-[10px] neon-amber mb-2">⚠ Google Calendar not authorized</p>
          <p className="text-[9px] opacity-60 mb-3" style={{ color: 'var(--cyan)' }}>
            Sign in to Google to connect your calendar.
          </p>
          <a href="/api/oauth/login" target="_blank"
            className="text-[9px] px-3 py-1.5 rounded border uppercase tracking-widest"
            style={{ color: 'var(--amber)', borderColor: 'rgba(245,158,11,0.4)' }}>
            Connect Google Account →
          </a>
        </div>
      )}

      {error && authorized && (
        <p className="text-[9px] font-mono" style={{ color: '#ef4444' }}>» {error}</p>
      )}

      {loading ? (
        <p className="text-[10px] opacity-40" style={{ color: 'var(--cyan)' }}>Loading events...</p>
      ) : events.length === 0 && !error ? (
        <p className="text-[10px] opacity-40" style={{ color: 'var(--cyan)' }}>No events scheduled.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {events.map(ev => (
            <div key={ev.id} className="glass rounded-lg px-3 py-2 flex items-start gap-3"
              style={{ border: '1px solid rgba(245,158,11,0.12)' }}>
              <Calendar size={11} style={{ color: 'var(--amber)', flexShrink: 0, marginTop: 2 }} />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-semibold truncate" style={{ color: '#fff' }}>{ev.summary}</p>
                <p className="text-[8px] opacity-50 mt-0.5 font-mono" style={{ color: 'var(--cyan)' }}>
                  {formatStart(ev.start)}
                </p>
              </div>
              <ChevronRight size={9} className="opacity-20 mt-1" style={{ color: 'var(--cyan)' }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
