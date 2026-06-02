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
  <div class="tpl-glass">
    <HudChrome
      :mode="mode"
      :mode-color="modeColor"
      :tcu-state="tcuState"
      :click-through="clickThrough"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <div class="glass-grid">
      <ShiftAdvisorArrows :advice="showShiftAdvisor ? shiftAdvice : ''" size="md" class="gear-cell">
        <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
      </ShiftAdvisorArrows>

      <div class="stat-cell">
        <div class="label">SPEED</div>
        <div class="val">{{ speed }}</div>
      </div>
      <div class="stat-cell">
        <div class="label">RPM</div>
        <div class="val rpm">{{ rpm }}</div>
        <div class="rpm-bar">
          <div class="rpm-fill" :style="{ width: `${rpmPct * 100}%`, background: rpmBarColor }" />
        </div>
      </div>
    </div>

    <div v-if="showShiftAdvisor && hint" class="hint">{{ hint }}</div>
    <div v-else-if="!connected" class="hud-status warn">offline</div>
    <div v-else-if="!live" class="hud-status dim">standby</div>
  </div>
</template>

<style scoped>
  .tpl-glass {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
  }

  .glass-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    flex: 1;
    align-items: center;
  }

  .gear-cell {
    grid-column: 1 / -1;
    justify-content: center;
  }

  .gear {
    font-size: 56px;
    font-weight: 900;
    line-height: 1;
    text-align: center;
    background: linear-gradient(180deg, #f8fafc 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }

  .stat-cell {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 10px;
    backdrop-filter: blur(8px);
  }

  .label {
    font-size: 8px;
    letter-spacing: 0.14em;
    color: #64748b;
    margin-bottom: 2px;
  }

  .val {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
  }

  .val.rpm {
    font-size: 18px;
  }

  .rpm-bar {
    margin-top: 4px;
    height: 3px;
    background: rgba(0, 0, 0, 0.35);
    border-radius: 2px;
    overflow: hidden;
  }

  .rpm-fill {
    height: 100%;
    transition: width 75ms linear;
  }

  .hint {
    font-size: 9px;
    text-align: center;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #38bdf8;
  }
</style>
