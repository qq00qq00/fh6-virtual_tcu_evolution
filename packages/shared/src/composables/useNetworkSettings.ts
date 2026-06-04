import type { ConfigMap } from '../types/ws'
import { computed, ref, watch } from 'vue'

const UDP_HUB_TARGET_SPLIT_RE = /[\s,;]+/
const UDP_HUB_TARGET_CHARS_RE = /^[\d\s,;:.]*$/
const BIND_HOST_CHARS_RE = /^[\d.]*$/
const PORT_CHARS_RE = /^\d{0,5}$/

export function isValidBindHost(host: string): boolean {
  const h = host.trim()
  if (h === '0.0.0.0' || h === '127.0.0.1')
    return true
  const parts = h.split('.')
  if (parts.length !== 4)
    return false
  return parts.every((p) => {
    const n = Number(p)
    return Number.isInteger(n) && n >= 0 && n <= 255
  })
}

export function isValidUdpPort(port: number): boolean {
  return Number.isInteger(port) && port >= 1 && port <= 65535
}

export function isValidWebPort(port: number): boolean {
  return Number.isInteger(port) && port >= 1024 && port <= 65535
}

export function allowsPortInput(value: string): boolean {
  return PORT_CHARS_RE.test(value)
}

export function allowsBindHostInput(value: string): boolean {
  return BIND_HOST_CHARS_RE.test(value)
}

export function allowsUdpHubTargetsInput(value: string): boolean {
  return UDP_HUB_TARGET_CHARS_RE.test(value)
}

function isValidTargetHost(host: string): boolean {
  const h = host.trim().toLowerCase()
  if (h === 'localhost')
    return true
  if (isValidBindHost(h))
    return true
  const labels = h.split('.')
  return labels.every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))
}

function parseUdpHubTarget(entry: string): { host: string, port: number } | null {
  const item = entry.trim()
  if (!item)
    return null

  const splitAt = item.lastIndexOf(':')
  const hasHost = splitAt >= 0
  const hostText = hasHost ? item.slice(0, splitAt) : '127.0.0.1'
  const portText = hasHost ? item.slice(splitAt + 1) : item
  const host = (hostText || '127.0.0.1').trim()
  const port = Number(portText.trim())
  if (!host || !isValidTargetHost(host) || !isValidUdpPort(port))
    return null
  return { host, port }
}

function validateUdpHubTargets(
  rawTargets: string,
  udpPort: number,
  enabled: boolean,
): '' | 'invalidUdpHubTargets' | 'udpHubTargetLoop' {
  const raw = rawTargets.trim()
  if (!raw)
    return enabled ? 'invalidUdpHubTargets' : ''
  if (!allowsUdpHubTargetsInput(raw))
    return 'invalidUdpHubTargets'

  const entries = raw.split(UDP_HUB_TARGET_SPLIT_RE).filter(Boolean)
  if (!entries.length)
    return enabled ? 'invalidUdpHubTargets' : ''

  for (const entry of entries) {
    const target = parseUdpHubTarget(entry)
    if (!target)
      return 'invalidUdpHubTargets'
    const host = target.host.toLowerCase()
    if (
      target.port === udpPort
      && (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0')
    ) {
      return 'udpHubTargetLoop'
    }
  }
  return ''
}

export function useNetworkSettings(config: () => ConfigMap) {
  const draftHost = ref('')
  const draftWebPort = ref('')
  const draftUdpPort = ref('')
  const draftUdpHubEnabled = ref(false)
  const draftUdpHubTargets = ref('')
  const applyError = ref('')
  const applyOk = ref(false)

  function syncFromConfig() {
    draftHost.value = String(config().web_host ?? '127.0.0.1')
    draftWebPort.value = String(config().web_port ?? 8765)
    draftUdpPort.value = String(config().udp_port ?? 5555)
    draftUdpHubEnabled.value = !!config().udp_hub_enabled
    draftUdpHubTargets.value = String(config().udp_hub_targets ?? '')
    applyError.value = ''
    applyOk.value = false
  }

  watch(config, syncFromConfig, { immediate: true, deep: true })

  const dirty = computed(() =>
    draftHost.value.trim() !== String(config().web_host ?? '')
    || String(draftWebPort.value).trim() !== String(config().web_port ?? '')
    || String(draftUdpPort.value).trim() !== String(config().udp_port ?? '')
    || draftUdpHubEnabled.value !== !!config().udp_hub_enabled
    || draftUdpHubTargets.value.trim() !== String(config().udp_hub_targets ?? '').trim(),
  )

  function validate(): {
    host: string
    webPort: number
    udpPort: number
    udpHubEnabled: boolean
    udpHubTargets: string
  } | null {
    const host = draftHost.value.trim()
    const webPort = Number(draftWebPort.value.trim())
    const udpPort = Number(draftUdpPort.value.trim())
    if (!isValidBindHost(host)) {
      applyError.value = 'invalidHost'
      return null
    }
    if (!isValidWebPort(webPort)) {
      applyError.value = 'invalidPort'
      return null
    }
    if (!isValidUdpPort(udpPort)) {
      applyError.value = 'invalidUdpPort'
      return null
    }
    const hubError = validateUdpHubTargets(
      draftUdpHubTargets.value,
      udpPort,
      draftUdpHubEnabled.value,
    )
    if (hubError) {
      applyError.value = hubError
      return null
    }
    applyError.value = ''
    return {
      host,
      webPort,
      udpPort,
      udpHubEnabled: draftUdpHubEnabled.value,
      udpHubTargets: draftUdpHubTargets.value.trim(),
    }
  }

  function setUdpHubEnabled(value: boolean) {
    if (value) {
      const udpPort = Number(draftUdpPort.value.trim())
      const hubError = validateUdpHubTargets(draftUdpHubTargets.value, udpPort, true)
      if (hubError) {
        applyError.value = hubError
        draftUdpHubEnabled.value = false
        return
      }
    }
    applyError.value = ''
    draftUdpHubEnabled.value = value
  }

  function setUdpHubTargets(value: string) {
    draftUdpHubTargets.value = value
    if (draftUdpHubEnabled.value) {
      const udpPort = Number(draftUdpPort.value.trim())
      applyError.value = validateUdpHubTargets(value, udpPort, true)
    }
  }

  function markApplyResult(ok: boolean, error = '') {
    applyOk.value = ok
    applyError.value = error
    if (ok)
      syncFromConfig()
  }

  return {
    draftHost,
    draftWebPort,
    draftUdpPort,
    draftUdpHubEnabled,
    draftUdpHubTargets,
    dirty,
    applyError,
    applyOk,
    syncFromConfig,
    validate,
    allowsBindHostInput,
    allowsPortInput,
    allowsUdpHubTargetsInput,
    setUdpHubEnabled,
    setUdpHubTargets,
    markApplyResult,
  }
}
