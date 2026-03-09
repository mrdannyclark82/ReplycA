import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search, Trash2, Plus, Database, RefreshCw } from 'lucide-react';

const API = '';

interface Memory {
  rowid: number;
  fact: string;
  category: string;
  topic: string;
}

export default function MemoryBrowser() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [newFact, setNewFact] = useState('');
  const [newCat, setNewCat] = useState('manual');
  const [addOpen, setAddOpen] = useState(false);
  const LIMIT = 30;

  const fetchMemories = useCallback(async (q = query, off = offset) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/memory/search`, { params: { q, limit: LIMIT, offset: off } });
      setMemories(res.data.memories || []);
      setTotal(res.data.total || 0);
    } catch { /* ignore */ }
    setLoading(false);
  }, [query, offset]);

  useEffect(() => { fetchMemories(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchMemories(query, 0);
  };

  const handleDelete = async (rowid: number) => {
    await axios.delete(`${API}/api/memory/${rowid}`);
    setMemories(prev => prev.filter(m => m.rowid !== rowid));
    setTotal(prev => prev - 1);
  };

  const handleAdd = async () => {
    if (!newFact.trim()) return;
    await axios.post(`${API}/api/memory`, { fact: newFact, category: newCat, topic: 'user-added' });
    setNewFact('');
    setAddOpen(false);
    fetchMemories(query, offset);
  };

  const catColor: Record<string, string> = {
    conversation: 'text-cyan-400',
    genesis: 'text-purple-400',
    knowledge: 'text-green-400',
    manual: 'text-amber-400',
  };

  return (
    <div className="flex flex-col gap-3 p-2 text-sm font-mono">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <Database size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Memory Core</span>
          <span className="text-xs text-gray-500">({total.toLocaleString()} records)</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setAddOpen(!addOpen)} className="px-2 py-1 text-xs bg-amber-400/10 border border-amber-400/30 text-amber-400 hover:bg-amber-400/20 rounded flex items-center gap-1">
            <Plus size={12} /> Add
          </button>
          <button onClick={() => fetchMemories()} className="px-2 py-1 text-xs bg-gray-800 border border-gray-600 text-gray-400 hover:text-white rounded">
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      {/* Add panel */}
      {addOpen && (
        <div className="bg-gray-900 border border-amber-400/30 rounded p-3 flex flex-col gap-2">
          <textarea
            value={newFact}
            onChange={e => setNewFact(e.target.value)}
            placeholder="Enter memory fact..."
            className="w-full bg-black border border-gray-700 rounded p-2 text-xs text-white placeholder-gray-600 resize-none h-16"
          />
          <div className="flex gap-2 items-center">
            <select value={newCat} onChange={e => setNewCat(e.target.value)} className="bg-black border border-gray-700 rounded p-1 text-xs text-white">
              <option value="manual">manual</option>
              <option value="knowledge">knowledge</option>
              <option value="conversation">conversation</option>
              <option value="genesis">genesis</option>
            </select>
            <button onClick={handleAdd} className="px-3 py-1 text-xs bg-amber-500 text-black font-bold rounded hover:bg-amber-400">Save</button>
            <button onClick={() => setAddOpen(false)} className="px-3 py-1 text-xs text-gray-500 hover:text-white">Cancel</button>
          </div>
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="flex-1 relative">
          <Search size={12} className="absolute left-2 top-2.5 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search memories..."
            className="w-full bg-black border border-gray-700 rounded pl-7 pr-2 py-1.5 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none"
          />
        </div>
        <button type="submit" className="px-3 py-1.5 text-xs bg-amber-400/20 border border-amber-400/40 text-amber-400 hover:bg-amber-400/30 rounded">
          Search
        </button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="text-center text-gray-500 py-6 text-xs animate-pulse">scanning memory banks…</div>
      ) : (
        <div className="flex flex-col gap-1 max-h-[480px] overflow-y-auto pr-1">
          {memories.length === 0 && <div className="text-center text-gray-600 py-6 text-xs">No records found.</div>}
          {memories.map(m => (
            <div key={m.rowid} className="group bg-gray-900/60 border border-gray-800 hover:border-gray-600 rounded p-2.5 flex gap-2 items-start">
              <div className="flex-1 min-w-0">
                <p className="text-gray-200 text-xs leading-relaxed break-words">{m.fact}</p>
                <div className="flex gap-2 mt-1">
                  <span className={`text-[10px] ${catColor[m.category] || 'text-gray-500'}`}>{m.category}</span>
                  {m.topic && <span className="text-[10px] text-gray-600">#{m.topic}</span>}
                </div>
              </div>
              <button
                onClick={() => handleDelete(m.rowid)}
                className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-opacity shrink-0 mt-0.5"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>{offset + 1}–{Math.min(offset + LIMIT, total)} of {total}</span>
          <div className="flex gap-2">
            <button disabled={offset === 0} onClick={() => { const o = Math.max(0, offset - LIMIT); setOffset(o); fetchMemories(query, o); }} className="px-2 py-1 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700">←</button>
            <button disabled={offset + LIMIT >= total} onClick={() => { const o = offset + LIMIT; setOffset(o); fetchMemories(query, o); }} className="px-2 py-1 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700">→</button>
          </div>
        </div>
      )}
    </div>
  );
}
