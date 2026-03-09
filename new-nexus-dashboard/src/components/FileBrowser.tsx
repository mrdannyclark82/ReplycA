import { useEffect, useState, useCallback } from 'react';
import { Folder, File, ChevronRight, Save, ArrowLeft, RefreshCw } from 'lucide-react';

interface FsItem { name: string; path: string; type: 'file' | 'dir'; size: number | null; ext: string | null; }

const S = {
  root:    { height: '100%', display: 'flex', fontFamily: 'monospace', fontSize: '11px', color: 'var(--text)' },
  tree:    { width: '220px', minWidth: '180px', borderRight: '1px solid rgba(255,255,255,0.06)', overflowY: 'auto' as const, padding: '6px 0' },
  editor:  { flex: 1, display: 'flex', flexDirection: 'column' as const },
  head:    { padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' as const },
  title:   { color: 'var(--cyan)', letterSpacing: '1.5px', textTransform: 'uppercase' as const, fontSize: '10px', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  btn:     { background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'rgba(255,255,255,0.5)', padding: '3px 8px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  saveBtn: { background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: '4px', color: '#34d399', padding: '3px 10px', cursor: 'pointer', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '4px' },
  textarea:{ flex: 1, background: 'rgba(0,0,0,0.3)', color: 'rgba(255,255,255,0.85)', border: 'none', outline: 'none', resize: 'none' as const, padding: '12px', fontFamily: 'monospace', fontSize: '11px', lineHeight: '1.6' },
  row:     { padding: '4px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '4px', margin: '1px 4px' },
  crumb:   { color: 'var(--amber)', cursor: 'pointer', fontSize: '10px', opacity: 0.7, padding: '4px 12px' },
  status:  { padding: '4px 12px', fontSize: '9px', borderTop: '1px solid rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.3)' },
  msg:     (ok: boolean) => ({ color: ok ? '#34d399' : '#f87171', fontSize: '10px' }),
};

function sizeStr(n: number | null) {
  if (n === null) return '';
  if (n < 1024) return `${n}B`;
  if (n < 1024*1024) return `${(n/1024).toFixed(0)}K`;
  return `${(n/1024/1024).toFixed(1)}M`;
}

// SERVER: using relative /api/* via Vite proxy

export default function FileBrowser() {
  const [cwd, setCwd]         = useState('');
  const [items, setItems]     = useState<FsItem[]>([]);
  const [filePath, setFilePath]= useState('');
  const [content, setContent] = useState('');
  const [dirty, setDirty]     = useState(false);
  const [saving, setSaving]   = useState(false);
  const [msg, setMsg]         = useState<{ ok: boolean; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const listDir = useCallback(async (p: string) => {
    setLoading(true);
    try {
      const r = await fetch(`/api/files/tree?path=${encodeURIComponent(p)}`);
      const d = await r.json();
      if (d.ok) { setItems(d.items); setCwd(d.cwd); }
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { listDir(''); }, []);

  const openFile = async (path: string) => {
    try {
      const r = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
      const d = await r.json();
      if (d.ok) { setFilePath(d.path); setContent(d.content); setDirty(false); setMsg(null); }
      else setMsg({ ok: false, text: d.error });
    } catch { /* ignore */ }
  };

  const save = async () => {
    setSaving(true);
    try {
      const r = await fetch(`/api/files/write`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: filePath, content }),
      });
      const d = await r.json();
      if (d.ok) { setDirty(false); setMsg({ ok: true, text: `Saved ${d.path}` }); }
      else setMsg({ ok: false, text: d.error });
    } catch (e: unknown) { setMsg({ ok: false, text: String(e) }); }
    setSaving(false);
  };

  const goUp = () => {
    const parts = cwd.split('/').filter(Boolean);
    listDir(parts.slice(0, -1).join('/'));
  };

  const extColor = (ext: string | null) => {
    if (!ext) return 'rgba(255,255,255,0.5)';
    if (['.py'].includes(ext)) return '#fbbf24';
    if (['.ts','.tsx','.js','.jsx'].includes(ext)) return '#60a5fa';
    if (['.md','.txt'].includes(ext)) return '#a78bfa';
    if (['.json','.yaml','.toml','.env','.example'].includes(ext)) return '#34d399';
    if (['.sh','.bash'].includes(ext)) return '#f87171';
    return 'rgba(255,255,255,0.5)';
  };

  return (
    <div style={S.root}>
      {/* Tree panel */}
      <div style={S.tree}>
        <div style={{ padding: '6px 12px 2px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {cwd && <ArrowLeft size={11} style={{ cursor: 'pointer', color: 'rgba(255,255,255,0.4)' }} onClick={goUp} />}
            <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              /{cwd}
            </span>
            <RefreshCw size={9} style={{ cursor: 'pointer', color: 'rgba(255,255,255,0.3)', marginLeft: 'auto' }} onClick={() => listDir(cwd)} />
          </div>
        </div>
        {loading && <div style={{ padding: '8px 12px', color: 'rgba(255,255,255,0.3)', fontSize: '10px' }}>Loading…</div>}
        {items.map(item => (
          <div
            key={item.path}
            style={{ ...S.row, background: filePath === item.path ? 'rgba(255,255,255,0.05)' : undefined }}
            onClick={() => item.type === 'dir' ? listDir(item.path) : openFile(item.path)}
          >
            {item.type === 'dir'
              ? <><Folder size={11} color="var(--amber)" /><ChevronRight size={9} style={{ marginLeft: '-2px', opacity: 0.4 }} /></>
              : <File size={11} color={extColor(item.ext)} />
            }
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                           color: item.type === 'dir' ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.6)' }}>
              {item.name}
            </span>
            {item.size !== null && <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.25)' }}>{sizeStr(item.size)}</span>}
          </div>
        ))}
      </div>

      {/* Editor panel */}
      <div style={S.editor}>
        <div style={S.head}>
          <span style={S.title}>{filePath || 'Select a file'}</span>
          {dirty && <span style={{ color: '#fbbf24', fontSize: '9px' }}>● unsaved</span>}
          {msg && <span style={S.msg(msg.ok)}>{msg.text}</span>}
          {filePath && (
            <button style={S.saveBtn} onClick={save} disabled={!dirty || saving}>
              <Save size={9} />{saving ? 'Saving…' : 'Save'}
            </button>
          )}
        </div>
        {filePath
          ? <textarea
              style={S.textarea}
              value={content}
              onChange={e => { setContent(e.target.value); setDirty(true); setMsg(null); }}
              spellCheck={false}
            />
          : <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.15)', fontSize: '12px' }}>
              Select a file from the tree
            </div>
        }
        {filePath && (
          <div style={S.status}>
            {content.split('\n').length} lines · {content.length} chars
          </div>
        )}
      </div>
    </div>
  );
}
