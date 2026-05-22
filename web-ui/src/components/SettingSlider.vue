<script setup>
import { computed } from 'vue'
import { rangeInput, settingRow } from '@/styles/ui'
import { rangeInputValue, sliderDisplayValue, sliderProps } from './setting-slider'

const props = defineProps(sliderProps)
const emit = defineEmits(['input'])
const display = computed(() => sliderDisplayValue(props.configKey, props.value, props.unit))
</script>

<template>
  <div :class="settingRow">
    <span class="text-xs text-tcu-txt-muted">{{ label }}</span>
    <span class="min-w-[50px] text-right font-mono text-xs text-tcu-txt">{{ display }}</span>
    <input
      type="range"
      :class="rangeInput"
      :min="min"
      :max="max"
      :step="step"
      :value="value"
      @input="emit('input', rangeInputValue($event))"
    >
  </div>
</template>
