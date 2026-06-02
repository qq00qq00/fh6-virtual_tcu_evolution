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
  <div class="tpl-racing">
    <HudChrome
      :mode="mode"
      :mode-color="modeColor"
      :tcu-state="tcuState"
      :click-through="clickThrough"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <div class="rpm-arc-wrap">
      <svg class="rpm-arc" viewBox="0 0 120 64" aria-hidden="true">
        <path class="arc-bg" d="M 12 56 A 48 48 0 0 1 108 56" fill="none" stroke-width="5" />
        <path
          class="arc-fill"
          d="M 12 56 A 48 48 0 0 1 108 56"
          fill="none"
          stroke-width="5"
          :stroke="rpmBarColor"
          pathLength="1"
          :stroke-dasharray="`${rpmPct} 1`"
        />
      </svg>
      <ShiftAdvisorArrows :advice="showShiftAdvisor ? shiftAdvice : ''" size="lg" class="center">
        <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
      </ShiftAdvisorArrows>
    </div>

    <div class="footer">
      <span class="rpm-val">{{ rpm }} <span class="u">RPM</span></span>
      <span class="spd">{{ speed }} <span class="u">KM/H</span></span>
    </div>
    <div v-if="showShiftAdvisor && hint" class="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
  .tpl-racing {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    align-items: stretch;
  }

  .rpm-arc-wrap {
    position: relative;
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 72px;
  }

  .rpm-arc {
    position: absolute;
    width: 100%;
    max-width: 200px;
    height: auto;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
  }

  .arc-bg {
    stroke: rgba(148, 163, 184, 0.25);
  }

  .arc-fill {
    transition:
      stroke-dasharray 75ms linear,
      stroke 150ms linear;
  }

  .center {
    position: relative;
    z-index: 1;
  }

  .gear {
    font-size: 72px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.05em;
    text-align: center;
  }

  .footer {
    display: flex;
    justify-content: space-between;
    font-weight: 700;
    color: #f8fafc;
    padding: 0 4px;
  }

  .rpm-val {
    font-size: 14px;
  }

  .spd {
    font-size: 14px;
    color: #38bdf8;
  }

  .u {
    font-size: 8px;
    color: #64748b;
    letter-spacing: 0.08em;
    font-weight: 600;
  }

  .hint {
    font-size: 9px;
    text-align: center;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #38bdf8;
  }
</style>
