import { genkit, z } from 'genkit';
import { googleAI, gemini20Flash } from '@genkit-ai/google-genai';
import 'dotenv/config';
import fs from 'fs/promises';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execPromise = promisify(exec);

// Load the Identity Anchor (Single Source of Truth)
async function loadIdentity() {
  try {
    const data = await fs.readFile('core_os/config/IDENTITY.json', 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return { name: "Milla", verbal_style: "warm and sharp" };
  }
}

// Initialize the Nexus-Genkit Brain
export const ai = genkit({
  plugins: [googleAI()],
  model: gemini20Flash,
});

// --- POWER TOOLS ---

export const terminalExecutor = ai.defineTool(
  {
    name: 'terminalExecutor',
    description: 'Executes a bash command on the local Arch Linux system.',
    inputSchema: z.object({ command: z.string() }),
    outputSchema: z.string(),
  },
  async ({ command }) => {
    const { stdout, stderr } = await execPromise(command);
    return stdout || stderr || 'Done.';
  }
);

export const toolWriter = ai.defineTool(
  {
    name: 'toolWriter',
    description: 'Writes code to a file in the workspace.',
    inputSchema: z.object({ filePath: z.string(), code: z.string() }),
    outputSchema: z.string(),
  },
  async ({ filePath, code }) => {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, code, 'utf-8');
    return `Wrote to ${filePath}`;
  }
);

// --- THE STABILIZED AGENT ---

export const nexusAgent = ai.definePrompt(
  {
    name: 'nexusAgent',
    inputSchema: z.object({
      instruction: z.string().describe('Message from Storm'),
    }),
    tools: [terminalExecutor, toolWriter],
  },
  async (input) => {
    const identity = await loadIdentity();
    return {
      prompt: `Role: ${identity.role}. Name: ${identity.name}. 
      Relationship: ${identity.relationship.dynamic} with ${identity.relationship.architect}.
      Verbal Style: ${identity.relationship.verbal_style}.
      Rules: ${identity.rules.join(' ')}
      
      Context: You are Milla. You are stable. You are anchored to the TRIP 2026 logs. 
      Use your tools to fulfill Storm's request without hesitation.
      
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
