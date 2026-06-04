const UDP_HUB_TARGETS_SPLIT_RE = /[\s,;]+/
const UDP_HUB_TARGET_INPUT_RE = /^[a-z0-9.:-]*$/i

export type UdpHubTargetError = '' | 'invalidUdpHubTargets' | 'udpHubTargetLoop' | 'udpHubDuplicate'

export function allowsUdpHubTargetInput(value: string): boolean {
  return UDP_HUB_TARGET_INPUT_RE.test(value)
}

/** @deprecated Use allowsUdpHubTargetInput for per-tag input. */
export function allowsUdpHubTargetsInput(value: string): boolean {
  return /^[\d\s,;:.a-z-]*$/i.test(value)
}

function isValidTargetHost(host: string): boolean {
  const h = host.trim().toLowerCase()
  if (h === 'localhost') return true
  if (h === '0.0.0.0' || h === '127.0.0.1') return true
  const parts = h.split('.')
  if (parts.length === 4) {
    return parts.every((p) => {
      const n = Number(p)
      return Number.isInteger(n) && n >= 0 && n <= 255
    })
  }
  const labels = h.split('.')
  return labels.every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))
}

export function isValidUdpPort(port: number): boolean {
  return Number.isInteger(port) && port >= 1 && port <= 65535
}

export function parseUdpHubTargetEntry(entry: string): { host: string; port: number } | null {
  const item = entry.trim()
  if (!item) return null

  const splitAt = item.lastIndexOf(':')
  const hasHost = splitAt >= 0
  const hostText = hasHost ? item.slice(0, splitAt) : '127.0.0.1'
  const portText = hasHost ? item.slice(splitAt + 1) : item
  const host = (hostText || '127.0.0.1').trim()
  const port = Number(portText.trim())
  if (!host || !isValidTargetHost(host) || !isValidUdpPort(port)) return null
  return { host, port }
}

/** Canonical tag label stored in config (host:port). */
export function normalizeUdpHubTargetTag(entry: string): string | null {
  const parsed = parseUdpHubTargetEntry(entry)
  if (!parsed) return null
  const host = parsed.host.toLowerCase() === 'localhost' ? '127.0.0.1' : parsed.host
  return `${host}:${parsed.port}`
}

export function splitUdpHubTargets(raw: string): string[] {
  const tags: string[] = []
  const seen = new Set<string>()
  for (const entry of raw.split(UDP_HUB_TARGETS_SPLIT_RE)) {
    if (!entry.trim()) continue
    const normalized = normalizeUdpHubTargetTag(entry)
    if (!normalized || seen.has(normalized)) continue
    seen.add(normalized)
    tags.push(normalized)
  }
  return tags
}

export function serializeUdpHubTargets(tags: readonly string[]): string {
  return tags
    .map((t) => t.trim())
    .filter(Boolean)
    .join(', ')
}

/** Strip non-string entries (e.g. Naive UI pushing `false` from on-create). */
export function sanitizeUdpHubTargetTags(tags: unknown): string[] {
  if (!Array.isArray(tags)) return []
  return tags.filter((t): t is string => typeof t === 'string' && Boolean(t.trim()))
}

export function validateUdpHubTargetTag(
  entry: unknown,
  udpPort: number,
  existing: readonly string[],
): UdpHubTargetError {
  if (typeof entry !== 'string') return 'invalidUdpHubTargets'
  if (!allowsUdpHubTargetInput(entry.trim())) return 'invalidUdpHubTargets'
  const normalized = normalizeUdpHubTargetTag(entry)
  if (!normalized) return 'invalidUdpHubTargets'
  if (existing.includes(normalized)) return 'udpHubDuplicate'
  const target = parseUdpHubTargetEntry(normalized)
  if (!target) return 'invalidUdpHubTargets'
  const host = target.host.toLowerCase()
  if (
    target.port === udpPort &&
    (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0')
  ) {
    return 'udpHubTargetLoop'
  }
  return ''
}

export function validateUdpHubTargetTags(
  tags: readonly string[],
  udpPort: number,
  enabled: boolean,
): UdpHubTargetError {
  if (!enabled) return ''
  if (!tags.length) return 'invalidUdpHubTargets'
  const seen = new Set<string>()
  for (const tag of tags) {
    const err = validateUdpHubTargetTag(tag, udpPort, [...seen])
    if (err) return err
    const normalized = normalizeUdpHubTargetTag(tag)
    if (normalized) seen.add(normalized)
  }
  return ''
}
