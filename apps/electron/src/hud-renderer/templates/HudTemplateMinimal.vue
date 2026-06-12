<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import HudChrome from '../HudChrome.vue'
  import HudLedDots from '../HudLedDots.vue'
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
  }>()

  const emit = defineEmits<{
    toggleClickThrough: [e: MouseEvent]
    close: []
  }>()
</script>

<template>
  <div class="tpl-minimal">
    <div class="panel" :class="clickThrough ? 'mode-float' : 'mode-pinned'">
      <div class="row-main">
        <div class="gear-block">
          <HudShiftHints :advice="shiftAdvice" :show="showShiftAdvisor" size="sm">
            <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
          </HudShiftHints>
          <span class="gear-lbl">GEAR</span>
        </div>

        <div class="speed-block">
          <span class="speed">{{ speed }}</span>
          <span class="unit">KM/H</span>
        </div>

        <div class="pedals-block">
          <HudPedalGauge label="THR" :value="throttle" compact />
          <HudPedalGauge label="BRK" :value="brake" compact />
        </div>
      </div>

      <HudLedDots :rpm-pct="rpmPct" :count="18" />
    </div>

    <div class="chrome-foot">
      <HudChrome
        compact
        footer
        :mode="mode"
        :mode-color="modeColor"
        :tcu-state="tcuState"
        :click-through="clickThrough"
        :learn-state="crossoverLearnState"
        @toggle-click-through="emit('toggleClickThrough', $event)"
        @close="emit('close')"
      />
    </div>

    <div v-if="!connected" class="hud-status warn">offline</div>
    <div v-else-if="!live" class="hud-status dim">standby</div>
  </div>
</template>

<style scoped>
  .tpl-minimal {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: fit-content;
    min-width: 340px;
    max-width: 100%;
  }

  .chrome-foot {
    width: 100%;
    box-sizing: border-box;
  }

  .panel {
    clip-path: polygon(
      8px 0,
      calc(100% - 8px) 0,
      100% 8px,
      100% calc(100% - 8px),
      calc(100% - 8px) 100%,
      8px 100%,
      0 calc(100% - 8px),
      0 8px
    );
    padding: 10px 12px 8px;
    transition:
      background 180ms,
      border-color 180ms;
  }

  .panel.mode-pinned {
    background: rgba(0, 0, 0, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }

  .panel.mode-float {
    background: transparent;
    border: none;
    -webkit-app-region: no-drag;
  }

  .row-main {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 8px;
  }

  .gear-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    min-width: 52px;
  }

  .gear {
    font-size: 40px;
    font-weight: 900;
    font-style: italic;
    line-height: 1;
    min-width: 40px;
    text-align: center;
  }

  .gear-lbl {
    font-size: 7px;
    letter-spacing: 0.18em;
    color: #64748b;
    font-weight: 700;
  }

  .speed-block {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 80px;
  }

  .speed {
    font-size: 32px;
    font-weight: 900;
    font-style: italic;
    line-height: 1;
    color: #f8fafc;
  }

  .unit {
    font-size: 8px;
    letter-spacing: 0.16em;
    color: #94a3b8;
    margin-top: 2px;
  }

  .pedals-block {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 72px;
  }
</style>
