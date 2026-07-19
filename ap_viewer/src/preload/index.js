const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  onUpdateData: (callback) => ipcRenderer.on('update-data', callback),
  // readJson: (val) => ipcRenderer.send('read-json', val)
})
