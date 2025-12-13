const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 450,
        height: 700,
        resizable: false,
        icon: path.join(__dirname, '../assets/icon1.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
        backgroundColor: '#1e1e1e',
        autoHideMenuBar: true
    });

    const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../dist/index.html')}`;

    if (process.env.ELECTRON_START_URL) {
        mainWindow.loadURL(startUrl);
    } else {
        mainWindow.loadURL(startUrl);
    }

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('https:') || url.startsWith('http:')) {
            shell.openExternal(url);
        }
        return { action: 'deny' };
    });
}

ipcMain.handle('get-schools', async () => {
    return new Promise((resolve, reject) => {
        runPythonCommand('get_schools', null, resolve, reject);
    });
});

ipcMain.handle('start-verify', async (event, data) => {
    return new Promise((resolve, reject) => {
        runPythonCommand('verify', data, resolve, reject);
    });
});

ipcMain.handle('generate-docs', async (event, data) => {
    return new Promise((resolve, reject) => {
        runPythonCommand('generate_docs', data, resolve, reject);
    });
});

ipcMain.handle('select-file', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openFile'],
        filters: [{ name: 'Images', extensions: ['png'] }]
    });
    return result.filePaths[0];
});

ipcMain.handle('select-folder', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    return result.filePaths[0];
});

const fs = require('fs');

ipcMain.handle('get-config', async () => {
    const docsDir = path.join(app.getPath('documents'), 'RJ Verifier');
    if (!fs.existsSync(docsDir)) {
        try { fs.mkdirSync(docsDir, { recursive: true }); } catch (e) { console.error("Create dir failed", e); }
    }
    const configPath = path.join(docsDir, 'config.json');

    if (!fs.existsSync(configPath)) {
        return { socialLockDone: false, usageCount: 0 };
    }
    try {
        return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    } catch (e) {
        return { socialLockDone: false, usageCount: 0 };
    }
});

ipcMain.handle('set-config', async (event, newConfig) => {
    const docsDir = path.join(app.getPath('documents'), 'RJ Verifier');
    if (!fs.existsSync(docsDir)) {
        try { fs.mkdirSync(docsDir, { recursive: true }); } catch (e) { console.error("Create dir failed", e); }
    }
    const configPath = path.join(docsDir, 'config.json');
    fs.writeFileSync(configPath, JSON.stringify(newConfig, null, 2));
    return true;
});

function runPythonCommand(action, data, resolve, reject) {
    let cmd, args;

    if (app.isPackaged) {
        cmd = path.join(process.resourcesPath, 'engine/rj_engine.exe');
        const engineDir = path.join(process.resourcesPath, 'engine');
        args = ['--action', action, '--basedir', engineDir];
    } else {
        cmd = 'python';
        const scriptPath = path.join(__dirname, '../engine/main.py');
        args = [scriptPath, '--action', action];
    }

    if (data) {
        args.push('--data', JSON.stringify(data));
    }

    console.log(`Executing: ${cmd} ${args.join(' ')}`);

    const pyProcess = spawn(cmd, args);

    let outputData = '';
    let errorData = '';

    pyProcess.stdout.on('data', (chunk) => {
        const dataStr = chunk.toString();
        if (mainWindow && action !== 'get_schools') {
            dataStr.split(/\r?\n/).forEach(line => {
                if (line.trim()) mainWindow.webContents.send('log-update', line);
            });
        }
        outputData += dataStr;
    });

    pyProcess.stderr.on('data', (chunk) => {
        const dataStr = chunk.toString();
        // console.error(`Python Log: ${dataStr}`); // Optional: keep console noise down
        if (mainWindow) {
            dataStr.split(/\r?\n/).forEach(line => {
                if (line.trim()) {
                    console.error(`Python Log: ${line}`);
                    mainWindow.webContents.send('log-update', line);
                }
            });
        }
        errorData += dataStr;
    });

    pyProcess.on('close', (code) => {
        if (code !== 0) {
            reject(`Process exited with code ${code}: ${errorData}`);
        } else {
            try {
                const lines = outputData.trim().split('\n');
                const lastLine = lines[lines.length - 1];
                const result = JSON.parse(lastLine);
                resolve(result);
            } catch (e) {
                if (outputData.includes('"success": true')) {
                    const matches = outputData.match(/\{"success": true.*\}/);
                    if (matches) resolve(JSON.parse(matches[0]));
                    else resolve({ success: true, message: outputData });
                } else {
                    reject(`Failed to parse result: ${e.message}`);
                }
            }
        }
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
