import { useState, useRef } from 'react';
import axios from 'axios';
import { Eye, Upload, X, Loader } from 'lucide-react';

const API = 'http://100.89.122.112:8000';

export default function VisionPanel() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('Describe what you see in detail.');
  const [result, setResult] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadFile = (file: File) => {
    setImageFile(file);
    setResult('');
    const reader = new FileReader();
    reader.onload = e => setImagePreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) loadFile(file);
  };

  const analyze = async () => {
    if (!imageFile) return;
    setAnalyzing(true); setResult('');
    try {
      const fd = new FormData();
      fd.append('image', imageFile, imageFile.name);
      fd.append('prompt', prompt);
      const res = await axios.post(`${API}/api/vision/analyze`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 90000,
      });
      setResult(res.data.description || '[No description]');
    } catch (e: any) {
      setResult(`[Error: ${e.message}]`);
    }
    setAnalyzing(false);
  };

  const clear = () => { setImagePreview(null); setImageFile(null); setResult(''); };

  return (
    <div className="flex flex-col gap-3 p-2 font-mono text-sm">
      <div className="flex items-center gap-2 text-amber-400">
        <Eye size={16} />
        <span className="font-bold uppercase tracking-widest text-xs">Milla's Eye</span>
        <span className="text-[10px] text-gray-500">moondream vision model</span>
      </div>

      {/* Drop zone */}
      {!imagePreview ? (
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors ${
            dragging ? 'border-amber-400 bg-amber-400/10' : 'border-gray-700 hover:border-gray-500'
          }`}
        >
          <Upload size={28} className="text-gray-600" />
          <p className="text-xs text-gray-500">Drop image here or click to browse</p>
          <p className="text-[9px] text-gray-700">JPG, PNG, WebP supported</p>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={e => e.target.files?.[0] && loadFile(e.target.files[0])} />
        </div>
      ) : (
        <div className="relative">
          <img src={imagePreview} alt="Preview" className="w-full max-h-56 object-contain rounded border border-gray-700 bg-black" />
          <button onClick={clear} className="absolute top-2 right-2 bg-black/70 rounded-full p-1 text-gray-400 hover:text-white">
            <X size={14} />
          </button>
          <p className="text-[10px] text-gray-600 mt-1 text-center">{imageFile?.name}</p>
        </div>
      )}

      {/* Prompt */}
      <div>
        <label className="text-[10px] text-gray-500 mb-1 block uppercase tracking-wider">Vision Prompt</label>
        <input
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="w-full bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-600 focus:border-amber-400 outline-none"
        />
      </div>

      <button
        onClick={analyze}
        disabled={!imageFile || analyzing}
        className="py-2 px-4 bg-amber-500 text-black font-bold text-xs rounded hover:bg-amber-400 disabled:opacity-40 flex items-center justify-center gap-2"
      >
        {analyzing ? <><Loader size={13} className="animate-spin" /> Analyzing…</> : <><Eye size={13} /> Analyze Image</>}
      </button>

      {analyzing && (
        <div className="text-center text-[10px] text-amber-400 animate-pulse">Milla is looking… (first run loads moondream ~30s)</div>
      )}

      {result && (
        <div className="bg-gray-900 border border-gray-700 rounded p-3">
          <div className="text-[9px] text-cyan-500 mb-1.5 tracking-widest uppercase">Milla's Analysis</div>
          <p className="text-xs text-gray-200 leading-relaxed whitespace-pre-wrap">{result}</p>
        </div>
      )}
    </div>
  );
}
