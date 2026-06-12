import type { HudTemplateId, ShiftAdvice } from '@virtual-tcu/shared/config/hud'
import type { TelemetrySnapshot } from '@virtual-tcu/shared/types/telemetry'
import type { DriveMode } from '@virtual-tcu/shared/types/ws'
import type { Ref } from 'vue'
import { normalizeHudTemplate, parseShiftAdvice } from '@virtual-tcu/shared/config/hud'
import { formatGearLabel } from '@virtual-tcu/shared/utils/format'
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
  const gearLabel = computed(() =>
    formatGearLabel(telemetry.value.gear, telemetry.value.is_race_on),
  )

  const speed = computed(() => Math.round(telemetry.value.speed_kmh ?? 0))
  const rpm = computed(() => Math.round(telemetry.value.rpm ?? 0))
  const rpmMax = computed(() => telemetry.value.rpm_max ?? 8000)
  const rpmPct = computed(() => Math.max(0, Math.min(1, telemetry.value.rpm_pct ?? 0)))
  const throttle = computed(() => Math.max(0, Math.min(1, telemetry.value.throttle ?? 0)))
  const brake = computed(() => Math.max(0, Math.min(1, telemetry.value.brake ?? 0)))
  const shiftAdvice = computed(() => parseShiftAdviceFromTelemetry(telemetry.value))
  const showShiftAdvisor = computed(
    () => mode.value === 'MANUAL' && tcuState.value === 'MANUAL' && !!shiftAdvice.value,
  )
  const showShiftBanner = computed(() => mode.value === 'MANUAL' && tcuState.value === 'MANUAL')

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
    if (clickThrough.value) return '#ffffff'
    return '#f1f5f9'
  })

  const gearStyle = computed(() => {
    if (!clickThrough.value) {
      return { color: tcuState.value === 'SHIFTING' ? '#a78bfa' : gearColor.value }
    }
    if (tcuState.value === 'SHIFTING') return { color: '#ddd6fe' }
    if (gearLabel.value === 'R') return { color: '#fde68a' }
    return { color: '#ffffff' }
  })

  const crossoverLearnState = computed<'learning' | 'learned' | 'relearning'>(() => {
    if (telemetry.value.crossover_relearning) return 'relearning'
    if (telemetry.value.calibrated && telemetry.value.power_curve_learned) return 'learned'
    return 'learning'
  })

  return {
    gearLabel,
    speed,
    rpm,
    rpmMax,
    rpmPct,
    throttle,
    brake,
    shiftAdvice,
    showShiftAdvisor,
    showShiftBanner,
    modeColor,
    rpmBarColor,
    gearColor,
    gearStyle,
    crossoverLearnState,
  }
}

export { type HudTemplateId, normalizeHudTemplate }
