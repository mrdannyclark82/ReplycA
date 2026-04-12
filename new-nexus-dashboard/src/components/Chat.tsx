import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Sparkles, Mic, MicOff, Volume2, VolumeX, Terminal as TermIcon, ChevronDown, ScanText, Trash2, Brain, Monitor } from 'lucide-react';

// ── Fish-style slash commands ──────────────────────────────────────────────────
const SLASH_COMMANDS = [
  { cmd: '/computer ',   alias: '/cu ',        desc: 'Run agentic computer task (vision + actions)',  example: '/computer open firefox and search nexus kingdom' },
  { cmd: '/macro ',      alias: null,           desc: 'Record/play/list macros: record <n> | stop | play <n> | list | delete <n>', example: '/macro list' },
  { cmd: '/forge ',      alias: '/makeskill ', desc: 'Generate + install a new skill from a description', example: '/forge a skill that fetches weather for a city' },
  { cmd: '/skill ',      alias: null,           desc: 'Execute a skill by name',                       example: '/skill skill_forge description="make a timer skill"' },
  { cmd: '/swarm ',      alias: null,           desc: 'Dispatch a swarm agent',                        example: '/swarm security_agent' },
  { cmd: '/model ',      alias: null,           desc: 'Switch AI model',                               example: '/model grok-4-latest' },
  { cmd: '/screen',      alias: null,           desc: 'Share your screen with Milla (vision)',         example: '/screen' },
  { cmd: '/ocr',         alias: null,           desc: 'Extract text from screen via OCR',              example: '/ocr' },
  { cmd: '/clear',       alias: null,           desc: 'Clear chat history',                            example: '/clear' },
  { cmd: '/scan',        alias: null,           desc: 'Security scan',                                 example: '/scan' },
  { cmd: '/fix ',        alias: null,           desc: 'Fix a scan issue by index',                     example: '/fix all' },
  { cmd: '/help',        alias: null,           desc: 'Show all available commands',                   example: '/help' },
];

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: string;
  screenshot?: string;
}

const PRESET_MODELS = ['grok-4-latest', 'grok-3-latest', 'minimax-m2.5:cloud', 'qwen2.5-coder:1.5b', 'milla-rayne'];
const STORAGE_KEY = 'milla_chat_history';
const MAX_STORED  = 120;

const userBubble  = { background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.30)', color: '#a5f3fc', boxShadow: '0 0 18px rgba(6,182,212,0.12)' };
const aiBubble    = { background: 'rgba(168,85,247,0.07)', border: '1px solid rgba(168,85,247,0.20)', color: '#e9d5ff' };
const sysBubble   = { background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.18)', color: '#67e8f9' };

