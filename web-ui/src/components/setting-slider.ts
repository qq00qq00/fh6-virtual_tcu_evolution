import { formatSliderValue } from '@/utils/format'

export const sliderProps = {
  label: { type: String, required: true },
  configKey: { type: String, required: true },
  value: { type: Number, required: true },
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  step: { type: Number, default: 1 },
  unit: { type: String, default: 'percent' },
} as const

export function sliderDisplayValue(key: string, value: number, unit?: string) {
  return formatSliderValue(key, value, unit as 'percent' | 'rpm' | 'raw' | undefined)
}

export function rangeInputValue(event: Event): number {
  const el = event.target
  if (el instanceof HTMLInputElement)
    return Number(el.value)
  return 0
}
