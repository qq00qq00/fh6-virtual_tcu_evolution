import type { HudTemplateId, ShiftAdvice } from '@virtual-tcu/shared/config/hud'
import type { TelemetrySnapshot } from '@virtual-tcu/shared/types/telemetry'
import type { DriveMode } from '@virtual-tcu/shared/types/ws'
import type { Ref } from 'vue'
import { normalizeHudTemplate, parseShiftAdvice } from '@virtual-tcu/shared/config/hud'
import { computed } from 'vue'

export function parseShiftAdviceFromTelemetry(t: Partial<TelemetrySnapshot>): ShiftAdvice {
  const direct = parseShiftAdvice(t.shift_advice)
  if (direct) return direct
  const hint = t.shift_hint ?? ''
  if (hint.startsWith('↑')) return 'up'
  if (hint.startsWith('↓')) return 'down'
  return ''
}

export function useHudView(
  telemetry: Ref<Partial<TelemetrySnapshot>>,
  mode: Ref<DriveMode>,
  tcuState: Ref<string>,
  clickThrough: Ref<boolean>,
) {
  const gearLabel = computed(() => {
    const g = telemetry.value.gear
    if (g === 0) return 'R'
    if (g === 11) return 'N'
    return g != null ? String(g) : '-'
  })

  const speed = computed(() => Math.round(telemetry.value.speed_kmh ?? 0))
  const rpm = computed(() => Math.round(telemetry.value.rpm ?? 0))
  const rpmPct = computed(() => Math.max(0, Math.min(1, telemetry.value.rpm_pct ?? 0)))
  const hint = computed(() => telemetry.value.shift_hint ?? '')
  const shiftAdvice = computed(() => parseShiftAdviceFromTelemetry(telemetry.value))
  const showShiftAdvisor = computed(
    () => mode.value === 'MANUAL' && tcuState.value === 'MANUAL' && !!shiftAdvice.value,
  )

  const modeColor = computed(() => {
    const colors: Record<string, string> = {
      COMFORT: '#38bdf8',
      RACE: '#22c55e',
      DRIFT: '#f43f5e',
      OFFROAD: '#fb923c',
      MANUAL: '#94a3b8',
    }
    return colors[mode.value] ?? '#94a3b8'
  })

  const rpmBarColor = computed(() => {
    if (rpmPct.value > 0.92) return '#ef4444'
    if (rpmPct.value > 0.78) return '#f59e0b'
    return '#22c55e'
  })

  const gearColor = computed(() => {
    if (tcuState.value === 'SHIFTING') return '#a78bfa'
    if (gearLabel.value === 'R') return '#f59e0b'
    return clickThrough.value ? '#ffffff' : '#f8fafc'
  })

  const gearStyle = computed(() => {
    if (!clickThrough.value) {
      return { color: tcuState.value === 'SHIFTING' ? '#a78bfa' : gearColor.value }
    }
    if (tcuState.value === 'SHIFTING') return { color: '#ddd6fe' }
    if (gearLabel.value === 'R') return { color: '#fde68a' }
    return { color: '#ffffff' }
  })

  return {
    gearLabel,
    speed,
    rpm,
    rpmPct,
    hint,
    shiftAdvice,
    showShiftAdvisor,
    modeColor,
    rpmBarColor,
    gearColor,
    gearStyle,
  }
}

export { type HudTemplateId, normalizeHudTemplate }
