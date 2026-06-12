/**
 * Electron main process for Virtual TCU.
 *
 * Responsibilities:
 *   - Spawn the bundled Python backend (VirtualTCU.exe --backend-only) and
 *     manage its lifecycle (start, restart, kill on quit).
 *   - Wait for HTTP health or a READY stdout marker, then expose endpoints to
 *     the settings window and HUD.
 *   - Open the read-only dashboard in the user's default browser
 *     (http://127.0.0.1:8765) when requested.
 *   - Create an optional always-on-top frameless HUD window that connects to
 *     the same WebSocket.
 *   - Wire up auto-update via electron-updater + GitHub Releases.
 */

import { join } from 'node:path'
import { electronApp, is, optimizer } from '@electron-toolkit/utils'
import { app, BrowserWindow, ipcMain, Menu, nativeImage, nativeTheme, shell, Tray } from 'electron'
import { autoUpdater } from 'electron-updater'
import { BackendLifecycle } from './backend-lifecycle'
import { detectTrayLocale, getTrayLabels, setTrayLocale } from './tray-i18n'
import { openExternalUrl } from './url-policy'

const backendLifecycle = new BackendLifecycle()

/** Matches packages/ui theme (--color-tcu-bg-0 / bodyColor). */
const SETTINGS_WINDOW_BG = '#030712'
const SETTINGS_TITLE_SYMBOL = '#f1f5f9'

let settingsWindow: BrowserWindow | null = null
let hudWindow: BrowserWindow | null = null
let tray: Tray | null = null
let isQuitting = false
let isBackendKilled = false

backendLifecycle.setOnReady(() => broadcastBackendReady())
backendLifecycle.setOnExit((code, signal) => {
  settingsWindow?.webContents.send('backend:exit', { code, signal })
  hudWindow?.webContents.send('backend:exit', { code, signal })
})

// ----- Windows ---------------------------------------------------------------

function settingsPagePath(): string {
  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    return `${process.env.ELECTRON_RENDERER_URL}/settings-renderer/index.html`
  }
  return join(__dirname, '..', 'renderer', 'settings-renderer', 'index.html')
}

function hudPagePath(): string {
  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    return `${process.env.ELECTRON_RENDERER_URL}/hud-renderer/index.html`
  }
  return join(__dirname, '..', 'renderer', 'hud-renderer', 'index.html')
}

function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.show()
    settingsWindow.focus()
    return
  }

  settingsWindow = new BrowserWindow({
    width: 1100,
    height: 760,
    minWidth: 880,
    minHeight: 600,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: SETTINGS_WINDOW_BG,
    title: 'Virtual TCU',
    ...(process.platform === 'win32'
      ? {
          titleBarOverlay: {
            color: SETTINGS_WINDOW_BG,
            symbolColor: SETTINGS_TITLE_SYMBOL,
            height: 40,
          },
        }
      : {}),
    webPreferences: {
      preload: join(__dirname, '..', 'preload', 'main.js'),
      sandbox: true,
      backgroundThrottling: false,
    },
  })

  settingsWindow.on('ready-to-show', () => {
    settingsWindow?.show()
  })

  settingsWindow.on('close', (e) => {
    if (!isQuitting) {
      e.preventDefault()
      settingsWindow?.hide()
    }
  })

  settingsWindow.on('closed', () => {
    settingsWindow = null
  })

  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    settingsWindow.loadURL(settingsPagePath())
  } else {
    settingsWindow.loadFile(settingsPagePath())
  }

  settingsWindow.webContents.on('did-finish-load', () => {
    if (backendLifecycle.isReady()) broadcastBackendReady()
  })

  // Retry on network errors (backend restart, Vite dev server restart, etc.)
  // so the window doesn't permanently land on a chrome-error:// page.
  let _loadRetries = 0
  const MAX_RETRIES = 10
  const RETRY_DELAY_MS = 2000

  settingsWindow.webContents.on(
    'did-fail-load',
    (_e, errorCode, _desc, validatedURL, isMainFrame) => {
      if (!isMainFrame) return
      // Only retry on transient network errors — not on file-not-found, etc.
      // -102 = CONNECTION_REFUSED, -105 = NAME_NOT_RESOLVED,
      // -106 = INTERNET_DISCONNECTED, -118 = CONNECTION_TIMED_OUT
      if (![-102, -105, -106, -118].includes(errorCode)) return
      if (_loadRetries >= MAX_RETRIES) return

      _loadRetries++
      console.warn(`[settings] load failed (${errorCode}), retry ${_loadRetries}/${MAX_RETRIES}…`)
      setTimeout(() => {
        if (settingsWindow && !settingsWindow.isDestroyed()) {
          if (is.dev && process.env.ELECTRON_RENDERER_URL) {
            settingsWindow.loadURL(settingsPagePath())
          } else {
            settingsWindow.loadFile(settingsPagePath())
          }
        }
      }, RETRY_DELAY_MS)
    },
  )
}

