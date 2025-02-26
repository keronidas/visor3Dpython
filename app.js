const { app, BrowserWindow } = require('electron');
require('child_process');



// Crea la ventana de Electron
function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        title: "Flask Camera",
        webPreferences: {
            nodeIntegration: true
        },
    });

    // Carga la URL de la aplicación Flask en Electron
    win.loadURL('http://127.0.0.1:5000');
    win.maximize();
}

app.whenReady().then(() => {
    createWindow(); // Crea la ventana de Electron

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
