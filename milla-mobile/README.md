# Nexus Kingdom — Mobile App

Expo React Native companion for M.I.L.L.A. R.A.Y.N.E.

## Quick Start

```bash
cd ogdray/milla-mobile
npx expo start                    # dev server + QR code
npx expo start --tunnel           # if phone is not on same LAN (uses Tailscale instead)
```

Scan the QR code with **Expo Go** (Android/iOS) — instant live reload.

## Screens

| Tab | Icon | What it does |
|-----|------|-------------|
| VOICE | ◎ | Hold-to-talk mic orb · voice chat with Milla · live neuro strip |
| HUD   | ⬡ | Biometric lock · neuro chemical bars · system node status · quick actions |
| FEED  | ⚡ | Push notification inbox · Milla activity feed · cron results |

## Connection

The app connects to the backend over **Tailscale**:

```
Server:  http://100.89.122.112:8000
WebSocket neuro stream:  ws://100.89.122.112:8000/ws/neuro
WebSocket voice:         ws://100.89.122.112:8000/ws/voice
```

To change the server URL: edit `milla-mobile/.env`

```
EXPO_PUBLIC_SERVER_URL=http://100.89.122.112:8000
```

## Build Standalone APK

```bash
npm install -g eas-cli
npx eas login
npx eas build --platform android --profile preview
```

This produces a `.apk` you can sideload without the Play Store.

## Voice Protocol

- **Input**: Hold mic button → raw PCM bytes (16kHz, mono, S16LE) streamed to `/ws/voice`
- **Output**: Server responds with JSON frames (transcript, Milla reply) + binary MP3 (TTS audio)
- **Text fallback**: Type in text input field → bypasses STT

## Push Notifications

Token auto-registers on app open via `POST /api/devices/register`.  
Milla sends pushes via `POST /api/notify` on the backend.
