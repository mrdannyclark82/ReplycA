import { useState, useEffect } from 'react';
import axios from 'axios';
import { Mail, Send, RefreshCw, Reply, AlertCircle } from 'lucide-react';

const API = '';

interface Email {
  id: string;
  threadId: string;
  subject: string;
  sender: string;
  snippet: string;
  error?: string;
}

export default function GmailPanel() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Email | null>(null);
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState('');
  const [view, setView] = useState<'inbox' | 'compose'>('inbox');

  const fetchInbox = async () => {
    setLoading(true); setError('');
    try {
      const res = await axios.get(`${API}/api/email/inbox`, { params: { limit: 15 } });
      if (res.data.ok) {
        setEmails(res.data.emails || []);
      } else {
        setError(res.data.error || 'Failed to load inbox');
      }
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  useEffect(() => { fetchInbox(); }, []);

  const replyTo = (email: Email) => {
    setSelected(email);
    setComposeTo(email.sender.match(/<(.+)>/)?.[1] || email.sender);
    setComposeSubject(`Re: ${email.subject}`);
    setComposeBody('');
    setView('compose');
  };

  const handleSend = async () => {
    if (!composeTo.trim() || !composeSubject.trim()) return;
    setSending(true); setSendResult('');
    try {
      const res = await axios.post(`${API}/api/email/send`, {
        to: composeTo,
        subject: composeSubject,
        body: composeBody,
        thread_id: selected?.threadId || ''
      });
      setSendResult(res.data.status === 'success' ? '✓ Sent!' : `Error: ${res.data.msg}`);
      if (res.data.status === 'success') {
        setTimeout(() => { setView('inbox'); setSendResult(''); setSelected(null); }, 2000);
      }
    } catch (e: any) { setSendResult(`Error: ${e.message}`); }
    setSending(false);
  };

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-400">
          <Mail size={16} />
          <span className="font-bold uppercase tracking-widest text-xs">Gmail</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setView('compose'); setSelected(null); setComposeTo(''); setComposeSubject(''); setComposeBody(''); }}
            className="px-2 py-1 text-xs bg-amber-400/10 border border-amber-400/30 text-amber-400 hover:bg-amber-400/20 rounded flex items-center gap-1">
            <Send size={11} /> Compose
          </button>
          {view === 'inbox' && (
            <button onClick={fetchInbox} className={`p-1 text-gray-500 hover:text-white ${loading ? 'animate-spin' : ''}`}>
              <RefreshCw size={13} />
            </button>
          )}
          {view === 'compose' && (
            <button onClick={() => setView('inbox')} className="px-2 py-1 text-xs text-gray-500 hover:text-white rounded border border-gray-700">
              ← Inbox
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-400/10 border border-red-400/30 text-red-400 text-xs rounded">
          <AlertCircle size={12} /> {error}
          {error.includes('OAuth') && <a href={`${API}/api/oauth/login`} target="_blank" rel="noreferrer" className="underline ml-1">Authorize →</a>}
        </div>
      )}

      {/* Inbox */}
      {view === 'inbox' && (
        <div className="flex flex-col gap-1 max-h-[500px] overflow-y-auto pr-1">
          {loading && <div className="text-center text-gray-600 text-xs py-8 animate-pulse">fetching inbox…</div>}
          {!loading && emails.length === 0 && !error && <div className="text-center text-gray-600 text-xs py-8">Inbox empty.</div>}
          {emails.map(email => (
            <div key={email.id} className="group bg-gray-900/60 border border-gray-800 hover:border-gray-600 rounded p-3 cursor-pointer" onClick={() => replyTo(email)}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-white truncate">{email.subject}</p>
                  <p className="text-[10px] text-cyan-400 truncate mt-0.5">{email.sender}</p>
                  <p className="text-[10px] text-gray-500 mt-1 line-clamp-2">{email.snippet}</p>
                </div>
                <button className="opacity-0 group-hover:opacity-100 shrink-0 mt-1 text-amber-400 hover:text-amber-300">
                  <Reply size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Compose / Reply */}
      {view === 'compose' && (
        <div className="flex flex-col gap-2">
          {selected && (
            <div className="px-3 py-2 bg-gray-900 border border-gray-700 rounded text-[10px] text-gray-400">
              <span className="text-gray-600">Replying to:</span> {selected.subject}
            </div>
          )}
          <input value={composeTo} onChange={e => setComposeTo(e.target.value)} placeholder="To"
            className="bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none" />
          <input value={composeSubject} onChange={e => setComposeSubject(e.target.value)} placeholder="Subject"
            className="bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none" />
          <textarea value={composeBody} onChange={e => setComposeBody(e.target.value)}
            placeholder="Message body… (Milla will help craft the reply)"
            className="bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none resize-none h-36" />
          <div className="flex items-center gap-3">
            <button onClick={handleSend} disabled={sending || !composeTo.trim()}
              className="px-4 py-2 text-xs bg-amber-500 text-black font-bold rounded hover:bg-amber-400 disabled:opacity-40 flex items-center gap-1">
              <Send size={12} /> {sending ? 'Sending…' : 'Send'}
            </button>
            {sendResult && <span className={`text-xs ${sendResult.startsWith('✓') ? 'text-green-400' : 'text-red-400'}`}>{sendResult}</span>}
          </div>
          <p className="text-[9px] text-gray-700">Milla uses your draft as context to write the final email body.</p>
        </div>
      )}
    </div>
  );
}
