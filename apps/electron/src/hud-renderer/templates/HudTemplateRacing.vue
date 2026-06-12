<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import HudChrome from '../HudChrome.vue'
  import HudPedalGauge from '../HudPedalGauge.vue'
  import HudRpmSegments from '../HudRpmSegments.vue'
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
    rpmMax: number
    rpmPct: number
    rpmBarColor: string
    throttle: number
    brake: number
    shiftAdvice: ShiftAdvice
    showShiftAdvisor: boolean
    crossoverLearnState: string
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
      :learn-state="crossoverLearnState"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <HudRpmSegments :rpm-pct="rpmPct" :rpm-max="rpmMax" :segments="16" variant="bar8" />

    <div class="dash-row">
      <div class="col speed-col">
        <span class="val">{{ speed }}</span>
        <span class="lbl">KM/H</span>
      </div>

      <div class="col gear-col">
        <HudShiftHints :advice="shiftAdvice" :show="showShiftAdvisor" size="lg">
          <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
        </HudShiftHints>
      </div>

      <div class="col pedals-col">
        <HudPedalGauge label="THR" :value="throttle" compact />
        <HudPedalGauge label="BRK" :value="brake" compact />
      </div>
    </div>

    <div v-if="!connected" class="hud-status warn">backend offline</div>
    <div v-else-if="!live" class="hud-status dim">awaiting telemetry…</div>
    <div v-else class="status-spacer" aria-hidden="true" />
  </div>
</template>

<style scoped>
  .tpl-racing {
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 320px;
  }

  .dash-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 12px;
    padding: 4px 2px 0;
  }

  .col {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .speed-col {
    align-items: flex-start;
  }

  .gear-col {
    align-items: center;
  }

  .pedals-col {
    align-items: flex-end;
    gap: 6px;
  }

  .val {
    font-size: 28px;
    font-weight: 900;
    font-style: italic;
    line-height: 1;
    color: #f8fafc;
    letter-spacing: -0.02em;
  }

  .lbl {
    font-size: 8px;
    letter-spacing: 0.16em;
    color: #94a3b8;
    margin-top: 2px;
    font-weight: 600;
  }

  .gear {
    font-size: 64px;
    font-weight: 900;
    font-style: italic;
    line-height: 1;
    letter-spacing: -0.04em;
    min-width: 72px;
    text-align: center;
  }

  .status-spacer {
    min-height: 12px;
  }
</style>
