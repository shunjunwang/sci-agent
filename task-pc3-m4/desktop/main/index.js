// PC3 M4 Electron 主进程
const { app, BrowserWindow, Menu, Tray, ipcMain, shell } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow = null;
let tray = null;

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'SciAgent',
    icon: path.join(__dirname, '../resources/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../preload/index.js')
    },
    show: false
  });

  // 加载前端页面
  const startUrl = isDev 
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../../frontend/out/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // 开发工具
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // 窗口事件
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 创建应用菜单
  createMenu();
}

// 创建应用菜单
function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '新建项目',
          accelerator: 'CmdOrCtrl+N',
          click: () => mainWindow.webContents.send('menu-new-project')
        },
        { type: 'separator' },
        {
          label: '打开文件',
          accelerator: 'CmdOrCtrl+O',
          click: () => mainWindow.webContents.send('menu-open-file')
        },
        {
          label: '保存',
          accelerator: 'CmdOrCtrl+S',
          click: () => mainWindow.webContents.send('menu-save')
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'front' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '文档',
          click: () => shell.openExternal('https://docs.sciagent.com')
        },
        {
          label: 'GitHub',
          click: () => shell.openExternal('https://github.com/sciagent')
        },
        { type: 'separator' },
        {
          label: '关于 SciAgent',
          click: () => mainWindow.webContents.send('menu-about')
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// 创建系统托盘
function createTray() {
  const iconPath = path.join(__dirname, '../resources/tray-icon.png');
  tray = new Tray(iconPath);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '打开 SciAgent',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        }
      }
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => app.quit()
    }
  ]);

  tray.setToolTip('SciAgent 桌面应用');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.show();
    }
  });
}

// IPC 通信处理
function setupIPC() {
  // 文件系统访问
  ipcMain.handle('read-file', async (event, filePath) => {
    const fs = require('fs').promises;
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      return { success: true, content };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('write-file', async (event, filePath, content) => {
    const fs = require('fs').promises;
    try {
      await fs.writeFile(filePath, content, 'utf-8');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // 打开外部链接
  ipcMain.on('open-external', (event, url) => {
    shell.openExternal(url);
  });
}

// 应用生命周期
app.whenReady().then(() => {
  createWindow();
  createTray();
  setupIPC();

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

// 单实例锁
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}