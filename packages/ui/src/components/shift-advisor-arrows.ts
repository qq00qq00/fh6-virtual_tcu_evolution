import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
import type { Ref } from 'vue'
import { computed } from 'vue'

export interface ShiftAdvisorArrowsProps {
  advice?: ShiftAdvice
  hint?: string
  showHint?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function useShiftAdvisorArrows(
  advice: Ref<ShiftAdvice | undefined>,
  hint: Ref<string | undefined>,
) {
  const showUp = computed(() => advice.value === 'up')
  const showDown = computed(() => advice.value === 'down')
  const hasAdvice = computed(() => showUp.value || showDown.value)
  const hintText = computed(() => hint.value?.trim() ?? '')

  return { showUp, showDown, hasAdvice, hintText }
}
