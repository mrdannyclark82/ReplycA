// Central config — reads server URL from environment or falls back to Tailscale IP
export const NEXUS_SERVER = process.env.EXPO_PUBLIC_SERVER_URL ?? 'http://100.89.122.112:8000';
export const NEXUS_WS     = NEXUS_SERVER.replace(/^http/, 'ws');

export const COLORS = {
  bg:         '#030712',
  bgPanel:    'rgba(10,10,20,0.85)',
  amber:      '#f59e0b',
  cyan:       '#06b6d4',
  purple:     '#a855f7',
  green:      '#22c55e',
  red:        '#ef4444',
  dimText:    'rgba(255,255,255,0.4)',
  border:     'rgba(255,255,255,0.07)',
} as const;

export const NEURO_COLORS: Record<string, string> = {
  dopamine:         COLORS.amber,
  serotonin:        COLORS.cyan,
  norepinephrine:   COLORS.red,
  cortisol:         '#f97316',
  oxytocin:         COLORS.purple,
  atp_energy:       COLORS.green,
};
