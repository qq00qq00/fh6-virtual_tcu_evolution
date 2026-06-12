import type { HudTemplateId } from '@virtual-tcu/shared/config/hud'
import type { TelemetrySnapshot } from '@virtual-tcu/shared/types/telemetry'
import type { DriveMode } from '@virtual-tcu/shared/types/ws'
import { normalizeHudTemplate } from '@virtual-tcu/shared/config/hud'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useHudClickThrough } from './hud-click-through'
import { useHudView } from './hud-view'
import { useHudWindowSync } from './hud-window-sync'

export function useHudApp() {
  const connected = ref(false)
  const live = ref(false)
  const mode = ref<DriveMode>('COMFORT')
  const telemetry = ref<Partial<TelemetrySnapshot>>({})
  const clickThrough = ref(false)
  const hudTemplate = ref<HudTemplateId>('classic')

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let cleanupBackendExit: (() => void) | null = null
  let cleanupBackendReady: (() => void) | null = null
  let mouseEventsIgnored = false

  const tcuState = computed(() => telemetry.value.tcu_state ?? 'STANDBY')

  const view = useHudView(telemetry, mode, tcuState, clickThrough)

  const shellClass = computed(() => `tpl-${hudTemplate.value}-shell`)

  function applyConfig(config: Record<string, unknown> | undefined) {
    if (!config) return
    if ('hud_template' in config) {
      hudTemplate.value = normalizeHudTemplate(config.hud_template)
    }
  }

  async function connectWs() {
    const fallbackUrl = 'ws://127.0.0.1:8765/ws'
    let url = fallbackUrl
    try {
      if (window.hud) {
        const info = await window.hud.getBackendInfo()
        url = info.wsUrl || fallbackUrl
      }
    } catch {
      // use fallback
    }

    if (ws) {
      ws.close()
      ws = null
    }

    try {
      ws = new WebSocket(url)
    } catch (err) {
      console.warn('[hud] WS construct failed', err)
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      connected.value = true
    }
    ws.onclose = () => {
      connected.value = false
      live.value = false
      scheduleReconnect()
    }
    ws.onerror = () => {
      ws?.close()
    }
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data as string)
        switch (msg.type) {
          case 'init':
            if (msg.data?.mode) mode.value = msg.data.mode
            if (typeof msg.data?.live === 'boolean') live.value = msg.data.live
            applyConfig(msg.data?.config)
            break
          case 'telemetry':
            telemetry.value = msg.data ?? {}
            break
          case 'state':
            if (msg.data?.mode) mode.value = msg.data.mode
            if (typeof msg.data?.live === 'boolean') live.value = msg.data.live
            break
          case 'config_update':
            applyConfig(msg.data)
            break
        }
      } catch {
        /* ignore */
      }
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connectWs()
    }, 1500)
  }

  function close() {
    window.hud?.close()
  }

  function applyMouseIgnore(ignore: boolean) {
    if (mouseEventsIgnored === ignore) return
    mouseEventsIgnored = ignore
    window.hud?.setIgnoreMouse(ignore)
  }

  const { syncFromPointer } = useHudClickThrough(clickThrough, applyMouseIgnore)

  function syncClickThroughMouse(e: MouseEvent) {
    syncFromPointer(e)
  }

  function toggleClickThrough(e: MouseEvent) {
    clickThrough.value = !clickThrough.value
    syncFromPointer(e)
  }

  const hudProps = computed(() => ({
    mode: mode.value,
    modeColor: view.modeColor.value,
    tcuState: tcuState.value,
    clickThrough: clickThrough.value,
    connected: connected.value,
    live: live.value,
    gearLabel: view.gearLabel.value,
    gearStyle: view.gearStyle.value,
    speed: view.speed.value,
    rpm: view.rpm.value,
    rpmMax: view.rpmMax.value,
    rpmPct: view.rpmPct.value,
    rpmBarColor: view.rpmBarColor.value,
    throttle: view.throttle.value,
    brake: view.brake.value,
    shiftAdvice: view.shiftAdvice.value,
    showShiftAdvisor: view.showShiftAdvisor.value,
    showShiftBanner: view.showShiftBanner.value,
    crossoverLearnState: view.crossoverLearnState.value,
  }))

  useHudWindowSync({
    hudTemplate,
    connected,
    live,
    showShiftAdvisor: view.showShiftAdvisor,
    showShiftBanner: view.showShiftBanner,
    clickThrough,
  })

  onMounted(() => {
    void connectWs()
    if (window.hud) {
      cleanupBackendExit = window.hud.onBackendExit(() => {
        connected.value = false
        live.value = false
      })
      cleanupBackendReady = window.hud.onBackendReady(() => {
        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
          reconnectTimer = null
        }
        void connectWs()
      })
    }
  })

  onUnmounted(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
    ws = null
    cleanupBackendExit?.()
    cleanupBackendReady?.()
  })

  return {
    connected,
    live,
    hudTemplate,
    shellClass,
    clickThrough,
    hudProps,
    close,
    toggleClickThrough,
    syncClickThroughMouse,
  }
}
