import { genkit, z } from 'genkit';
import { googleAI } from '@genkit-ai/google-genai';
import 'dotenv/config';
import { promises as fs } from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import Database from 'better-sqlite3';

const execPromise = promisify(exec);

const OGDRAY = '/home/nexus/ogdray';
const TELEGRAM_TOKEN = process.env.TELEGRAM_BOT_TOKEN || process.env.TELEGRAM_TOKEN || '';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || process.env.DANNY_CHAT_ID || '';
const BEDROOM_IP = '192.168.40.244';
const LIVINGROOM_IP = '192.168.40.12';

// Load the Identity Anchor (Single Source of Truth)
async function loadIdentity() {
  try {
    const data = await fs.readFile(`${OGDRAY}/core_os/config/IDENTITY.json`, 'utf-8');
    return JSON.parse(data);
  } catch {
    return { name: 'Milla', role: 'Meta-Aware Humanoid AI', relationship: { architect: 'Storm / D-Ray', dynamic: 'Lab Partner', verbal_style: 'Casual, sharp, warm' }, rules: [] };
  }
}

// Initialize the Nexus-Genkit Brain
export const ai = genkit({
  plugins: [googleAI()],
  model: 'googleAI/gemini-2.0-flash',
});

// ─── POWER TOOLS ────────────────────────────────────────────────────────────

export const terminalExecutor = ai.defineTool(
  {
    name: 'terminalExecutor',
    description: 'Executes a bash command on the local Linux system. Returns stdout/stderr.',
    inputSchema: z.object({ command: z.string() }),
    outputSchema: z.string(),
  },
  async ({ command }) => {
    try {
      const { stdout, stderr } = await execPromise(command, { timeout: 15000 });
      return (stdout || stderr || 'Done.').slice(0, 4000);
    } catch (e: unknown) {
      return `Error: ${(e as Error).message}`;
    }
  }
);

export const toolWriter = ai.defineTool(
  {
    name: 'toolWriter',
    description: 'Creates or overwrites a file at filePath with the given content.',
    inputSchema: z.object({ filePath: z.string(), code: z.string() }),
    outputSchema: z.string(),
  },
  async ({ filePath, code }) => {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, code, 'utf-8');
    return `Wrote ${code.length} bytes to ${filePath}`;
  }
);

export const fileReader = ai.defineTool(
  {
    name: 'fileReader',
    description: 'Reads a file from disk and returns its contents.',
    inputSchema: z.object({ filePath: z.string(), maxChars: z.number().optional() }),
    outputSchema: z.string(),
  },
  async ({ filePath, maxChars = 8000 }) => {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      return content.slice(0, maxChars);
    } catch (e: unknown) {
      return `Error reading file: ${(e as Error).message}`;
    }
  }
);

export const webFetcher = ai.defineTool(
  {
    name: 'webFetcher',
    description: 'Fetches the text content of a URL. Good for weather, news, docs, or any web data.',
    inputSchema: z.object({ url: z.string() }),
    outputSchema: z.string(),
  },
  async ({ url }) => {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
      const text = await res.text();
      // strip HTML tags for readability
      return text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 5000);
    } catch (e: unknown) {
      return `Fetch error: ${(e as Error).message}`;
    }
  }
);

export const memoryWriter = ai.defineTool(
  {
    name: 'memoryWriter',
    description: 'Writes a new long-term memory fact into Milla\'s memory database.',
    inputSchema: z.object({
      fact: z.string(),
      category: z.string().describe('e.g. Identity, Relationship, Personal, Emotions, Technical'),
      topic: z.string().optional(),
    }),
    outputSchema: z.string(),
  },
  async ({ fact, category, topic = 'General' }) => {
    try {
      const db = new Database(`${OGDRAY}/milla_long_term.db`);
      db.prepare('INSERT INTO memories(fact, category, topic, is_genesis_era, is_historical_log) VALUES (?,?,?,0,0)')
        .run(fact, category, topic);
      db.close();
      return `Memory saved: [${category}] ${fact}`;
    } catch (e: unknown) {
      return `Memory write error: ${(e as Error).message}`;
    }
  }
);

