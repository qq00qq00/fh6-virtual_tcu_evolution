import type { ConfigMap } from '../types/ws'
import { computed, ref, watch } from 'vue'
import {
  allowsUdpHubTargetInput,
  allowsUdpHubTargetsInput,
  normalizeUdpHubTargetTag,
  sanitizeUdpHubTargetTags,
  serializeUdpHubTargets,
  splitUdpHubTargets,
  validateUdpHubTargetTag,
  validateUdpHubTargetTags,
} from '../utils/udpHubTargets'

const BIND_HOST_CHARS_RE = /^[\d.]*$/
const PORT_CHARS_RE = /^\d{0,5}$/

export function isValidBindHost(host: string): boolean {
  const h = host.trim()
  if (h === '0.0.0.0' || h === '127.0.0.1') return true
  const parts = h.split('.')
  if (parts.length !== 4) return false
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

export { allowsUdpHubTargetInput, allowsUdpHubTargetsInput }

function tagsEqual(a: readonly string[], b: readonly string[]): boolean {
  if (a.length !== b.length) return false
  return a.every((tag, i) => tag === b[i])
}

export function useNetworkSettings(config: () => ConfigMap) {
  const draftHost = ref('')
  const draftWebPort = ref('')
  const draftUdpPort = ref('')
  const draftUdpHubEnabled = ref(false)
  const draftUdpHubTargetTags = ref<string[]>([])
  const udpHubTagError = ref('')
  const applyError = ref('')
  const applyOk = ref(false)

  function syncFromConfig() {
    draftHost.value = String(config().web_host ?? '127.0.0.1')
    draftWebPort.value = String(config().web_port ?? 8765)
    draftUdpPort.value = String(config().udp_port ?? 5555)
    draftUdpHubEnabled.value = !!config().udp_hub_enabled
    draftUdpHubTargetTags.value = sanitizeUdpHubTargetTags(
      splitUdpHubTargets(String(config().udp_hub_targets ?? '')),
    )
    udpHubTagError.value = ''
    applyError.value = ''
    applyOk.value = false
  }

  watch(config, syncFromConfig, { immediate: true, deep: true })

  watch(draftUdpPort, () => {
    if (!draftUdpHubEnabled.value) return
    applyError.value = validateUdpHubTargetTags(draftUdpHubTargetTags.value, currentUdpPort(), true)
  })

  const savedHubTags = computed(() => splitUdpHubTargets(String(config().udp_hub_targets ?? '')))

  const dirty = computed(
    () =>
      draftHost.value.trim() !== String(config().web_host ?? '') ||
      String(draftWebPort.value).trim() !== String(config().web_port ?? '') ||
      String(draftUdpPort.value).trim() !== String(config().udp_port ?? '') ||
      draftUdpHubEnabled.value !== !!config().udp_hub_enabled ||
      !tagsEqual(draftUdpHubTargetTags.value, savedHubTags.value),
  )

  function currentUdpPort(): number {
    return Number(draftUdpPort.value.trim())
  }

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
    const hubError = validateUdpHubTargetTags(
      draftUdpHubTargetTags.value,
      udpPort,
      draftUdpHubEnabled.value,
    )
    if (hubError) {
      applyError.value = hubError
      return null
    }
    applyError.value = ''
    udpHubTagError.value = ''
    return {
      host,
      webPort,
      udpPort,
      udpHubEnabled: draftUdpHubEnabled.value,
      udpHubTargets: serializeUdpHubTargets(draftUdpHubTargetTags.value),
    }
  }

  function setUdpHubEnabled(value: boolean) {
    udpHubTagError.value = ''
    if (!value) {
      applyError.value = ''
      draftUdpHubEnabled.value = false
      return
    }
    draftUdpHubEnabled.value = true
  }

  function setUdpHubTargetTags(tags: unknown) {
    const clean = sanitizeUdpHubTargetTags(tags)
    draftUdpHubTargetTags.value = clean
    udpHubTagError.value = ''
    if (draftUdpHubEnabled.value) {
      applyError.value = validateUdpHubTargetTags(clean, currentUdpPort(), true)
    }
  }

  /** Return normalized tag string on success; `false` cancels (sanitized on update). */
  function onCreateUdpHubTag(label: string): string | false {
    const udpPort = currentUdpPort()
    if (!isValidUdpPort(udpPort)) {
      udpHubTagError.value = 'invalidUdpPort'
      return false
    }
    const err = validateUdpHubTargetTag(label, udpPort, draftUdpHubTargetTags.value)
    if (err) {
      udpHubTagError.value = err
      return false
    }
    const tag = normalizeUdpHubTargetTag(label)
    if (!tag) {
      udpHubTagError.value = 'invalidUdpHubTargets'
      return false
    }
    udpHubTagError.value = ''
    applyError.value = ''
    return tag
  }

  function markApplyResult(ok: boolean, error = '') {
    applyOk.value = ok
    applyError.value = error
    if (ok) syncFromConfig()
  }

  return {
    draftHost,
    draftWebPort,
    draftUdpPort,
    draftUdpHubEnabled,
    draftUdpHubTargetTags,
    udpHubTagError,
    dirty,
    applyError,
    applyOk,
    syncFromConfig,
    validate,
    allowsBindHostInput,
    allowsPortInput,
    allowsUdpHubTargetInput,
    allowsUdpHubTargetsInput,
    setUdpHubEnabled,
    setUdpHubTargetTags,
    onCreateUdpHubTag,
    markApplyResult,
  }
}
