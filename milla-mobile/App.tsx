import 'react-native-gesture-handler';
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, View } from 'react-native';
import VoiceChat from './src/screens/VoiceChat';
import HUD      from './src/screens/HUD';
import Feed     from './src/screens/Feed';
import { COLORS } from './src/config';

const Tab = createBottomTabNavigator();

const TabIcon = ({ icon, color }: { icon: string; color: string }) => (
  <Text style={{ fontSize: 18, color }}>{icon}</Text>
);

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" backgroundColor={COLORS.bg} />
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: 'rgba(3,7,18,0.97)',
            borderTopColor: 'rgba(255,255,255,0.06)',
            borderTopWidth: 1,
            paddingBottom: 4,
            height: 60,
          },
          tabBarActiveTintColor:   COLORS.amber,
          tabBarInactiveTintColor: 'rgba(255,255,255,0.25)',
          tabBarLabelStyle: { fontSize: 9, letterSpacing: 2, fontFamily: 'monospace' },
        }}
      >
        <Tab.Screen name="VOICE" component={VoiceChat}
          options={{ tabBarIcon: ({ color }) => <TabIcon icon="◎" color={color} /> }} />
        <Tab.Screen name="HUD" component={HUD}
          options={{ tabBarIcon: ({ color }) => <TabIcon icon="⬡" color={color} /> }} />
        <Tab.Screen name="FEED" component={Feed}
          options={{ tabBarIcon: ({ color }) => <TabIcon icon="⚡" color={color} /> }} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
