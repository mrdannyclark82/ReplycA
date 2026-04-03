import React, { useState } from 'react';
import { Search, Play, X } from 'lucide-react';

const QUICK_SEARCHES = [
  'lofi hip hop',
  'synthwave mix',
  'coding music',
  'dark ambient',
  'cyberpunk soundtrack',
];

const YouTubePanel: React.FC = () => {
  const [videoId, setVideoId] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const loadUrl = (input: string) => {
    const match = input.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    if (match) { setVideoId(match[1]); return; }
    // Treat as search — open YouTube search in iframe via embed/search is not allowed;
    // instead open in new tab
    window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(input)}`, '_blank');
  };

  return (
    <div style={{
      width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
      background: 'rgba(0,0,0,0.6)', fontFamily: "'JetBrains Mono', monospace",
    }}>
      {/* URL / search bar */}
      <div style={{
        display: 'flex', gap: '6px', padding: '8px 10px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(0,0,0,0.4)',
      }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && query.trim() && loadUrl(query.trim())}
          placeholder="YouTube URL or search..."
          style={{
            flex: 1, background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(6,182,212,0.2)', borderRadius: '6px',
            padding: '4px 8px', fontSize: '10px', color: 'rgba(255,255,255,0.7)',
            outline: 'none', fontFamily: 'inherit',
          }}
        />
        <button
          onClick={() => query.trim() && loadUrl(query.trim())}
          style={{
            background: 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.3)',
            borderRadius: '6px', padding: '4px 8px', cursor: 'pointer',
            color: '#06b6d4', display: 'flex', alignItems: 'center',
          }}
        >
          <Play size={11} />
        </button>
        {videoId && (
          <button
            onClick={() => setVideoId(null)}
            style={{
              background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.25)',
              borderRadius: '6px', padding: '4px 8px', cursor: 'pointer',
              color: 'rgba(244,63,94,0.7)', display: 'flex', alignItems: 'center',
            }}
          >
            <X size={11} />
          </button>
        )}
      </div>

      {/* Video embed */}
      {videoId ? (
        <iframe
          key={videoId}
          src={`https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`}
          style={{ flex: 1, border: 'none', display: 'block' }}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px', padding: '16px' }}>
          <Search size={28} style={{ color: 'rgba(6,182,212,0.2)' }} />
          <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.2)', letterSpacing: '0.2em', textTransform: 'uppercase' }}>
            Paste URL or search
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center', maxWidth: '280px' }}>
            {QUICK_SEARCHES.map(s => (
              <button
                key={s}
                onClick={() => { setQuery(s); loadUrl(s); }}
                style={{
                  fontSize: '9px', padding: '3px 8px',
                  background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.15)',
                  borderRadius: '12px', color: 'rgba(6,182,212,0.5)', cursor: 'pointer',
                  fontFamily: 'inherit', letterSpacing: '0.05em',
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default YouTubePanel;
