<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import HudArcTach from '../HudArcTach.vue'
  import HudChrome from '../HudChrome.vue'
  import HudPedalGauge from '../HudPedalGauge.vue'
  import HudShiftHints from '../HudShiftHints.vue'

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
    throttle: number
    brake: number
    shiftAdvice: ShiftAdvice
    showShiftAdvisor: boolean
    crossoverLearnState: string
    learnMatureGears?: number
    learnTargetGears?: number
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
      :learn-state="crossoverLearnState"
      :learn-mature-gears="learnMatureGears"
      :learn-target-gears="learnTargetGears"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <HudArcTach :rpm-pct="rpmPct" :show-ticks="false">
      <HudShiftHints :advice="shiftAdvice" :show="showShiftAdvisor" size="md" placement="below">
        <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
      </HudShiftHints>
    </HudArcTach>

    <div class="speed-line">{{ speed }} <span class="u">KM/H</span></div>

    <div class="wings">
      <HudPedalGauge label="THR" :value="throttle" />
      <HudPedalGauge label="BRK" :value="brake" />
    </div>

    <div v-if="!connected" class="hud-status warn">backend offline</div>
    <div v-else-if="!live" class="hud-status dim">awaiting telemetry…</div>
  </div>
</template>

<style scoped>
  .tpl-classic {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    width: 280px;
  }

  .gear {
    font-size: 52px;
    font-weight: 900;
    font-style: italic;
    line-height: 1;
    letter-spacing: -0.04em;
    min-width: 56px;
    text-align: center;
    color: #f8fafc;
  }

  .speed-line {
    font-size: 18px;
    font-weight: 800;
    font-style: italic;
    color: #f8fafc;
    margin-top: -2px;
  }

  .speed-line .u {
    font-size: 9px;
    letter-spacing: 0.12em;
    font-style: normal;
    color: #94a3b8;
    margin-left: 4px;
  }

  .wings {
    display: flex;
    justify-content: space-between;
    gap: 24px;
    width: 100%;
    padding: 4px 8px 4px;
  }
</style>
