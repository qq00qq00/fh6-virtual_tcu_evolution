/**
 * Preload for settings and dashboard windows.
 * Exposes `window.tcu` for native actions (HUD, open dashboard, updates).
 */

import { contextBridge, ipcRenderer } from 'electron'

export interface UpdaterCheckResult {
  ok: boolean
  info?: { version?: string; releaseDate?: string; releaseNotes?: unknown } | null
  currentVersion?: string
  error?: string
}

export interface UpdaterStatus {
  kind: 'checking' | 'available' | 'not-available' | 'progress' | 'downloaded' | 'error'
  info?: {
    version?: string
    releaseNotes?: unknown
    percent?: number
    transferred?: number
    total?: number
  }
  error?: string
}

export interface UpdaterDownloadResult {
  ok: boolean
  error?: string
}

export interface IpcActionResult {
  ok: boolean
  error?: string
}

const api = {
  toggleHud: () => ipcRenderer.invoke('hud:toggle'),
  closeHud: () => ipcRenderer.invoke('hud:close'),
  openDashboard: () => ipcRenderer.invoke('app:open-dashboard'),
  openExternal: (url: string): Promise<IpcActionResult> =>
    ipcRenderer.invoke('app:open-external', url),
  openSettings: () => ipcRenderer.invoke('app:open-settings'),
  setLocale: (locale: string): Promise<void> => ipcRenderer.invoke('app:set-locale', locale),
  checkForUpdates: (): Promise<UpdaterCheckResult> => ipcRenderer.invoke('updater:check'),
  downloadUpdate: (): Promise<UpdaterDownloadResult> => ipcRenderer.invoke('updater:download'),
  quitAndInstallUpdate: () => ipcRenderer.invoke('updater:quit-and-install'),
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('app:get-version'),
  getBackendInfo: () => ipcRenderer.invoke('app:get-backend-info'),
  restartBackend: () => ipcRenderer.invoke('app:restart-backend'),
  onBackendReady: (cb: (info: { wsUrl?: string; url?: string; ready?: boolean }) => void) => {
    const listener = (_: unknown, info: { wsUrl?: string; url?: string; ready?: boolean }) =>
      cb(info)
    ipcRenderer.on('backend:ready', listener)
    return () => ipcRenderer.removeListener('backend:ready', listener)
  },
  onUpdaterStatus: (cb: (status: UpdaterStatus) => void) => {
    const listener = (_: unknown, status: UpdaterStatus) => cb(status)
    ipcRenderer.on('updater:status', listener)
    return () => ipcRenderer.removeListener('updater:status', listener)
  },
  onBackendExit: (cb: (info: unknown) => void) => {
    const listener = (_: unknown, info: unknown) => cb(info)
    ipcRenderer.on('backend:exit', listener)
    return () => ipcRenderer.removeListener('backend:exit', listener)
  },
}

try {
  contextBridge.exposeInMainWorld('tcu', api)
  contextBridge.exposeInMainWorld('isElectron', true)
} catch (err) {
  console.error('[preload/main] expose failed:', err)
}

export type TcuMainApi = typeof api