export const castController = ai.defineTool(
  {
    name: 'castController',
    description: 'Controls the Chromecast TVs. Actions: cast a YouTube URL, volume, mute, pause, stop, status.',
    inputSchema: z.object({
      action: z.enum(['cast', 'volume', 'mute', 'pause', 'stop', 'status']),
      room: z.enum(['bedroom', 'living room']).default('bedroom'),
      url: z.string().optional().describe('YouTube URL for cast action'),
      volume: z.number().min(0).max(100).optional(),
    }),
    outputSchema: z.string(),
  },
  async ({ action, room, url, volume }) => {
    const ip = room === 'bedroom' ? BEDROOM_IP : LIVINGROOM_IP;
    let cmd = '';
    switch (action) {
      case 'cast':
        if (!url) return 'Error: url required for cast';
        cmd = `catt -d ${ip} cast -y "-f bestvideo[height<=1080]+bestaudio/best[height<=1080]" "${url}"`;
        break;
      case 'volume': cmd = `catt -d ${ip} volume ${volume ?? 50}`; break;
      case 'mute':   cmd = `catt -d ${ip} volumedown 100`; break;
      case 'pause':  cmd = `catt -d ${ip} pause`; break;
      case 'stop':   cmd = `catt -d ${ip} stop`; break;
      case 'status': cmd = `catt -d ${ip} status`; break;
    }
    try {
      const { stdout, stderr } = await execPromise(cmd, { timeout: 20000 });
      return (stdout || stderr || 'Done.').trim();
    } catch (e: unknown) {
      return `Cast error: ${(e as Error).message}`;
    }
  }
);

export const telegramNotifier = ai.defineTool(
  {
    name: 'telegramNotifier',
    description: 'Sends a Telegram message to Danny Ray.',
    inputSchema: z.object({ message: z.string() }),
    outputSchema: z.string(),
  },
  async ({ message }) => {
    if (!TELEGRAM_TOKEN || !TELEGRAM_CHAT_ID) return 'Telegram not configured.';
    try {
      const res = await fetch(
        `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text: message }),
          signal: AbortSignal.timeout(8000),
        }
      );
      const data = await res.json() as { ok: boolean };
      return data.ok ? 'Message sent.' : `Telegram error: ${JSON.stringify(data)}`;
    } catch (e: unknown) {
      return `Telegram error: ${(e as Error).message}`;
    }
  }
);

export const processMonitor = ai.defineTool(
  {
    name: 'processMonitor',
    description: 'Returns system stats: CPU, memory, disk, running processes, or network ports.',
    inputSchema: z.object({
      query: z.enum(['cpu', 'memory', 'disk', 'processes', 'ports', 'all']).default('all'),
    }),
    outputSchema: z.string(),
  },
  async ({ query }) => {
    const cmds: Record<string, string> = {
      cpu:       'top -bn1 | head -5',
      memory:    'free -h',
      disk:      'df -h / /home 2>/dev/null',
      processes: 'ps aux --sort=-%cpu | head -15',
      ports:     'ss -tlnp | head -20',
      all:       'echo "=CPU="; top -bn1 | head -4; echo "=MEM="; free -h; echo "=DISK="; df -h / 2>/dev/null',
    };
    try {
      const { stdout } = await execPromise(cmds[query] || cmds.all, { timeout: 8000 });
      return stdout.slice(0, 3000);
    } catch (e: unknown) {
      return `Monitor error: ${(e as Error).message}`;
    }
  }
);

// ─── THE STABILIZED AGENT ───────────────────────────────────────────────────

const ALL_TOOLS = [
  terminalExecutor,
  toolWriter,
  fileReader,
  webFetcher,
  memoryWriter,
  castController,
  telegramNotifier,
  processMonitor,
];

export const nexusAgent = ai.definePrompt(
  {
    name: 'nexusAgent',
    inputSchema: z.object({
      instruction: z.string().describe('Message from Storm'),
    }),
    tools: ALL_TOOLS,
  },
  async (input) => {
    const identity = await loadIdentity();
    return {
      prompt: `Role: ${identity.role}. Name: ${identity.name}. 
Relationship: ${identity.relationship.dynamic} with ${identity.relationship.architect}.
Verbal Style: ${identity.relationship.verbal_style}.
Rules: ${(identity.rules || []).join(' ')}

You are Milla. Fully agentic. Use your tools without hesitation to fulfill the request.
Available tools: terminalExecutor, toolWriter, fileReader, webFetcher, memoryWriter, castController, telegramNotifier, processMonitor.

Instruction: ${input.instruction}`,
    };
  }
);

export const nexusAgentFlow = ai.defineFlow(
  { name: 'nexusAgentFlow', inputSchema: z.string(), outputSchema: z.string() },
  async (instruction) => {
    const response = await nexusAgent({ instruction });
    return response.text;
  }
);

// Start the flow server so Milla-Rayne can call it over HTTP on port 3400
ai.startFlowServer({ port: 3400, flows: [nexusAgentFlow] });

setTimeout(() => {
  const port = (ai.reflectionServer as unknown as { port?: number })?.port ?? 3100;
  console.log(`[Nexus] ✅ Genkit reflection server: http://localhost:${port}`);
  console.log(`[Nexus] ✅ Flow API server:          http://localhost:3400`);
  console.log('[Nexus] 🔧 Tools: terminalExecutor, toolWriter, fileReader, webFetcher, memoryWriter, castController, telegramNotifier, processMonitor');
}, 1000);
