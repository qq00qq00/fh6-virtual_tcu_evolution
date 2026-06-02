export const HUD_TEMPLATES = [
  { value: 'classic', i18nKey: 'hudClassic' },
  { value: 'minimal', i18nKey: 'hudMinimal' },
  { value: 'racing', i18nKey: 'hudRacing' },
  { value: 'glass', i18nKey: 'hudGlass' },
] as const

export type HudTemplateId = (typeof HUD_TEMPLATES)[number]['value']

const VALID = new Set<string>(HUD_TEMPLATES.map((t) => t.value))

export function normalizeHudTemplate(value: unknown): HudTemplateId {
  if (typeof value === 'string' && VALID.has(value)) return value as HudTemplateId
  return 'classic'
}

export type ShiftAdvice = 'up' | 'down' | ''

export function parseShiftAdvice(value: unknown): ShiftAdvice {
  if (value === 'up' || value === 'down') return value
  return ''
}
