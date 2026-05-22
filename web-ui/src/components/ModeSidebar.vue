<script setup>
import { toRefs } from 'vue'
import { DRIVE_MODES } from '@/config/modes'
import {
  actionBtn,
  actionBtnDanger,
  actionBtnPrimary,
  badgeCalibrated,
  badgeLearning,
  cardSm,
  col,
  sectionTitle,
} from '@/styles/ui'
import { modeBtnClass, REGIME_PILL } from '@/utils/mode-colors'
import { useModeSidebar } from './mode-sidebar'

const props = defineProps({
  mode: { type: String, required: true },
  shiftCount: { type: Number, required: true },
  packetsTotal: { type: Number, required: true },
  telemetry: { type: Object, default: null },
  logStatus: { type: Object, default: null },
})
const emit = defineEmits(['setMode', 'logStart', 'logStop'])

const { telemetry, logStatus } = toRefs(props)
const {
  sportIndex,
  sportBarWidth,
  sportRegime,
  hasTorque,
  hasPower,
  peakTorqueText,
  peakPowerText,
  peakRpm,
  peakG,
  logMode,
  logSize,
} = useModeSidebar(telemetry, logStatus)

const isCalibrated = () => !!telemetry.value?.calibrated
const isRecording = () => !!logStatus.value?.recording
</script>

