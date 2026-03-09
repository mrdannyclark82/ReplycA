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