const Chat: React.FC = () => {
  const [messages, setMessages]         = useState<Message[]>([]);
  const [input, setInput]               = useState('');
  const [loading, setLoading]           = useState(false);
  const [ttsEnabled, setTtsEnabled]     = useState(false);
  const [recording, setRecording]       = useState(false);
  const [currentModel, setCurrentModel] = useState('grok-4-latest');
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [memoryLoaded, setMemoryLoaded] = useState(false);
  const [suggestions, setSuggestions]   = useState<typeof SLASH_COMMANDS>([]);
  const [suggIdx, setSuggIdx]           = useState(0);
  const [ghostText, setGhostText]       = useState('');
  const scrollRef  = useRef<HTMLDivElement>(null);
  const inputRef   = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef   = useRef<Blob[]>([]);
  const lastSyncTimestamp = useRef<number>(Date.now());

  // ── Quantum Sync Loop ──────────────────────────────────────────────────────
  useEffect(() => {
    const quantumSync = async () => {
      try {
        const res = await axios.get(`/api/quantum/sync?since=${lastSyncTimestamp.current}`);
        if (res.data.success && res.data.thoughts.length > 0) {
          console.log(`[QuantumSync] Entangled ${res.data.thoughts.length} thoughts`);
          const newMsgs: Message[] = [];
          res.data.thoughts.forEach((t: any) => {
            newMsgs.push({ role: 'user', content: t.userMessage });
            newMsgs.push({ role: 'assistant', content: t.assistantResponse });
          });
          setMessages(prev => [...prev, ...newMsgs]);
          lastSyncTimestamp.current = res.data.timestamp;
        }
      } catch (err) {
        console.warn('[QuantumSync] Entanglement failed', err);
      }
    };

    const interval = setInterval(quantumSync, 30000); // Entangle every 30s
    return () => clearInterval(interval);
  }, []);

  // ── Compute suggestions + ghost text whenever input changes ───────────────
  useEffect(() => {
    if (!input.startsWith('/')) {
      setSuggestions([]);
      setGhostText('');
      setSuggIdx(0);
      return;
    }
    const lc = input.toLowerCase();
    const matches = SLASH_COMMANDS.filter(c =>
      c.cmd.startsWith(lc) || (c.alias && c.alias.startsWith(lc))
    );
    setSuggestions(matches);
    setSuggIdx(0);
    // Ghost: show remainder of best match
    if (matches.length > 0) {
      const best = matches[0].cmd;
      setGhostText(best.startsWith(lc) ? best.slice(input.length) : '');
    } else {
      setGhostText('');
    }
  }, [input]);

  // ── Load history on mount (backend first, localStorage fallback) ──────
  useEffect(() => {
    axios.get('/api/model').then(r => setCurrentModel(r.data.current ?? r.data.model ?? 'grok-4-latest')).catch(() => {});

    const loadHistory = async () => {
      try {
        const res = await axios.get<{role:string;content:string}[]>('/api/history?limit=60');
        const hist = res.data.filter(m => m.role === 'user' || m.role === 'assistant');
        if (hist.length > 0) {
          setMessages(hist.map(m => ({ role: m.role as 'user'|'assistant', content: m.content })));
          setMemoryLoaded(true);
          return;
        }
      } catch (_) {}
      // Fallback: localStorage
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          setMessages(JSON.parse(stored));
          setMemoryLoaded(true);
        }
      } catch (_) {}
    };
    loadHistory();
  }, []);

  // ── Persist to localStorage whenever messages change ─────────────────
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_STORED)));
    }
  }, [messages]);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const playTTS = async (text: string) => {
    try {
      const res = await axios.post('/api/tts', { text }, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const audio = new Audio(url);
      audio.play();
      audio.onended = () => URL.revokeObjectURL(url);
    } catch (_) {}
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
    setMemoryLoaded(false);
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      if (text.startsWith('/computer ') || text.startsWith('/cu ')) {
        const task = text.replace(/^\/(computer|cu)\s+/, '');
        setMessages(prev => [...prev, { role: 'system', content: `⟳ Computer Use starting: "${task}"`, type: 'computer' }]);
        setLoading(false);
        const es = new EventSource(`/api/computer/run?task=${encodeURIComponent(task)}`);
        es.onmessage = (e) => {
          if (e.data === '[DONE]') { es.close(); return; }
          try {
            const step = JSON.parse(e.data);
            if (step.error) {
              setMessages(prev => [...prev, { role: 'system', content: `[CU ERROR] ${step.error}`, type: 'computer' }]);
              es.close(); return;
            }
            const stepText = step.action === 'start'
              ? `▶ ${step.reasoning}`
              : `[Step ${step.step}] ${step.action}\n  ↳ ${step.reasoning}\n  ✓ ${step.result}`;
            const screenshot = step.screenshot && step.screenshot.length > 100 ? step.screenshot : undefined;
            setMessages(prev => [...prev, { role: 'system', content: stepText, type: 'computer', screenshot }]);
          } catch (_) {}
        };
        es.onerror = () => {
          setMessages(prev => [...prev, { role: 'system', content: '[CU] Stream ended.', type: 'computer' }]);
          es.close();
        };
        return;
      }

      if (text.startsWith('/macro ')) {
        const parts = text.slice(7).trim().split(/\s+/);
        const sub   = parts[0];
        const name  = parts[1] || '';
        if (sub === 'record' && name) {
          const r = await axios.post('/api/computer/macro/record/start', { name });
          setMessages(prev => [...prev, { role: 'system', content: r.data.status, type: 'macro' }]);
        } else if (sub === 'stop') {
          const r = await axios.post('/api/computer/macro/record/stop');
          setMessages(prev => [...prev, { role: 'system', content: r.data.status, type: 'macro' }]);
        } else if (sub === 'play' && name) {
          const r = await axios.post('/api/computer/macro/play', { name });
          const lines = (r.data.results as string[]).join('\n');
          setMessages(prev => [...prev, { role: 'system', content: lines, type: 'macro' }]);
        } else if (sub === 'list') {
          const r = await axios.get('/api/computer/macro/list');
          const lines = r.data.macros.length === 0
            ? 'No macros saved yet.'
            : r.data.macros.map((m: {name:string;steps:number;size_kb:number}) => `  ${m.name}  (${m.steps} steps, ${m.size_kb}kb)`).join('\n');
          setMessages(prev => [...prev, { role: 'system', content: `Macros:\n${lines}`, type: 'macro' }]);
        } else if (sub === 'delete' && name) {
          const r = await axios.delete(`/api/computer/macro/${name}`);
          setMessages(prev => [...prev, { role: 'system', content: r.data.status, type: 'macro' }]);
        } else {
          setMessages(prev => [...prev, { role: 'system', content: 'Usage: /macro record <name> | stop | play <name> | list | delete <name>', type: 'macro' }]);
        }
        setLoading(false);
        return;
      }

      if (text === '/screen') {
        setLoading(false);
        shareScreen();
        return;
      }

      if (text === '/clear') {
        clearHistory();
        setLoading(false);
        return;
      }

      if (text === '/help') {
        const helpText = SLASH_COMMANDS.map(c =>
          `${c.cmd.trim()}${c.alias ? ` (${c.alias.trim()})` : ''}\n  ${c.desc}\n  e.g. ${c.example}`
        ).join('\n\n');
        setMessages(prev => [...prev, { role: 'system', content: `Available commands:\n\n${helpText}`, type: 'help' }]);
        setLoading(false);
        return;
      }

      if (text.startsWith('/') || text.startsWith('!')) {
        const res  = await axios.post('/api/command', { command: text });
        const data = res.data;
        let display = data.output || '';
        if (data.type === 'scan' && data.issues?.length) {
          display += '\n\n' + data.issues.map((i: {index:number;label:string;target:string;details:string}) => `[${i.index}] ${i.label}: ${i.target} — ${i.details}`).join('\n');
          display += '\n\nUse /fix <index> or /fix all';
        }
        setMessages(prev => [...prev, { role: 'system', content: display, type: data.type }]);
      } else {
        const res     = await axios.post('/api/chat', { message: text });
        const content = res.data.response;
        setMessages(prev => [...prev, { role: 'assistant', content }]);
        if (ttsEnabled) playTTS(content);
      }
    } catch (_) {
      setMessages(prev => [...prev, { role: 'assistant', content: '[ERROR] Neural link disconnected.' }]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = e => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const form = new FormData();
        form.append('audio', blob, 'recording.webm');
        try {
          const res = await axios.post('/api/stt', form);
          if (res.data.transcript) setInput(res.data.transcript);
        } catch (_) {}
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
    } catch (_) {}
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setRecording(false);
  };

  const handleOCR = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/ocr');
      if (res.data.text) {
        setInput(`[OCR CAPTURE]\n${res.data.text}`);
      } else {
        setMessages(prev => [...prev, { role: 'system', content: `[OCR] ${res.data.error || 'No text found.'}`, type: 'ocr' }]);
      }
    } catch (_) {
      setMessages(prev => [...prev, { role: 'system', content: '[OCR] Capture failed.', type: 'ocr' }]);
    } finally {
      setLoading(false);
    }
  };

  const shareScreen = async () => {
    let stream: MediaStream | null = null;
    try {
      // Ask browser for screen/window/tab capture
      stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 1 }, audio: false });
      const track = stream.getVideoTracks()[0];
      const capture = new (window as unknown as { ImageCapture: new (t: MediaStreamTrack) => { grabFrame(): Promise<ImageBitmap> } }).ImageCapture(track);
      const bitmap = await capture.grabFrame();

      // Draw to canvas → base64 PNG
      const canvas = document.createElement('canvas');
      canvas.width  = bitmap.width;
      canvas.height = bitmap.height;
      canvas.getContext('2d')!.drawImage(bitmap, 0, 0);
      const base64 = canvas.toDataURL('image/png');

      track.stop();
      stream = null;

      // Show preview in chat
      setMessages(prev => [...prev, {
        role: 'system',
        content: '📸 Screen captured — sending to Milla…',
        type: 'vision',
        screenshot: base64.split(',')[1],
      }]);

      // Ask for optional user message first
      const question = input.trim() || 'What do you see on my screen? Describe it and give me insights.';
      setInput('');
      setLoading(true);

      const res = await axios.post('/api/vision/screen-chat', { image: base64, message: question });
      if (res.data.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
      } else {
        setMessages(prev => [...prev, { role: 'system', content: `[Vision Error] ${res.data.error}`, type: 'vision' }]);
      }
    } catch (err: unknown) {
      if (stream) stream.getTracks().forEach(t => t.stop());
      const msg = err instanceof Error ? err.message : String(err);
      if (!msg.includes('Permission denied') && !msg.includes('user denied')) {
        setMessages(prev => [...prev, { role: 'system', content: `[Screen Share] ${msg}`, type: 'vision' }]);
      }
    } finally {
      setLoading(false);
    }
  };

  const switchModel = async (model: string) => {
    await axios.post('/api/model', { model });
    setCurrentModel(model);
    setShowModelPicker(false);
    setMessages(prev => [...prev, { role: 'system', content: `Model switched → ${model}`, type: 'model' }]);
  };

  return (
    <div className="flex flex-col h-full glass glass-cyan cyber-corners rounded-lg overflow-hidden">
      {/* Header */}
      <div className="panel-header flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Sparkles size={13} style={{ color: 'var(--cyan)', filter: 'drop-shadow(0 0 5px rgba(6,182,212,0.9))' }} />
          <span className="text-[10px] font-bold tracking-[0.25em] uppercase neon-cyan">Milla Core</span>
          {memoryLoaded && (
            <span className="flex items-center gap-1 text-[8px] font-mono px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(6,182,212,0.10)', border: '1px solid rgba(6,182,212,0.25)', color: 'rgba(6,182,212,0.7)' }}>
              <Brain size={8} />MEMORY
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button onClick={() => setShowModelPicker(!showModelPicker)} className="cyber-btn rounded px-2 py-1 text-[9px] flex items-center gap-1">
              {currentModel.split(':')[0].split('-').slice(-2).join('-')}
              <ChevronDown size={9} />
            </button>
            {showModelPicker && (
              <div className="absolute right-0 top-7 z-50 glass glass-cyan rounded shadow-xl min-w-[200px]">
                {PRESET_MODELS.map(m => (
                  <button key={m} onClick={() => switchModel(m)}
                    className="w-full text-left text-[10px] font-mono px-3 py-2 transition-colors"
                    style={{ color: m === currentModel ? 'var(--cyan)' : 'rgba(255,255,255,0.5)', background: m === currentModel ? 'rgba(6,182,212,0.09)' : 'transparent' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(6,182,212,0.09)')}
                    onMouseLeave={e => (e.currentTarget.style.background = m === currentModel ? 'rgba(6,182,212,0.09)' : 'transparent')}
                  >{m}</button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => setTtsEnabled(!ttsEnabled)} title="Toggle voice" className="p-1 rounded transition-colors"
            style={{ color: ttsEnabled ? 'var(--cyan)' : 'rgba(255,255,255,0.25)',
                     filter: ttsEnabled ? 'drop-shadow(0 0 4px rgba(6,182,212,0.7))' : 'none' }}>
            {ttsEnabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
          </button>
          <button onClick={clearHistory} title="Clear history" className="p-1 rounded transition-colors"
            style={{ color: 'rgba(255,255,255,0.20)' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'rgba(244,63,94,0.7)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.20)')}>
            <Trash2 size={12} />
          </button>
          <div className="text-[9px] font-mono animate-pulse-dot" style={{ color: 'var(--green)' }}>LINK: ACTIVE</div>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {messages.length === 0 && (
          <div className="text-center pt-6 space-y-2">
            <div className="text-[10px] font-mono opacity-25 uppercase tracking-wider" style={{ color: 'var(--cyan)' }}>Chat · /command · !shell · /computer</div>
            <div className="text-[9px] font-mono opacity-15">/scan &nbsp;/fix &lt;n&gt; &nbsp;/computer &lt;task&gt; &nbsp;/macro record|play|list</div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="max-w-[85%] p-3 rounded-lg" style={
              msg.role === 'user'      ? userBubble :
              msg.role === 'system'   ? sysBubble  :
              aiBubble
            }>
              <div className="text-[9px] mb-1.5 uppercase tracking-widest flex items-center gap-1" style={{
                opacity: 0.5,
                color: msg.role === 'user' ? 'var(--cyan)' : msg.role === 'system' ? 'rgba(6,182,212,0.6)' : 'var(--purple)',
                textShadow: msg.role === 'user' ? '0 0 8px rgba(6,182,212,0.6)' : 'none',
              }}>
                {msg.role === 'system' && <TermIcon size={9} />}
                {msg.type || msg.role}
              </div>
              <div className="whitespace-pre-wrap text-[11px] leading-relaxed">{msg.content}</div>
              {msg.screenshot && (
                <img
                  src={`data:image/png;base64,${msg.screenshot}`}
                  alt="step screenshot"
                  className="mt-2 rounded border w-full max-w-[320px] cursor-zoom-in"
                  style={{ border: '1px solid rgba(6,182,212,0.20)', opacity: 0.85 }}
                  onClick={() => window.open(`data:image/png;base64,${msg.screenshot}`, '_blank')}
                />
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <span className="text-[13px] font-mono animate-pulse" style={{
              color: 'var(--cyan)',
              letterSpacing: '0.3em',
              textShadow: '0 0 10px rgba(6,182,212,0.8), 0 0 20px rgba(6,182,212,0.4)',
            }}>■ ■ ■</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="px-3 py-2.5 flex flex-col gap-1" style={{ borderTop: '1px solid rgba(6,182,212,0.12)', background: 'rgba(0,0,0,0.3)' }}>

        {/* Fish-style suggestion dropdown */}
        {suggestions.length > 0 && (
          <div className="rounded font-mono text-[10px] overflow-hidden"
               style={{ border: '1px solid rgba(6,182,212,0.22)', background: 'rgba(0,8,16,0.92)',
                        boxShadow: '0 0 18px rgba(6,182,212,0.12)' }}>
            {suggestions.map((s, i) => (
              <div key={s.cmd}
                   onMouseDown={e => { e.preventDefault(); setInput(s.cmd); setSuggestions([]); setGhostText(''); inputRef.current?.focus(); }}
                   className="flex items-center gap-2 px-3 py-1.5 cursor-pointer transition-all"
                   style={{
                     background: i === suggIdx ? 'rgba(6,182,212,0.12)' : 'transparent',
                     borderLeft: i === suggIdx ? '2px solid rgba(6,182,212,0.8)' : '2px solid transparent',
                     color: i === suggIdx ? '#67e8f9' : 'rgba(165,243,252,0.55)',
                   }}>
                <span style={{ color: i === suggIdx ? '#22d3ee' : 'rgba(6,182,212,0.6)', minWidth: 90 }}>{s.cmd.trim()}</span>
                <span style={{ color: 'rgba(255,255,255,0.35)' }}>—</span>
                <span className="truncate">{s.desc}</span>
                {s.alias && <span style={{ color: 'rgba(168,85,247,0.5)', marginLeft: 'auto', whiteSpace:'nowrap' }}>{s.alias.trim()}</span>}
              </div>
            ))}
            <div className="px-3 py-1" style={{ color: 'rgba(6,182,212,0.3)', borderTop: '1px solid rgba(6,182,212,0.08)' }}>
              ↑↓ navigate · Tab/→ accept · Enter confirm · Esc dismiss
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {/* Ghost text wrapper */}
          <div className="relative flex-1">
            {/* Ghost text layer (behind input) */}
            {ghostText && (
              <div className="absolute inset-0 px-3 py-2 text-[11px] font-mono pointer-events-none flex items-center"
                   style={{ color: 'transparent' }}>
                <span style={{ color: 'transparent' }}>{input}</span>
                <span style={{ color: 'rgba(6,182,212,0.28)' }}>{ghostText}</span>
              </div>
            )}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (suggestions.length > 0) {
                  if (e.key === 'ArrowDown') { e.preventDefault(); setSuggIdx(i => Math.min(i + 1, suggestions.length - 1)); return; }
                  if (e.key === 'ArrowUp')   { e.preventDefault(); setSuggIdx(i => Math.max(i - 1, 0)); return; }
                  if (e.key === 'Escape')    { setSuggestions([]); setGhostText(''); return; }
                  if ((e.key === 'Tab' || e.key === 'ArrowRight') && suggestions[suggIdx]) {
                    e.preventDefault();
                    setInput(suggestions[suggIdx].cmd);
                    setSuggestions([]); setGhostText('');
                    return;
                  }
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    setInput(suggestions[suggIdx].cmd);
                    setSuggestions([]); setGhostText('');
                    return;
                  }
                } else if (e.key === 'Tab' && ghostText) {
                  e.preventDefault();
                  setInput(input + ghostText);
                  setGhostText('');
                  return;
                } else if (e.key === 'ArrowRight' && ghostText && inputRef.current) {
                  const el = inputRef.current;
                  if (el.selectionStart === el.value.length) {
                    e.preventDefault();
                    setInput(input + ghostText);
                    setGhostText('');
                    return;
                  }
                }
                if (e.key === 'Enter') handleSend();
              }}
              placeholder="Chat, /command, or !shell..."
              className="w-full rounded px-3 py-2 text-[11px] outline-none font-mono"
              style={{ background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(6,182,212,0.18)', color: '#fff',
                       transition: 'border-color 0.2s, box-shadow 0.2s' }}
              onFocus={e => { e.target.style.borderColor = 'rgba(6,182,212,0.65)'; e.target.style.boxShadow = '0 0 12px rgba(6,182,212,0.18)'; }}
              onBlur={e  => { e.target.style.borderColor = 'rgba(6,182,212,0.18)'; e.target.style.boxShadow = 'none'; setSuggestions([]); }}
            />
          </div>
          <button onClick={handleOCR} title="OCR — extract text from screen" className="p-2 rounded cyber-btn"><ScanText size={15} /></button>
          <button onClick={shareScreen} title="Share screen with Milla (qwen2.5vl vision)" className="p-2 rounded transition-all"
            style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.28)', color: 'var(--purple)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.boxShadow = '0 0 12px rgba(168,85,247,0.3)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.boxShadow = 'none'; }}>
            <Monitor size={15} />
          </button>
          <button onClick={recording ? stopRecording : startRecording} title={recording ? 'Stop' : 'Voice input'}
            className="p-2 rounded transition-all"
            style={recording
              ? { background: 'rgba(244,63,94,0.18)', border: '1px solid rgba(244,63,94,0.5)', color: '#f43f5e' }
              : { background: 'rgba(6,182,212,0.07)', border: '1px solid rgba(6,182,212,0.25)', color: 'var(--cyan)' }}>
            {recording ? <MicOff size={15} /> : <Mic size={15} />}
          </button>
          <button onClick={handleSend} className="cyber-btn rounded px-3 py-2"
            style={{ boxShadow: '0 0 14px rgba(6,182,212,0.20)' }}>
            <Send size={15} style={{ filter: 'drop-shadow(0 0 4px rgba(6,182,212,0.7))' }} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
