// PC3 M4 Electron 预加载脚本
// 提供安全的 IPC 通信桥梁

const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 文件系统操作
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  
  // 外部链接
  openExternal: (url) => ipcRenderer.send('open-external', url),
  
  // 菜单事件监听
  onMenuNewProject: (callback) => ipcRenderer.on('menu-new-project', callback),
  onMenuOpenFile: (callback) => ipcRenderer.on('menu-open-file', callback),
  onMenuSave: (callback) => ipcRenderer.on('menu-save', callback),
  onMenuAbout: (callback) => ipcRenderer.on('menu-about', callback),
  
  // 平台信息
  platform: process.platform,
  isElectron: true
});