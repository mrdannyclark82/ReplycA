import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/axiom-rayne/',
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: null,
      includeAssets: ['icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Axiom-Rayne',
        short_name: 'Axiom',
        description: 'M.I.L.L.A. R.A.Y.N.E. — Axiom Neural Interface',
        theme_color: '#f59e0b',
        background_color: '#030712',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/axiom-rayne/',
        scope: '/axiom-rayne/',
        categories: ['productivity', 'utilities'],
        icons: [
          { src: '/axiom-rayne/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: '/axiom-rayne/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
        shortcuts: [
          { name: 'Voice Chat', url: '/axiom-rayne/', description: 'Talk to Milla', icons: [{ src: '/axiom-rayne/icon-192.png', sizes: '192x192' }] },
        ],
      },
      workbox: {
        skipWaiting: true,
        clientsClaim: true,
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        navigateFallback: '/axiom-rayne/index.html',
        navigateFallbackDenylist: [/^\/api/, /^\/ws/],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache', expiration: { maxEntries: 50, maxAgeSeconds: 300 } },
          },
        ],
      },
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 5175,
    proxy: {
      '/api': 'http://localhost:5000',
      '/ws': {
        target: 'ws://localhost:5000',
        ws: true,
      },
    },
  },
})