<template>
  <div :class="col">
    <h3 :class="sectionTitle">
      {{ $t('modes.title') }}
    </h3>
    <button
      v-for="m in DRIVE_MODES"
      :key="m.id"
      type="button"
      :class="modeBtnClass(m.id, mode === m.id)"
      @click="emit('setMode', m.id)"
    >
      <span class="font-medium">{{ $t(`modes.${m.i18nKey}.name`) }}</span>
      <span
        class="rounded bg-tcu-bg-3 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-tcu-txt-dim"
        :class="mode === m.id && 'bg-white/5 text-current'"
      >
        {{ $t(`modes.${m.i18nKey}.tag`) }}
      </span>
    </button>
    <div class="mt-3 rounded-md bg-tcu-bg-1 p-2.5 text-center text-xs text-tcu-txt-dim">
      {{ $t('modes.hotkeyHintBefore') }}<kbd>F9</kbd><br>{{ $t('modes.hotkeyHintAfter') }}
    </div>

    <h3 class="mt-6" :class="[sectionTitle]">
      {{ $t('calibration.title') }}
    </h3>
    <div :class="cardSm">
      <div class="mb-1.5 text-[11px] text-tcu-txt-dim">
        {{ $t('calibration.currentCar') }}
      </div>
      <span :class="isCalibrated() ? badgeCalibrated : badgeLearning">
        {{ isCalibrated() ? $t('calibration.calibrated') : $t('calibration.learning') }}
      </span>
      <div class="mt-2 text-[11px] leading-snug text-tcu-txt-dim">
        {{ $t('calibration.hint') }}
      </div>
    </div>

    <h3 class="mt-6" :class="[sectionTitle]">
      {{ $t('driveStyle.title') }}
    </h3>
    <div class="mt-2.5" :class="[cardSm]">
      <div class="mb-1.5 flex items-baseline justify-between text-[11px] uppercase tracking-widest text-tcu-txt-dim">
        <span>{{ $t('driveStyle.sportIndex') }}</span>
        <span class="font-mono text-xs font-semibold text-tcu-txt">{{ sportIndex }}</span>
      </div>
      <div class="relative h-1.5 overflow-hidden rounded-sm bg-tcu-bg-3">
        <div
          class="h-full rounded-sm bg-linear-to-r from-mode-comfort via-mode-dynamic to-mode-race transition-[width] duration-150"
          :style="{ width: sportBarWidth }"
        />
        <div class="absolute top-[-2px] bottom-[-2px] left-[30%] w-0.5 bg-tcu-txt-dim/40" />
        <div class="absolute top-[-2px] bottom-[-2px] left-[55%] w-0.5 bg-tcu-txt-dim/40" />
      </div>
      <div class="mt-2 flex items-baseline justify-between text-[11px] uppercase tracking-widest text-tcu-txt-dim">
        <span>{{ $t('driveStyle.regime') }}</span>
        <span
          class="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide"
          :class="REGIME_PILL[sportRegime] ?? REGIME_PILL.CRUISE"
        >
          {{ sportRegime }}
        </span>
      </div>
      <div class="mt-1.5 text-[10px] leading-snug text-tcu-txt-dim">
        {{ $t('driveStyle.hint') }}
      </div>
    </div>

    <h3 class="mt-6" :class="[sectionTitle]">
      {{ $t('powerBand.title') }}
    </h3>
    <div class="mt-2.5 text-[11px] text-tcu-txt-muted" :class="[cardSm]">
      <div class="flex justify-between py-0.5">
        <span class="text-tcu-txt-dim">{{ $t('powerBand.peakTorque') }}</span>
        <span class="font-mono font-semibold text-tcu-txt" :class="!hasTorque && 'font-normal text-warn'">
          {{ hasTorque ? peakTorqueText : $t('powerBand.learning') }}
        </span>
      </div>
      <div class="flex justify-between py-0.5">
        <span class="text-tcu-txt-dim">{{ $t('powerBand.peakPower') }}</span>
        <span class="font-mono font-semibold text-tcu-txt" :class="!hasPower && 'font-normal text-warn'">
          {{ hasPower ? peakPowerText : $t('powerBand.learning') }}
        </span>
      </div>
      <div class="mt-1.5 text-[10px] leading-snug text-tcu-txt-dim">
        {{ $t('powerBand.hint') }}
      </div>
    </div>

    <h3 class="mt-6" :class="[sectionTitle]">
      {{ $t('logger.title') }}
    </h3>
    <div class="mb-2 rounded-md bg-tcu-bg-1 p-2.5 text-xs text-tcu-txt-muted">
      <div class="mb-1 flex justify-between">
        <span>{{ $t('logger.status') }}:</span>
        <span :class="isRecording() && 'font-semibold text-danger before:content-[\'●_\']'">
          {{ isRecording() ? $t('logger.recording') : $t('logger.stopped') }}
        </span>
      </div>
      <div class="mb-1 flex justify-between">
        <span>{{ $t('logger.mode') }}:</span><span>{{ logMode }}</span>
      </div>
      <div class="mb-1 flex justify-between">
        <span>{{ $t('logger.packets') }}:</span><span>{{ logStatus?.packets ?? 0 }}</span>
      </div>
      <div class="flex justify-between">
        <span>{{ $t('logger.size') }}:</span><span>{{ logSize }}</span>
      </div>
    </div>
    <button type="button" :class="actionBtnPrimary" :disabled="logStatus?.recording" @click="emit('logStart', 'events')">
      {{ $t('logger.startEvents') }}
    </button>
    <button type="button" :class="actionBtn" :disabled="logStatus?.recording" @click="emit('logStart', 'all')">
      {{ $t('logger.startAll') }}
    </button>
    <button type="button" :class="actionBtnDanger" :disabled="!logStatus?.recording" @click="emit('logStop')">
      {{ $t('logger.stop') }}
    </button>
    <div class="mt-1 text-[10px] leading-snug text-tcu-txt-dim">
      {{ $t('logger.hint') }}
    </div>

    <h3 class="mt-6" :class="[sectionTitle]">
      {{ $t('session.title') }}
    </h3>
    <div class="grid grid-cols-2 gap-2">
      <div class="rounded-md bg-tcu-bg-1 p-2.5">
        <div class="text-[10px] uppercase text-tcu-txt-dim">{{ $t('session.shifts') }}</div>
        <div class="mt-0.5 font-mono text-base font-semibold">{{ shiftCount }}</div>
      </div>
      <div class="rounded-md bg-tcu-bg-1 p-2.5">
        <div class="text-[10px] uppercase text-tcu-txt-dim">{{ $t('session.packets') }}</div>
        <div class="mt-0.5 font-mono text-base font-semibold">{{ packetsTotal }}</div>
      </div>
      <div class="rounded-md bg-tcu-bg-1 p-2.5">
        <div class="text-[10px] uppercase text-tcu-txt-dim">{{ $t('session.peakRpm') }}</div>
        <div class="mt-0.5 font-mono text-base font-semibold">{{ peakRpm }}</div>
      </div>
      <div class="rounded-md bg-tcu-bg-1 p-2.5">
        <div class="text-[10px] uppercase text-tcu-txt-dim">{{ $t('session.peakG') }}</div>
        <div class="mt-0.5 font-mono text-base font-semibold">{{ peakG }}</div>
      </div>
    </div>
  </div>
</template>
