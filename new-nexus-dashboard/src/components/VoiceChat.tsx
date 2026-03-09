import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Mic, MicOff, Volume2, VolumeX, Send, Loader } from 'lucide-react';

const API = 'http://100.89.122.112:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isAudio?: boolean;
}

export default function VoiceChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [typedInput, setTypedInput] = useState('');
  const [status, setStatus] = useState('STANDBY');
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const speak = async (text: string) => {
    if (!ttsEnabled) return;
    try {
      const res = await axios.post(`${API}/api/tts`, { text }, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      if (audioRef.current) { audioRef.current.pause(); URL.revokeObjectURL(audioRef.current.src); }
      audioRef.current = new Audio(url);
      audioRef.current.play();
    } catch { /* tts optional */ }
  };

  const sendText = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setProcessing(true);
    setStatus('THINKING');
    try {
      const res = await axios.post(`${API}/api/chat`, {
        message: text,
        history: messages.slice(-8).map(m => ({ role: m.role, content: m.content }))
      });
      const reply = res.data?.response || res.data?.message?.content || '[No response]';
      const assistantMsg: Message = { role: 'assistant', content: reply };
      setMessages(prev => [...prev, assistantMsg]);
      setStatus('STANDBY');
      await speak(reply);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `[Error: ${e.message}]` }]);
      setStatus('ERROR');
    }
    setProcessing(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setProcessing(true);
        setStatus('TRANSCRIBING');
        try {
          const fd = new FormData();
          fd.append('audio', blob, 'voice.webm');
          const sttRes = await axios.post(`${API}/api/stt`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
          const transcript = sttRes.data?.transcript?.trim();
          if (transcript) {
            await sendText(transcript);
          } else {
            setStatus('STANDBY');
            setProcessing(false);
          }
        } catch {
          setStatus('STT ERROR');
          setProcessing(false);
        }
      };
      mediaRef.current = mr;
      mr.start();
      setRecording(true);
      setStatus('RECORDING');
    } catch {
      setStatus('MIC DENIED');
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    mediaRef.current = null;
    setRecording(false);
  };

  const handleTypedSend = (e: React.FormEvent) => {
    e.preventDefault();
    sendText(typedInput);
    setTypedInput('');
  };

  const statusColor: Record<string, string> = {
    STANDBY: 'text-gray-500',
    RECORDING: 'text-red-400 animate-pulse',
    TRANSCRIBING: 'text-yellow-400 animate-pulse',
    THINKING: 'text-cyan-400 animate-pulse',
    ERROR: 'text-red-500',
    'STT ERROR': 'text-orange-500',
    'MIC DENIED': 'text-red-600',
  };

  return (
    <div className="flex flex-col h-full gap-2 p-2 font-mono text-sm">
      {/* Status bar */}
      <div className="flex items-center justify-between px-1">
        <span className="text-xs text-amber-400 tracking-widest uppercase font-bold">Voice Link</span>
        <div className="flex items-center gap-3">
          <span className={`text-[10px] tracking-widest uppercase ${statusColor[status] || 'text-gray-500'}`}>
            ⬡ {status}
          </span>
          <button onClick={() => setTtsEnabled(!ttsEnabled)} className={`text-xs ${ttsEnabled ? 'text-cyan-400' : 'text-gray-600'}`} title="Toggle TTS">
            {ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
          </button>
        </div>
      </div>

      {/* Message scroll */}
      <div className="flex-1 overflow-y-auto min-h-0 flex flex-col gap-2 pr-1">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-600 gap-2">
            <div className="text-4xl">⬡</div>
            <span className="text-xs tracking-widest">Press mic to speak, or type below</span>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-3 py-2 rounded text-xs leading-relaxed ${
              m.role === 'user'
                ? 'bg-amber-400/20 border border-amber-400/30 text-amber-100'
                : 'bg-gray-800 border border-gray-700 text-gray-100'
            }`}>
              {m.role === 'assistant' && <div className="text-[9px] text-cyan-500 mb-1 tracking-widest">MILLA RAYNE</div>}
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          </div>
        ))}
        {processing && (
          <div className="flex justify-start">
            <div className="bg-gray-800 border border-gray-700 px-3 py-2 rounded">
              <Loader size={12} className="text-cyan-400 animate-spin" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-center">
        <button
          onMouseDown={startRecording}
          onMouseUp={stopRecording}
          onTouchStart={startRecording}
          onTouchEnd={stopRecording}
          disabled={processing}
          className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center border transition-all ${
            recording
              ? 'bg-red-500/30 border-red-400 text-red-400 scale-110'
              : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-amber-400 hover:text-amber-400'
          } disabled:opacity-40`}
          title="Hold to record"
        >
          {recording ? <MicOff size={16} /> : <Mic size={16} />}
        </button>

        <form onSubmit={handleTypedSend} className="flex-1 flex gap-2">
          <input
            type="text"
            value={typedInput}
            onChange={e => setTypedInput(e.target.value)}
            placeholder="Or type here…"
            disabled={processing || recording}
            className="flex-1 bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none disabled:opacity-40"
          />
          <button
            type="submit"
            disabled={processing || !typedInput.trim()}
            className="px-3 py-2 bg-amber-400/20 border border-amber-400/40 text-amber-400 hover:bg-amber-400/30 rounded disabled:opacity-30"
          >
            <Send size={13} />
          </button>
        </form>
      </div>
      <p className="text-[9px] text-gray-700 text-center">Hold mic button to record voice • TTS plays Milla's responses</p>
    </div>
  );
}
