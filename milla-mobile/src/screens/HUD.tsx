import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import * as Haptics from 'expo-haptics';
import { COLORS, NEURO_COLORS, NEXUS_SERVER } from '../config';
import { useNeuro } from '../hooks/useNeuro';

interface QuickAction { label: string; icon: string; color: string; endpoint: string; body?: object; }

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Cast Bedroom TV',  icon: '📺', color: COLORS.amber,  endpoint: '/api/computer/action', body: { action: 'shell', args: { command: 'python3 core_os/tools/cast_control.py scan' } } },
  { label: 'Screenshot',       icon: '📸', color: COLORS.cyan,   endpoint: '/api/computer/screenshot' },
  { label: 'System Status',    icon: '⚡', color: COLORS.green,  endpoint: '/api/neuro' },
  { label: 'List Macros',      icon: '🎬', color: COLORS.purple, endpoint: '/api/computer/macro/list' },
];

export default function HUD() {
  const { state: neuro, connected } = useNeuro();
  const [authenticated, setAuthenticated] = useState(false);
  const [actionResults, setActionResults] = useState<Record<string, unknown>>({});
  const [running, setRunning] = useState<string | null>(null);
  const [nodes, setNodes]     = useState({ termux: false, google: false, swarm: false });

  useEffect(() => {
    checkBiometrics();
    fetchNodes();
  }, []);

  const checkBiometrics = async () => {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    if (!hasHardware) { setAuthenticated(true); return; }
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Nexus Kingdom — Identity Verification',
      fallbackLabel: 'Use Passcode',
    });
    setAuthenticated(result.success);
    if (result.success) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  const fetchNodes = async () => {
    try {
      const res = await fetch(`${NEXUS_SERVER}/api/nodes`);
      setNodes(await res.json());
    } catch { /* offline */ }
  };

  const runAction = async (action: QuickAction) => {
    setRunning(action.label);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const res = await fetch(`${NEXUS_SERVER}${action.endpoint}`, {
        method: action.body ? 'POST' : 'GET',
        headers: action.body ? { 'Content-Type': 'application/json' } : {},
        body: action.body ? JSON.stringify(action.body) : undefined,
      });
      const result = await res.json();
      setActionResults(r => ({ ...r, [action.label]: result }));
    } catch (e) {
      setActionResults(r => ({ ...r, [action.label]: { error: String(e) } }));
    }
    setRunning(null);
  };

  if (!authenticated) {
    return (
      <View style={[s.container, s.center]}>
        <Text style={s.lockIcon}>🔐</Text>
        <Text style={s.lockText}>IDENTITY REQUIRED</Text>
        <TouchableOpacity style={s.authBtn} onPress={checkBiometrics}>
          <Text style={s.authBtnText}>AUTHENTICATE</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const neuroEntries = Object.entries(neuro).filter(([k]) => k in NEURO_COLORS);

  return (
    <ScrollView style={s.container} contentContainerStyle={{ paddingBottom: 40 }}>

      {/* Header */}
      <View style={s.header}>
        <Text style={s.title}>NEURAL HUD</Text>
        <View style={[s.dot, { backgroundColor: connected ? COLORS.green : COLORS.red }]} />
      </View>

      {/* Neuro chemicals */}
      <View style={s.card}>
        <Text style={s.cardTitle}>NEURO STATE</Text>
        {neuroEntries.map(([key, val]) => {
          const pct = typeof val === 'number' ? (key === 'atp_energy' ? val / 100 : val) : 0;
          const color = NEURO_COLORS[key] ?? COLORS.cyan;
          return (
            <View key={key} style={s.neuroRow}>
              <Text style={[s.neuroKey, { color }]}>{key.slice(0, 8).toUpperCase()}</Text>
              <View style={s.track}>
                <View style={[s.fill, { width: `${Math.min(100, pct * 100)}%`, backgroundColor: color }]} />
              </View>
              <Text style={[s.neuroVal, { color }]}>{(pct * 100).toFixed(0)}%</Text>
            </View>
          );
        })}
      </View>

      {/* System nodes */}
      <View style={s.card}>
        <Text style={s.cardTitle}>SYSTEM NODES</Text>
        {[
          { label: 'Termux Bridge', active: nodes.termux, color: COLORS.green },
          { label: 'Google OAuth',  active: nodes.google, color: nodes.google ? COLORS.green : COLORS.amber },
          { label: 'Swarm Sync',    active: nodes.swarm,  color: COLORS.cyan },
          { label: 'Neural Link',   active: connected,    color: COLORS.purple },
        ].map(node => (
          <View key={node.label} style={s.nodeRow}>
            <Text style={s.nodeLabel}>{node.label}</Text>
            <View style={[s.nodeDot, { backgroundColor: node.active ? node.color : 'rgba(255,255,255,0.1)', shadowColor: node.active ? node.color : 'transparent', shadowOpacity: 0.8, shadowRadius: 6, shadowOffset: { width: 0, height: 0 } }]} />
          </View>
        ))}
      </View>

      {/* Quick actions */}
      <View style={s.card}>
        <Text style={s.cardTitle}>QUICK ACTIONS</Text>
        <View style={s.actionGrid}>
          {QUICK_ACTIONS.map(action => (
            <TouchableOpacity key={action.label} style={[s.actionBtn, { borderColor: action.color + '40' }]}
              onPress={() => runAction(action)} disabled={running === action.label}>
              {running === action.label
                ? <ActivityIndicator size="small" color={action.color} />
                : <Text style={s.actionIcon}>{action.icon}</Text>}
              <Text style={[s.actionLabel, { color: action.color }]}>{action.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {/* Last result */}
        {running === null && Object.keys(actionResults).length > 0 && (
          <View style={s.resultBox}>
            <Text style={s.resultText} numberOfLines={4}>
              {JSON.stringify(Object.values(actionResults).at(-1), null, 2)}
            </Text>
          </View>
        )}
      </View>

    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: COLORS.bg },
  center:      { justifyContent: 'center', alignItems: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  title:       { fontSize: 14, fontWeight: '900', color: COLORS.amber, letterSpacing: 6, fontFamily: 'monospace', flex: 1 },
  dot:         { width: 8, height: 8, borderRadius: 4 },
  card:        { margin: 16, marginBottom: 0, padding: 16, backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: COLORS.border, borderRadius: 12 },
  cardTitle:   { fontSize: 9, color: COLORS.cyan, letterSpacing: 4, marginBottom: 14, fontFamily: 'monospace', opacity: 0.7 },
  neuroRow:    { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  neuroKey:    { width: 80, fontSize: 9, letterSpacing: 2, fontFamily: 'monospace' },
  track:       { flex: 1, height: 4, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' },
  fill:        { height: '100%', borderRadius: 2 },
  neuroVal:    { width: 36, textAlign: 'right', fontSize: 9, fontFamily: 'monospace' },
  nodeRow:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  nodeLabel:   { fontSize: 11, color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' },
  nodeDot:     { width: 10, height: 10, borderRadius: 5 },
  actionGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  actionBtn:   { width: '47%', padding: 14, borderWidth: 1, borderRadius: 10, alignItems: 'center', gap: 6, backgroundColor: 'rgba(255,255,255,0.02)' },
  actionIcon:  { fontSize: 22 },
  actionLabel: { fontSize: 10, letterSpacing: 1, fontFamily: 'monospace', textAlign: 'center' },
  resultBox:   { marginTop: 12, padding: 10, backgroundColor: 'rgba(0,0,0,0.4)', borderRadius: 6 },
  resultText:  { fontSize: 10, color: COLORS.green, fontFamily: 'monospace' },
  lockIcon:    { fontSize: 48, marginBottom: 16 },
  lockText:    { fontSize: 12, color: COLORS.amber, letterSpacing: 6, fontFamily: 'monospace', marginBottom: 24 },
  authBtn:     { paddingHorizontal: 32, paddingVertical: 12, borderWidth: 1, borderColor: COLORS.amber, borderRadius: 8 },
  authBtnText: { color: COLORS.amber, fontSize: 11, letterSpacing: 4, fontFamily: 'monospace' },
});