function broadcastBackendReady() {
  const endpoints = backendLifecycle.getEndpoints()
  const payload = {
    url: endpoints.url,
    wsUrl: endpoints.wsUrl,
    lanUrl: endpoints.lanUrl,
    ready: true,
  }
  settingsWindow?.webContents.send('backend:ready', payload)
  hudWindow?.webContents.send('backend:ready', payload)
}

function openDashboardInBrowser() {
  backendLifecycle.refreshEndpoints()
  const { url } = backendLifecycle.getEndpoints()
  shell.openExternal(url).catch((err) => {
    console.warn('[app] open dashboard failed:', err)
  })
}

function createHudWindow() {
  if (hudWindow) {
    hudWindow.show()
    hudWindow.focus()
    return
  }

  hudWindow = new BrowserWindow({
    width: 340,
    height: 280,
    minWidth: 240,
    minHeight: 120,
    x: 24,
    y: 24,
    show: false,
    frame: false,
    transparent: true,
    resizable: true,
    movable: true,
    skipTaskbar: true,
    alwaysOnTop: true,
    hasShadow: false,
    fullscreenable: false,
    minimizable: false,
    maximizable: false,
    backgroundColor: '#00000000',
    ...(process.platform === 'win32' ? { thickFrame: false, roundedCorners: false as const } : {}),
    webPreferences: {
      preload: join(__dirname, '..', 'preload', 'hud.js'),
      sandbox: true,
      backgroundThrottling: false,
    },
  })

  hudWindow.setBackgroundColor('#00000000')

  hudWindow.setAlwaysOnTop(true, 'screen-saver')
  hudWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true })

  hudWindow.on('ready-to-show', () => {
    hudWindow?.show()
  })

  hudWindow.on('closed', () => {
    hudWindow = null
  })

  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    hudWindow.loadURL(hudPagePath())
  } else {
    hudWindow.loadFile(hudPagePath())
  }
}

// ----- Tray ------------------------------------------------------------------

function buildTrayMenu() {
  const labels = getTrayLabels()
  return Menu.buildFromTemplate([
    { label: labels.settings, click: () => createSettingsWindow() },
    { label: labels.openDashboard, click: () => openDashboardInBrowser() },
    {
      label: labels.toggleHud,
      click: () => {
        if (hudWindow && hudWindow.isVisible()) hudWindow.hide()
        else createHudWindow()
      },
    },
    { type: 'separator' },
    {
      label: labels.restartBackend,
      click: () => {
        void backendLifecycle.restart().catch((err) => {
          console.error('[backend] restart failed:', err)
        })
      },
    },
    { type: 'separator' },
    {
      label: labels.quit,
      click: () => {
        isQuitting = true
        app.quit()
      },
    },
  ])
}

function rebuildTrayMenu() {
  if (!tray) return
  const labels = getTrayLabels()
  tray.setToolTip(labels.tooltip)
  tray.setContextMenu(buildTrayMenu())
}

function createTray() {
  const iconPath = app.isPackaged
    ? join(process.resourcesPath, 'icon.ico')
    : join(__dirname, '..', '..', 'build', 'icon.ico')
  const icon = nativeImage.createFromPath(iconPath)
  setTrayLocale(detectTrayLocale())
  tray = new Tray(icon)
  rebuildTrayMenu()
  tray.on('click', () => {
    createSettingsWindow()
  })
}

function prepareForQuit(): void {
  isQuitting = true
  backendLifecycle.setQuitting(true)
  tray?.destroy()
  tray = null
  if (settingsWindow && !settingsWindow.isDestroyed()) {
    settingsWindow.removeAllListeners('close')
    settingsWindow.destroy()
    settingsWindow = null
  }
  if (hudWindow && !hudWindow.isDestroyed()) {
    hudWindow.destroy()
    hudWindow = null
  }
}

// ----- IPC -------------------------------------------------------------------

