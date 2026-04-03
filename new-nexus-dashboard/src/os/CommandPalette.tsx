import { useState, useEffect, useRef, useCallback } from 'react';
import { Search } from 'lucide-react';

export interface PaletteCommand {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  action: () => void;
  keywords?: string[];
}

interface Props {
  commands: PaletteCommand[];
}

export default function CommandPalette({ commands }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [idx, setIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = query.trim()
    ? commands.filter(c => {
        const q = query.toLowerCase();
        return c.label.toLowerCase().includes(q) ||
          c.description?.toLowerCase().includes(q) ||
          c.keywords?.some(k => k.toLowerCase().includes(q));
      })
    : commands;

  const run = useCallback((cmd: PaletteCommand) => {
    setOpen(false);
    setQuery('');
    cmd.action();
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(o => !o);
        setQuery('');
        setIdx(0);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  useEffect(() => { setIdx(0); }, [query]);

  if (!open) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 99999,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      paddingTop: '18vh',
    }}
    onClick={() => setOpen(false)}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '520px', maxWidth: '90vw',
          background: 'rgba(10,12,18,0.96)', backdropFilter: 'blur(24px)',
          border: '1px solid rgba(6,182,212,0.2)', borderRadius: '14px',
          boxShadow: '0 24px 64px rgba(0,0,0,0.8), 0 0 0 1px rgba(6,182,212,0.06)',
          overflow: 'hidden',
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {/* Search input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <Search size={14} style={{ color: 'rgba(6,182,212,0.5)', flexShrink: 0 }} />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'ArrowDown') { e.preventDefault(); setIdx(i => Math.min(i + 1, filtered.length - 1)); }
              if (e.key === 'ArrowUp')   { e.preventDefault(); setIdx(i => Math.max(i - 1, 0)); }
              if (e.key === 'Enter' && filtered[idx]) run(filtered[idx]);
            }}
            placeholder="Search commands..."
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              fontSize: '13px', color: 'rgba(255,255,255,0.85)',
              letterSpacing: '0.03em',
            }}
          />
          <kbd style={{ fontSize: '9px', color: 'rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', padding: '2px 5px' }}>ESC</kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', fontSize: '11px', color: 'rgba(255,255,255,0.2)' }}>
              No commands found
            </div>
          ) : filtered.map((cmd, i) => (
            <div
              key={cmd.id}
              onClick={() => run(cmd)}
              onMouseEnter={() => setIdx(i)}
              style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: '10px 16px', cursor: 'pointer',
                background: i === idx ? 'rgba(6,182,212,0.1)' : 'transparent',
                borderLeft: `2px solid ${i === idx ? 'rgba(6,182,212,0.6)' : 'transparent'}`,
                transition: 'background 0.1s ease',
              }}
            >
              <span style={{ fontSize: '16px', width: '20px', textAlign: 'center', flexShrink: 0 }}>{cmd.icon ?? '◈'}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)', letterSpacing: '0.05em' }}>{cmd.label}</div>
                {cmd.description && (
                  <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)', marginTop: '1px', letterSpacing: '0.03em' }}>{cmd.description}</div>
                )}
              </div>
              {i === idx && (
                <kbd style={{ fontSize: '9px', color: 'rgba(6,182,212,0.5)', background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)', borderRadius: '4px', padding: '2px 5px', flexShrink: 0 }}>↵</kbd>
              )}
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <div style={{ padding: '8px 16px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '16px' }}>
          {[['↑↓', 'navigate'], ['↵', 'open'], ['esc', 'close']].map(([key, label]) => (
            <span key={key} style={{ fontSize: '9px', color: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <kbd style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '3px', padding: '1px 4px', fontFamily: 'inherit' }}>{key}</kbd>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
