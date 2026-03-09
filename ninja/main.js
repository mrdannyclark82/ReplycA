const { app, BrowserWindow, session, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      partition: 'persist:private',
      webviewTag: true  // Enable webview tag
    }
  });

  applyPrivacySettings();
  
  mainWindow.loadFile('index.html');
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
    'facebook.net', 'twitter.com', 'linkedin.com'
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
