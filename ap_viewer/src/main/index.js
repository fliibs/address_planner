import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
const fs = require('fs')
const { Menu } = require("electron");

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: false,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }

  })
  // 1. 引入Electron中的Menu模块

  // 2. 创建一个菜单数组
  let menuTemplate = [
    // 一级菜单
    {
      label: "file",
      // 二级菜单 submenu
      submenu: [
        {
          label: "open json",
          click:function(){
            dialog.showOpenDialog({
              filters: [
                { name: 'Json', extensions: ['json'] },
                { name: 'All Files', extensions: ['*'] }
              ],
              properties: ['openFile']
            })
              .then(result => {
                const data_json = fs.readFileSync(result.filePaths[0], "utf-8");
                const data = JSON.parse(data_json);
                mainWindow.webContents.send('update-data', data);
                // console.log(data);
              }).catch(err => {
                console.log(err);
              })
          }
          
        },
       
      ]
    },
  ];

  

  // ipcMain.on('read-json', (event, val) => {
  //   console.log(val)
  //   dialog.showOpenDialog({
  //     filters: [
  //       { name: 'Json', extensions: ['json'] },
  //       { name: 'All Files', extensions: ['*'] }
  //     ],
  //     properties: ['openFile']
  //   })
  //     .then(result => {
  //       const data_json = fs.readFileSync(result.filePaths[0], "utf-8");
  //       const data = JSON.parse(data_json);
  //       mainWindow.webContents.send('update-data', data);
  //       // console.log(data);
  //     }).catch(err => {
  //       console.log(err);
  //     })
  // })


  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
    let menuBuilder = Menu.buildFromTemplate(menuTemplate);
    Menu.setApplicationMenu(menuBuilder);
  })


  // mainWindow.webContents.setWindowOpenHandler((details) => {
  //   shell.openExternal(details.url)
  //   return { action: 'deny' }
  // })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.
