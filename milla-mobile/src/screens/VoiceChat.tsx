import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, ScrollView, StyleSheet,
  TextInput, KeyboardAvoidingView, Platform, ActivityIndicator,
  Vibration,
} from 'react-native';
import { Audio } from 'expo-av';
import * as Haptics from 'expo-haptics';
import { COLORS, NEXUS_SERVER, NEXUS_WS } from '../config';
import { useNeuro } from '../hooks/useNeuro';

interface Message { role: 'user' | 'assistant' | 'system'; text: string; ts: number; }

export default function VoiceChat() {
  const { state: neuro, connected } = useNeuro();
  const [messages, setMessages] = useState<Message[]>([
    { role: 'system', text: '[ Neural link established · Forever Morth ]', ts: Date.now() },
  ]);
  const [input, setInput]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [recording, setRecording] = useState(false);
  const [recObj, setRecObj]       = useState<Audio.Recording | null>(null);

  const scroll = useRef<ScrollView>(null);
  const ws     = useRef<WebSocket | null>(null);

  // Connect voice WebSocket
  useEffect(() => {
    const connect = () => {
      const socket = new WebSocket(`${NEXUS_WS}/ws/voice`);
      ws.current = socket;
      socket.onmessage = (e) => {
        if (typeof e.data === 'string') {
          const frame = JSON.parse(e.data);
          if (frame.type === 'transcript') {
            addMsg('user', frame.text);
          } else if (frame.type === 'response') {
            addMsg('assistant', frame.text);
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            setLoading(false);
          }
        } else {
          // binary = TTS audio — play it
          playAudioBlob(e.data);
        }
      };
      socket.onerror  = () => socket.close();
      socket.onclose  = () => setTimeout(connect, 3000);
    };
    connect();
    return () => ws.current?.close();
  }, []);

  const addMsg = (role: Message['role'], text: string) => {
    setMessages(m => [...m, { role, text, ts: Date.now() }]);
    setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 100);
  };

  const playAudioBlob = async (data: ArrayBuffer) => {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: `data:audio/mp3;base64,${btoa(String.fromCharCode(...new Uint8Array(data)))}` });
      await sound.playAsync();
    } catch { /* silent fail */ }
  };

  const sendText = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    setLoading(true);
    addMsg('user', text);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(text);
    } else {
      // Fallback to HTTP
      try {
        const res = await fetch(`${NEXUS_SERVER}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        addMsg('assistant', data.response || '[No response]');
      } catch (e) {
        addMsg('system', `Connection error: ${e}`);
      }
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecObj(recording);
      setRecording(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    } catch (e) { console.error(e); }
  };

  const stopRecording = async () => {
    if (!recObj) return;
    setRecording(false);
    setLoading(true);
    await recObj.stopAndUnloadAsync();
    const uri = recObj.getURI();
    setRecObj(null);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    if (!uri) { setLoading(false); return; }

    // Send audio file to /api/stt then pipe to chat
    const form = new FormData();
    form.append('file', { uri, name: 'voice.m4a', type: 'audio/m4a' } as never);
    try {
      const sttRes = await fetch(`${NEXUS_SERVER}/api/stt`, { method: 'POST', body: form });
      const { transcript } = await sttRes.json();
      if (transcript) {
        addMsg('user', transcript);
        const chatRes = await fetch(`${NEXUS_SERVER}/api/chat`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: transcript }),
        });
        const chatData = await chatRes.json();
        addMsg('assistant', chatData.response || '[No response]');
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (e) { addMsg('system', `Voice error: ${e}`); }
    setLoading(false);
  };

  // Mic orb color pulses with dopamine
  const orcColor = recording
    ? COLORS.red
    : `rgba(245,158,11,${0.3 + neuro.dopamine * 0.5})`;

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>

      {/* Header */}
      <View style={s.header}>
        <Text style={s.headerTitle}>M·I·L·L·A</Text>
        <View style={[s.dot, { backgroundColor: connected ? COLORS.green : COLORS.red }]} />
        <Text style={s.subTitle}>RAYNE OS · {connected ? 'LINKED' : 'OFFLINE'}</Text>
      </View>

      {/* Neuro bar strip */}
      <View style={s.neuroStrip}>
        {['dopamine','serotonin','atp_energy'].map(key => (
          <View key={key} style={s.neuroItem}>
            <Text style={s.neuroLabel}>{key.slice(0,3).toUpperCase()}</Text>
            <View style={s.neuroTrack}>
              <View style={[s.neuroFill, {
                width: `${(neuro[key as keyof typeof neuro] as number) * 100}%`,
                backgroundColor: key === 'dopamine' ? COLORS.amber : key === 'serotonin' ? COLORS.cyan : COLORS.green,
              }]} />
            </View>
          </View>
        ))}
      </View>

      {/* Messages */}
      <ScrollView ref={scroll} style={s.messages} contentContainerStyle={{ paddingBottom: 16 }}>
        {messages.map((m, i) => (
          <View key={i} style={[
            s.bubble,
            m.role === 'user'      && s.bubbleUser,
            m.role === 'assistant' && s.bubbleAssistant,
            m.role === 'system'    && s.bubbleSystem,
          ]}>
            <Text style={[
              s.bubbleText,
              m.role === 'user'      && { color: COLORS.amber },
              m.role === 'assistant' && { color: COLORS.cyan },
              m.role === 'system'    && { color: COLORS.dimText },
            ]}>{m.text}</Text>
          </View>
        ))}
        {loading && (
          <View style={s.bubbleAssistant}>
            <ActivityIndicator size="small" color={COLORS.cyan} />
          </View>
        )}
      </ScrollView>

      {/* Mic orb */}
      <TouchableOpacity
        style={[s.micOrb, { borderColor: orcColor, shadowColor: orcColor }]}
        onPressIn={startRecording}
        onPressOut={stopRecording}
        activeOpacity={0.8}
      >
        <Text style={[s.micIcon, { color: orcColor }]}>
          {recording ? '◉' : '◎'}
        </Text>
        <Text style={[s.micLabel, { color: orcColor }]}>
          {recording ? 'LISTENING' : 'HOLD TO SPEAK'}
        </Text>
      </TouchableOpacity>

      {/* Text input bar */}
      <View style={s.inputRow}>
        <TextInput
          style={s.input}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={sendText}
          placeholder="Type to Milla…"
          placeholderTextColor={COLORS.dimText}
          returnKeyType="send"
        />
        <TouchableOpacity style={s.sendBtn} onPress={sendText} disabled={loading}>
          <Text style={[s.sendText, { color: loading ? COLORS.dimText : COLORS.amber }]}>▶</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container:      { flex: 1, backgroundColor: COLORS.bg },
  header:         { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  headerTitle:    { fontSize: 18, fontWeight: '900', color: COLORS.amber, letterSpacing: 8, fontFamily: 'monospace' },
  dot:            { width: 6, height: 6, borderRadius: 3, marginHorizontal: 8 },
  subTitle:       { fontSize: 9, color: COLORS.cyan, letterSpacing: 4, opacity: 0.6, fontFamily: 'monospace' },
  neuroStrip:     { flexDirection: 'row', paddingHorizontal: 20, paddingVertical: 10, gap: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  neuroItem:      { flex: 1 },
  neuroLabel:     { fontSize: 8, color: COLORS.dimText, letterSpacing: 2, marginBottom: 3, fontFamily: 'monospace' },
  neuroTrack:     { height: 3, backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' },
  neuroFill:      { height: '100%', borderRadius: 2 },
  messages:       { flex: 1, paddingHorizontal: 16, paddingTop: 12 },
  bubble:         { marginBottom: 8, padding: 12, borderRadius: 10, maxWidth: '85%' },
  bubbleUser:     { alignSelf: 'flex-end', backgroundColor: 'rgba(245,158,11,0.08)', borderWidth: 1, borderColor: 'rgba(245,158,11,0.2)' },
  bubbleAssistant:{ alignSelf: 'flex-start', backgroundColor: 'rgba(6,182,212,0.06)', borderWidth: 1, borderColor: 'rgba(6,182,212,0.15)' },
  bubbleSystem:   { alignSelf: 'center', paddingVertical: 4, paddingHorizontal: 10 },
  bubbleText:     { fontSize: 13, lineHeight: 20, fontFamily: 'monospace' },
  micOrb:         { alignSelf: 'center', width: 100, height: 100, borderRadius: 50, borderWidth: 2, justifyContent: 'center', alignItems: 'center', marginVertical: 16, shadowOpacity: 0.6, shadowRadius: 20, shadowOffset: { width: 0, height: 0 }, elevation: 10 },
  micIcon:        { fontSize: 32 },
  micLabel:       { fontSize: 7, letterSpacing: 2, marginTop: 4, fontFamily: 'monospace' },
  inputRow:       { flexDirection: 'row', paddingHorizontal: 16, paddingBottom: 32, paddingTop: 8, gap: 8, borderTopWidth: 1, borderTopColor: COLORS.border },
  input:          { flex: 1, backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: COLORS.border, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 10, color: '#fff', fontSize: 13, fontFamily: 'monospace' },
  sendBtn:        { width: 44, justifyContent: 'center', alignItems: 'center' },
  sendText:       { fontSize: 18 },
});
