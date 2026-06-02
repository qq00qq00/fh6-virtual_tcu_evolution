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
  <div class="tpl-minimal">
    <HudChrome
      :mode="mode"
      :mode-color="modeColor"
      :tcu-state="tcuState"
      :click-through="clickThrough"
      @toggle-click-through="emit('toggleClickThrough', $event)"
      @close="emit('close')"
    />

    <div class="core">
      <ShiftAdvisorArrows :advice="showShiftAdvisor ? shiftAdvice : ''" size="sm">
        <div class="gear" :style="gearStyle">{{ gearLabel }}</div>
      </ShiftAdvisorArrows>
      <div class="side">
        <div class="speed">{{ speed }}<span class="u">km/h</span></div>
        <div class="rpm-bar">
          <div class="rpm-fill" :style="{ width: `${rpmPct * 100}%`, background: rpmBarColor }" />
        </div>
        <div class="rpm">{{ rpm }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .tpl-minimal {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
  }

  .core {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
  }

  .gear {
    font-size: 48px;
    font-weight: 900;
    line-height: 1;
    min-width: 44px;
    text-align: center;
  }

  .side {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .speed {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
  }

  .speed .u {
    font-size: 9px;
    color: #64748b;
    margin-left: 4px;
    font-weight: 500;
  }

  .rpm {
    font-size: 11px;
    color: #94a3b8;
    font-weight: 600;
  }

  .rpm-bar {
    height: 3px;
    background: rgba(148, 163, 184, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .rpm-fill {
    height: 100%;
    transition: width 75ms linear;
  }
</style>
