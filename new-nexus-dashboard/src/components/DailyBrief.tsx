import { useState, useEffect } from 'react';
import axios from 'axios';
import { BookOpen, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

const API = 'http://100.89.122.112:8000';

interface Brief { date: string; filename: string; }

export default function DailyBrief() {
  const [briefs, setBriefs] = useState<Brief[]>([]);
  const [content, setContent] = useState('');
  const [date, setDate] = useState('');
  const [idx, setIdx] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchBriefs = async () => {
    setLoading(true);
    try {
      const list = await axios.get(`${API}/api/brief/list`);
      setBriefs(list.data.briefs || []);
      if (list.data.briefs?.length) {
        loadBrief(list.data.briefs[0], 0);
      } else {
        setLoading(false);
      }
    } catch { setLoading(false); }
  };

  const loadBrief = async (brief: Brief, i: number) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/brief/latest`);
      // For specific dates, just use the latest endpoint for now
      // In future can add /api/brief/{filename}
      if (i === 0) {
        setContent(res.data.content || '');
        setDate(res.data.date || brief.date);
      } else {
        setContent(`[Brief for ${brief.date}]\n\nUse the latest endpoint for full content.`);
        setDate(brief.date);
      }
      setIdx(i);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchBriefs(); }, []);

  // Simple markdown-ish renderer
  const renderContent = (text: string) => {
    return text.split('\n').map((line, i) => {
      if (line.startsWith('# ')) return <h1 key={i} className="text-sm font-bold text-amber-400 mt-3 mb-1">{line.slice(2)}</h1>;
      if (line.startsWith('## ')) return <h2 key={i} className="text-xs font-bold text-cyan-400 mt-2 mb-0.5">{line.slice(3)}</h2>;
      if (line.startsWith('### ')) return <h3 key={i} className="text-xs font-semibold text-purple-400 mt-1.5">{line.slice(4)}</h3>;
      if (line.startsWith('- ') || line.startsWith('* ')) return <li key={i} className="text-[11px] text-gray-300 ml-3 list-disc">{line.slice(2)}</li>;
      if (line.startsWith('> ')) return <blockquote key={i} className="text-[11px] text-gray-400 border-l-2 border-gray-600 pl-2 italic">{line.slice(2)}</blockquote>;
      if (line.trim() === '' || line === '---') return <div key={i} className="h-1.5" />;
      if (line.startsWith('```')) return <div key={i} className="h-0.5" />;
      return <p key={i} className="text-[11px] text-gray-300 leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <BookOpen size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Daily Brief</span>
          {date && <span className="text-[10px] text-gray-500">{date}</span>}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => briefs[idx + 1] && loadBrief(briefs[idx + 1], idx + 1)} disabled={idx >= briefs.length - 1}
            className="p-1 text-gray-600 hover:text-white disabled:opacity-30"><ChevronLeft size={14} /></button>
          <span className="text-[10px] text-gray-600">{idx + 1}/{briefs.length}</span>
          <button onClick={() => idx > 0 && loadBrief(briefs[idx - 1], idx - 1)} disabled={idx === 0}
            className="p-1 text-gray-600 hover:text-white disabled:opacity-30"><ChevronRight size={14} /></button>
          <button onClick={fetchBriefs} className="p-1 text-gray-600 hover:text-white ml-1"><RefreshCw size={12} /></button>
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-600 text-xs py-8 animate-pulse">loading brief…</div>
      ) : !content ? (
        <div className="text-center text-gray-600 text-xs py-8">No daily briefs found.</div>
      ) : (
        <div className="bg-gray-900/50 border border-gray-800 rounded p-4 max-h-[520px] overflow-y-auto">
          <div className="flex flex-col gap-0.5">{renderContent(content)}</div>
        </div>
      )}
    </div>
  );
}
