import type { AppLocale } from '@virtual-tcu/shared/i18n'
import en from '@virtual-tcu/shared/locales/en'
import zhCN from '@virtual-tcu/shared/locales/zh-CN'
import { app } from 'electron'

let locale: AppLocale = detectTrayLocale()

export function detectTrayLocale(): AppLocale {
  const sys = app.getLocale().toLowerCase()
  return sys.startsWith('zh') ? 'zh-CN' : 'en'
}

export function setTrayLocale(next: AppLocale) {
  locale = next
}

export function getTrayLocale(): AppLocale {
  return locale
}

export function getTrayLabels() {
  const m = locale === 'zh-CN' ? zhCN : en
  return {
    tooltip: m.app.title,
    settings: m.electronApp.trayMenu.settings,
    openDashboard: m.electronApp.openDashboard,
    toggleHud: m.electronApp.toggleHud,
    restartBackend: m.electronApp.trayMenu.restartBackend,
    quit: m.electronApp.trayMenu.quit,
  }
}
