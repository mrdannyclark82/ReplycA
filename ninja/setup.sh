#!/bin/bash

# setup.sh - One-shot privacy browser setup script

echo "🚀 Setting up Privacy Browser..."

# Create package.json
cat > package.json << 'EOF'
{
  "name": "ninja",
  "version": "1.0.0",
  "description": "A privacy-focused web browser",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "dev": "electron . --dev"
  },
  "dependencies": {
    "electron": "^latest"
  }
}
EOF

# Create main.js
cat > main.js << 'EOF'
const { app, BrowserWindow, session } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      partition: 'persist:private'
    }
  });

  applyPrivacySettings();
  
  mainWindow.loadURL('https://duckduckgo.com');
  mainWindow.setMenuBarVisibility(false);
}

function applyPrivacySettings() {
  const ses = session.fromPartition('persist:private');
  
  // Clear existing cookies
  ses.cookies.get({}).then(cookies => {
    cookies.forEach(cookie => {
      ses.cookies.remove(cookie.url, cookie.name);
    });
  });
  
  // Block tracking requests
  ses.webRequest.onBeforeRequest((details, callback) => {
    const shouldBlock = shouldBlockRequest(details);
    callback({ cancel: shouldBlock });
  });

  // Remove tracking headers
  ses.webRequest.onBeforeSendHeaders((details, callback) => {
    const { requestHeaders } = details;
    delete requestHeaders['Referer'];
    delete requestHeaders['Origin'];
    delete requestHeaders['User-Agent'];
    callback({ requestHeaders });
  });

  // Block tracking responses
  ses.webRequest.onHeadersReceived((details, callback) => {
    const { responseHeaders } = details;
    if (responseHeaders) {
      Object.keys(responseHeaders).forEach(header => {
        if (header.toLowerCase() === 'set-cookie') {
          delete responseHeaders[header];
        }
      });
    }
    callback({ responseHeaders });
  });
}

function shouldBlockRequest(details) {
  const url = details.url.toLowerCase();
  const blockedPatterns = [
    'doubleclick.net', 'google-analytics.com', 'facebook.com/tr',
    'googletagmanager.com', 'hotjar.com', 'mixpanel.com',
    'scorecardresearch.com', 'quantserve.com', 'adservice.google.com',
    'facebook.net', 'twitter.com', 'linkedin.com', 'youtube.com',
    'googlesyndication.com', '2mdn.net', 'admob.com', 'adsense.com'
  ];
  return blockedPatterns.some(pattern => url.includes(pattern));
}

app.whenReady().then(createWindow);

app.on('web-contents-created', (event, contents) => {
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    if (!['https:', 'http:'].includes(parsedUrl.protocol)) {
      event.preventDefault();
    }
  });

  contents.setWindowOpenHandler(({ url }) => {
    return { action: 'deny' };
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  session.fromPartition('persist:private').clearStorageData();
});
EOF

# Create preload.js
cat > preload.js << 'EOF'
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('privacyAPI', {
    getVersion: () => process.versions.electron
});

// Anti-fingerprinting measures
try {
    delete navigator.__proto__.webdriver;
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
} catch (e) {
    // Silently fail
}
EOF

# Create index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔒 Privacy Browser</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 0;
            font-family: system-ui, -apple-system, sans-serif;
            background: #121212; color: #e0e0e0;
        }
        #browser-container { display: flex; flex-direction: column; height: 100vh; }
        #toolbar {
            background: #1e1e1e; padding: 12px; display: flex; gap: 12px;
            border-bottom: 1px solid #333;
        }
        #url-bar {
            flex: 1; padding: 10px 15px; border-radius: 24px;
            border: 1px solid #444; background: #2d2d2d; color: white;
            font-size: 14px;
        }
        button {
            background: #333; color: white; border: none; 
            padding: 10px 20px; border-radius: 20px; cursor: pointer;
            font-weight: 500; transition: background 0.2s;
        }
        button:hover { background: #444; }
        #webview-container { flex: 1; display: flex; }
        webview { flex: 1; }
    </style>
</head>
<body>
    <div id="browser-container">
        <div id="toolbar">
            <button id="back">← Back</button>
            <button id="forward">Forward →</button>
            <button id="refresh">🔄 Refresh</button>
            <input type="text" id="url-bar" placeholder="Enter website URL...">
            <button id="go">Go</button>
        </div>
        <div id="webview-container">
            <webview 
                id="webview" 
                src="https://duckduckgo.com" 
                partition="persist:private"
                allowpopups>
            </webview>
        </div>
    </div>

    <script>
        const webview = document.getElementById('webview');
        const urlBar = document.getElementById('url-bar');
        const backBtn = document.getElementById('back');
        const forwardBtn = document.getElementById('forward');
        const refreshBtn = document.getElementById('refresh');
        const goBtn = document.getElementById('go');

        // Navigation controls
        backBtn.addEventListener('click', () => webview.goBack());
        forwardBtn.addEventListener('click', () => webview.goForward());
        refreshBtn.addEventListener('click', () => webview.reload());

        // URL handling
        goBtn.addEventListener('click', () => {
            let url = urlBar.value.trim();
            if (url && !url.match(/^https?:\/\//)) {
                url = 'https://' + url;
            }
            if (url) webview.src = url;
        });

        // Enter key support
        urlBar.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') goBtn.click();
        });

        // Update URL bar
        webview.addEventListener('did-navigate', (event) => {
            urlBar.value = event.url;
        });

        // Error handling
        webview.addEventListener('did-fail-load', (event) => {
            if (event.errorCode !== -3) {
                console.warn('Navigation failed:', event.errorDescription);
            }
        });

        // Block popups
        webview.addEventListener('new-window', (event) => {
            event.preventDefault();
        });
    </script>
</body>
</html>
EOF

# Make script executable and install dependencies
echo "📦 Installing dependencies..."
npm install

# Create run script
cat > run.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Privacy Browser..."
npm start
EOF

chmod +x run.sh

echo "✅ Privacy Browser setup complete!"
echo ""
echo "To run your browser:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  cd ninja"
echo "  npm start"
echo ""
echo "Features included:"
echo "  • Blocks 15+ tracking domains"
echo "  • Removes tracking headers"
echo "  • Blocks third-party cookies"
echo "  • Prevents popups"
echo "  • Private browsing mode"
echo "  • DuckDuckGo default search"
