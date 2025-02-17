const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Inicia el servidor Flask
const startFlaskServer = () => {
    const flaskApp = spawn('python', ['app/app.py']);
    flaskApp.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });
    flaskApp.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
    });
};

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
    startFlaskServer();
    createWindow();

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
