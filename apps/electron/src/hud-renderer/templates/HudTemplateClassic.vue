<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import ShiftAdvisorArrows from '@virtual-tcu/ui/components/ShiftAdvisorArrows.vue'
  import HudChrome from '../HudChrome.vue'

  defineProps<{
    mode: string
    modeColor: string
    tcuState: string
    clickThrough: boolean
    connected: boolean
    live: boolean
    gearLabel: string
    gearStyle: Record<string, string>
    speed: number
    rpm: number
    rpmPct: number
    rpmBarColor: string
    hint: string
    shiftAdvice: ShiftAdvice
    showShiftAdvisor: boolean
  }>()

  const emit = defineEmits<{
    toggleClickThrough: [e: MouseEvent]
    close: []
  }>()
</script>

<template>
  <div class="tpl-classic">
    <HudChrome
      :mode="mode"
      :mode-color="modeColor"
      :tcu-state="tcuState"
      :click-through="clickThrough"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <div class="main-row">
      <ShiftAdvisorArrows
        :advice="showShiftAdvisor ? shiftAdvice : ''"
        :hint="hint"
        size="sm"
        class="gear-wrap"
      >
        <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
      </ShiftAdvisorArrows>

      <div class="metrics">
        <div class="rpm-line">
          <span class="rpm-num">{{ rpm }}</span>
          <span class="rpm-unit">RPM</span>
        </div>
        <div class="rpm-bar">
          <div class="rpm-fill" :style="{ width: `${rpmPct * 100}%`, background: rpmBarColor }" />
        </div>
        <div class="speed-line">
          <span class="speed-num">{{ speed }}</span>
          <span class="speed-unit">km/h</span>
        </div>
      </div>
    </div>

    <div v-if="hint && showShiftAdvisor" class="hint">{{ hint }}</div>
    <div v-else-if="!connected" class="hud-status warn">backend offline</div>
    <div v-else-if="!live" class="hud-status dim">awaiting telemetry…</div>
  </div>
</template>

<style scoped>
  .tpl-classic {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
    min-height: 0;
  }

  .main-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
  }

  .gear-wrap {
    flex-shrink: 0;
  }

  .gear {
    font-size: 64px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.04em;
    min-width: 56px;
    text-align: center;
  }

  .metrics {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .rpm-line,
  .speed-line {
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  .rpm-num {
    font-size: 20px;
    font-weight: 700;
    color: #f8fafc;
  }

  .rpm-unit,
  .speed-unit {
    font-size: 9px;
    color: #64748b;
    letter-spacing: 0.1em;
  }

  .rpm-bar {
    height: 4px;
    background: rgba(148, 163, 184, 0.25);
    border-radius: 2px;
    overflow: hidden;
  }

  .rpm-fill {
    height: 100%;
    transition:
      width 75ms linear,
      background 150ms linear;
  }

  .speed-num {
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
  }

  .hint {
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #38bdf8;
    text-align: center;
  }
</style>