function registerIpc() {
  ipcMain.handle('app:get-backend-info', () => {
    const endpoints = backendLifecycle.getEndpoints()
    return {
      url: endpoints.url,
      wsUrl: endpoints.wsUrl,
      lanUrl: endpoints.lanUrl,
      ready: backendLifecycle.isReady(),
    }
  })

  ipcMain.handle('app:open-dashboard', () => {
    openDashboardInBrowser()
  })

  ipcMain.handle('app:open-external', (_e, url: unknown) => {
    if (typeof url !== 'string') return { ok: false, error: 'Invalid URL' }
    return openExternalUrl(url)
  })

  ipcMain.handle('app:open-settings', () => {
    createSettingsWindow()
  })

  ipcMain.handle('app:set-locale', (_e, value: unknown) => {
    if (value !== 'en' && value !== 'zh-CN') return
    setTrayLocale(value)
    rebuildTrayMenu()
  })

  ipcMain.handle('hud:toggle', () => {
    if (hudWindow && hudWindow.isVisible()) hudWindow.hide()
    else createHudWindow()
  })

  ipcMain.handle('hud:close', () => {
    hudWindow?.close()
    hudWindow = null
  })

  ipcMain.handle('hud:set-ignore-mouse', (_e, ignore: boolean) => {
    hudWindow?.setIgnoreMouseEvents(ignore, { forward: true })
  })

  ipcMain.handle('hud:set-size', (_e, width: unknown, height: unknown) => {
    if (!hudWindow || hudWindow.isDestroyed()) return
    const w = Math.round(Number(width))
    const h = Math.round(Number(height))
    if (!Number.isFinite(w) || !Number.isFinite(h) || w < 1 || h < 1) return
    const [curW, curH] = hudWindow.getSize()
    if (curW === w && curH === h) return
    hudWindow.setSize(w, h, false)
  })

  ipcMain.handle('app:restart-backend', () => backendLifecycle.restart())

  ipcMain.handle('updater:check', async () => {
    if (!app.isPackaged) {
      return {
        ok: false,
        error: 'Auto-update is only available in packaged builds',
        currentVersion: app.getVersion(),
      }
    }
    try {
      const r = await autoUpdater.checkForUpdates()
      return {
        ok: true,
        info: r?.updateInfo ?? null,
        currentVersion: app.getVersion(),
      }
    } catch (err) {
      return {
        ok: false,
        error: (err as Error).message,
        currentVersion: app.getVersion(),
      }
    }
  })

  ipcMain.handle('updater:download', async () => {
    if (!app.isPackaged) {
      return { ok: false, error: 'Auto-update is only available in packaged builds' }
    }
    try {
      await autoUpdater.downloadUpdate()
      return { ok: true }
    } catch (err) {
      return {
        ok: false,
        error: (err as Error).message,
      }
    }
  })

  ipcMain.handle('updater:quit-and-install', () => {
    autoUpdater.quitAndInstall()
  })

  ipcMain.handle('app:get-version', () => app.getVersion())
}

// ----- Auto-update -----------------------------------------------------------

function broadcastUpdater(payload: { kind: string; info?: unknown; error?: string }) {
  settingsWindow?.webContents.send('updater:status', payload)
}

function setupAutoUpdater() {
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'qq00qq00',
    repo: 'fh6-virtual_tcu_evolution',
  })
  autoUpdater.autoDownload = false
  autoUpdater.autoInstallOnAppQuit = true

  autoUpdater.on('checking-for-update', () => {
    broadcastUpdater({ kind: 'checking' })
  })
  autoUpdater.on('update-not-available', (info) => {
    broadcastUpdater({ kind: 'not-available', info })
  })
  autoUpdater.on('error', (err) => {
    console.warn('[updater]', err.message)
    broadcastUpdater({ kind: 'error', error: err.message })
  })
  autoUpdater.on('update-available', (info) => {
    console.log('[updater] update available:', info.version)
    broadcastUpdater({ kind: 'available', info })
  })
  autoUpdater.on('download-progress', (progress) => {
    broadcastUpdater({ kind: 'progress', info: progress })
  })
  autoUpdater.on('update-downloaded', (info) => {
    console.log('[updater] update downloaded:', info.version)
    broadcastUpdater({ kind: 'downloaded', info })
  })

  if (app.isPackaged) {
    setTimeout(() => {
      autoUpdater.checkForUpdates().catch(() => {})
    }, 8_000)
  }
}

// ----- Lifecycle -------------------------------------------------------------

const gotLock = app.requestSingleInstanceLock()
if (!gotLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    createSettingsWindow()
  })

  app.whenReady().then(async () => {
    electronApp.setAppUserModelId('com.virtualtcu.app')
    nativeTheme.themeSource = 'dark'
    app.on('browser-window-created', (_, w) => optimizer.watchWindowShortcuts(w))

    registerIpc()
    createTray()

    try {
      await backendLifecycle.start()
    } catch (err) {
      console.error('Backend failed to start:', err)
    }

    createSettingsWindow()
    setupAutoUpdater()

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createSettingsWindow()
    })
  })
}

app.on('before-quit', (e) => {
  if (!isBackendKilled) {
    e.preventDefault()
    prepareForQuit()
    void backendLifecycle.forceStop().finally(() => {
      isBackendKilled = true
      app.quit()
    })
  }
})

app.on('window-all-closed', () => {
  // Stay alive in tray on Windows; explicit quit happens via tray menu.
  if (process.platform !== 'win32') {
    isQuitting = true
    backendLifecycle.setQuitting(true)
    tray?.destroy()
    tray = null
    app.quit()
  }
})
