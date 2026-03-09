import React, { useEffect, useState, useRef, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl } from 'react-native';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { COLORS, NEXUS_SERVER } from '../config';

interface FeedItem {
  id: string;
  type: 'cron' | 'dream' | 'alert' | 'upgrade' | 'memory';
  title: string;
  body: string;
  ts: number;
  read: boolean;
}

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export default function Feed() {
  const [items, setItems]     = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const notifListener = useRef<ReturnType<typeof Notifications.addNotificationReceivedListener> | null>(null);

  useEffect(() => {
    registerForPush();
    loadFeed();

    notifListener.current = Notifications.addNotificationReceivedListener(notif => {
      const { title, body } = notif.request.content;
      setItems(prev => [{
        id: notif.request.identifier,
        type: 'alert',
        title: title ?? 'Milla Alert',
        body: body ?? '',
        ts: Date.now(),
        read: false,
      }, ...prev]);
    });

    return () => { notifListener.current?.remove(); };
  }, []);

  const registerForPush = async () => {
    try {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') return;
      const tokenData = await Notifications.getExpoPushTokenAsync({
        projectId: Constants.expoConfig?.extra?.eas?.projectId ?? 'nexus-kingdom',
      });
      await fetch(`${NEXUS_SERVER}/api/devices/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenData.data, platform: 'android' }),
      });
    } catch (e) { console.log('[Push] registration skipped:', e); }
  };

  const loadFeed = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${NEXUS_SERVER}/api/agent/feed`);
      const data = await res.json();
      if (data.ok && data.feed) {
        const mapped: FeedItem[] = data.feed.map((item: { source: string; content: string; job_id: string }, idx: number) => {
          const src = item.source || '';
          const isError = item.content?.toLowerCase().includes('error') || item.content?.toLowerCase().includes('traceback');
          const type: FeedItem['type'] = src.startsWith('memory:')
            ? (src.includes('dream') ? 'dream' : 'memory')
            : isError ? 'alert' : 'cron';
          return {
            id: `${item.job_id || idx}-${Date.now()}`,
            type,
            title: src.replace('cron:', '').replace('memory:', '').trim(),
            body: (item.content || '').trim().slice(0, 300),
            ts: Date.now() - idx * 60000,
            read: false,
          };
        });
        setItems(mapped);
      }
    } catch { /* offline */ }
    setLoading(false);
  }, []);

  const typeColor: Record<FeedItem['type'], string> = {
    cron:    COLORS.green,
    dream:   COLORS.purple,
    alert:   COLORS.red,
    upgrade: COLORS.cyan,
    memory:  COLORS.amber,
  };

  const typeIcon: Record<FeedItem['type'], string> = {
    cron: '⚙', dream: '💭', alert: '⚡', upgrade: '↑', memory: '◈',
  };

  return (
    <View style={s.container}>
      <View style={s.header}>
        <Text style={s.title}>MILLA FEED</Text>
        <TouchableOpacity onPress={loadFeed} disabled={loading}>
          {loading ? <ActivityIndicator size="small" color={COLORS.cyan} /> : <Text style={s.refresh}>↺</Text>}
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadFeed} tintColor={COLORS.cyan} />}
      >
        {items.length === 0 && !loading && (
          <View style={s.empty}>
            <Text style={s.emptyText}>No events yet</Text>
            <Text style={s.emptySubText}>Milla's activity will appear here</Text>
          </View>
        )}
        {items.map(item => (
          <TouchableOpacity key={item.id} style={[s.item, !item.read && s.itemUnread]}
            onPress={() => setItems(prev => prev.map(i => i.id === item.id ? { ...i, read: true } : i))}>
            <View style={[s.typeTag, { backgroundColor: typeColor[item.type] + '20', borderColor: typeColor[item.type] + '40' }]}>
              <Text style={[s.typeIcon, { color: typeColor[item.type] }]}>{typeIcon[item.type]}</Text>
            </View>
            <View style={s.itemBody}>
              <Text style={[s.itemTitle, { color: typeColor[item.type] }]}>{item.title}</Text>
              <Text style={s.itemText} numberOfLines={4}>{item.body}</Text>
              <Text style={s.itemTs}>{new Date(item.ts).toLocaleTimeString()}</Text>
            </View>
            {!item.read && <View style={[s.unreadDot, { backgroundColor: typeColor[item.type] }]} />}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: COLORS.bg },
  header:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  title:       { fontSize: 14, fontWeight: '900', color: COLORS.amber, letterSpacing: 6, fontFamily: 'monospace' },
  refresh:     { fontSize: 20, color: COLORS.cyan },
  empty:       { alignItems: 'center', paddingTop: 80 },
  emptyText:   { fontSize: 12, color: 'rgba(255,255,255,0.3)', letterSpacing: 4, fontFamily: 'monospace' },
  emptySubText:{ fontSize: 10, color: 'rgba(255,255,255,0.15)', marginTop: 8, fontFamily: 'monospace' },
  item:        { flexDirection: 'row', padding: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border, alignItems: 'flex-start', gap: 12 },
  itemUnread:  { backgroundColor: 'rgba(245,158,11,0.03)' },
  typeTag:     { width: 36, height: 36, borderRadius: 8, borderWidth: 1, justifyContent: 'center', alignItems: 'center', flexShrink: 0 },
  typeIcon:    { fontSize: 16 },
  itemBody:    { flex: 1 },
  itemTitle:   { fontSize: 12, fontWeight: '700', fontFamily: 'monospace', marginBottom: 3 },
  itemText:    { fontSize: 11, color: 'rgba(255,255,255,0.5)', fontFamily: 'monospace', lineHeight: 17 },
  itemTs:      { fontSize: 9, color: 'rgba(255,255,255,0.2)', fontFamily: 'monospace', marginTop: 4 },
  unreadDot:   { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
});
