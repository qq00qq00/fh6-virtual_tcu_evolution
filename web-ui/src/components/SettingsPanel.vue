<script setup>
import { computed, toRefs } from 'vue'
import { FEATURE_TOGGLES, HOTKEY_FIELDS, SETTING_GROUPS } from '@/config/settings'
import {
  actionBtn,
  actionBtnCompact,
  actionBtnDanger,
  col,
  hotkeyInput,
  sectionTitle,
  statRow,
  tabActive,
  tabBase,
  toggleRow,
} from '@/styles/ui'
import { hotkeyInputValue, TAB_IDS, useSettingsPanel } from './settings-panel'
import SettingSlider from './SettingSlider.vue'
import ToggleSwitch from './ToggleSwitch.vue'

const props = defineProps({
  config: { type: Object, required: true },
  telemetry: { type: Object, default: null },
  sessionStats: { type: Object, default: null },
  shiftHistory: { type: Array, default: () => [] },
  watchdogStuck: { type: Boolean, default: false },
})
const emit = defineEmits(['setConfig', 'resetConfig', 'exportProfile', 'openImport'])

const { config, telemetry, sessionStats, shiftHistory, watchdogStuck } = toRefs(props)

const {
  activeTab,
  slidersFor,
  statsRows,
  historyItems,
  configValue,
  configBool,
  configText,
  sliderDef,
} = useSettingsPanel(
  () => config.value,
  () => telemetry.value,
  () => sessionStats.value,
  () => shiftHistory.value,
)

const extrasSliders = computed(() => slidersFor('extras'))
</script>

<template>
  <div :class="col">
    <div class="mb-4 flex gap-1 border-b border-tcu-border">
      <button
        v-for="tab in TAB_IDS"
        :key="tab"
        type="button"
        :class="[tabBase, activeTab === tab && tabActive]"
        @click="activeTab = tab"
      >
        {{ $t(`tabs.${tab}`) }}
      </button>
    </div>

    <div v-show="activeTab === 'settings'">
      <div
        v-if="watchdogStuck"
        class="mb-3 rounded-lg border border-warn bg-warn/15 px-3.5 py-2.5 text-sm text-warn before:font-bold before:content-['⚠_']"
      >
        {{ $t('settings.watchdog') }}
      </div>
      <h3 :class="sectionTitle">
        {{ $t('settings.features') }}
      </h3>
      <div v-for="f in FEATURE_TOGGLES" :key="f.key" :class="toggleRow">
        <span class="text-sm text-tcu-txt-muted">{{ $t(`settings.${f.i18nKey}`) }}</span>
        <ToggleSwitch
          :on="configBool(f.key)"
          @toggle="emit('setConfig', f.key, !configBool(f.key))"
        />
      </div>

      <template v-for="group in SETTING_GROUPS" :key="group.i18nKey">
        <h3 class="mt-5" :class="[sectionTitle]">
          {{ $t(`settings.${group.i18nKey}`) }}
        </h3>
        <p v-if="group.hintKey" class="mb-1.5 text-[10px] text-tcu-txt-dim">
          {{ $t(`settings.${group.hintKey}`) }}
        </p>
        <SettingSlider
          v-for="key in group.keys"
          :key="key"
          :label="$t(`settings.${sliderDef(key)?.i18nKey ?? key}`)"
          :config-key="key"
          :value="configValue(key)"
          :min="sliderDef(key)?.min ?? 0"
          :max="sliderDef(key)?.max ?? 100"
          :step="sliderDef(key)?.step ?? 1"
          :unit="sliderDef(key)?.unit"
          @input="emit('setConfig', key, $event)"
        />
      </template>

      <button
        type="button"
        class="mt-4" :class="[actionBtnDanger]"
        @click="() => { if (confirm($t('settings.resetConfirm'))) emit('resetConfig') }"
      >
        {{ $t('settings.reset') }}
      </button>
      <div class="mt-1 text-center text-[10px] text-tcu-txt-dim">
        {{ $t('settings.autosave') }}
      </div>
    </div>

    <div v-show="activeTab === 'stats'">
      <h3 :class="sectionTitle">
        {{ $t('stats.title') }}
      </h3>
      <template v-if="statsRows">
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.duration') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.duration }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.totalShifts') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.total }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.upshifts') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.upshifts }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.downshifts') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.downshifts }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.kickdowns') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.kickdowns }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.brakeDowns') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.brakeDowns }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.predictives') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.predictives }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.launches') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.launches }}</span>
        </div>
        <h3 class="mt-5" :class="[sectionTitle]">
          {{ $t('stats.performance') }}
        </h3>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.peakRpm') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.peakRpm }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.peakSpeed') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.peakSpeed }} km/h</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.peakGLat') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.peakGLat }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.peakGLon') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.peakGLon }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.peakPower') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.peakPower }} kW</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.avgThrottle') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.avgThr }}%</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.carsDriven') }}</span><span class="font-mono font-semibold text-tcu-txt">{{ statsRows.cars }}</span>
        </div>
        <h3 class="mt-5" :class="[sectionTitle]">
          {{ $t('stats.learning') }}
        </h3>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.gearRatios') }}</span>
          <span class="font-mono font-semibold text-tcu-txt">{{ statsRows.calib ? $t('stats.learned') : $t('stats.learningStatus') }}</span>
        </div>
        <div :class="statRow">
          <span class="text-tcu-txt-dim">{{ $t('stats.powerCurve') }}</span>
          <span class="font-mono font-semibold text-tcu-txt">{{ statsRows.powerLearned ? $t('stats.learned') : $t('stats.learningStatus') }}</span>
        </div>
      </template>
    </div>

    <div v-show="activeTab === 'history'">
      <h3 :class="sectionTitle">
        {{ $t('history.title') }}
      </h3>
      <div class="flex max-h-60 flex-col gap-1 overflow-y-auto">
        <div v-if="historyItems.length === 0" class="py-5 text-center text-xs text-tcu-txt-dim">
          {{ $t('history.empty') }}
        </div>
        <div
          v-for="(h, i) in historyItems"
          :key="i"
          class="grid grid-cols-[auto_auto_1fr_auto] items-center gap-2.5 rounded-md border border-tcu-border bg-tcu-bg-1 px-2.5 py-1.5 font-mono text-[11px]"
        >
          <span class="text-sm font-bold" :class="h.action === 'UP' ? 'text-accent' : 'text-warn'">
            {{ h.action === 'UP' ? '↑' : '↓' }}
          </span>
          <span class="text-tcu-txt-muted">gear {{ h.gear }}</span>
          <span class="text-[10px] uppercase tracking-wide text-tcu-txt-dim">{{ h.reason || h.rule }}</span>
          <span class="text-right text-[10px] text-tcu-txt-dim">
            {{ new Date(h.ts * 1000).toTimeString().slice(0, 8) }} · {{ h.rpm_pct }}% · {{ h.throttle }}%T {{ h.brake }}%B
          </span>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'extras'">
      <h3 :class="sectionTitle">
        {{ $t('extras.profileTitle') }}
      </h3>
      <p class="mb-2 text-[11px] leading-snug text-tcu-txt-dim">
        {{ $t('extras.profileHint') }}
      </p>
      <div class="mt-2 grid grid-cols-2 gap-1.5">
        <button type="button" :class="[actionBtn, actionBtnCompact]" @click="emit('exportProfile')">
          {{ $t('extras.export') }}
        </button>
        <button type="button" :class="[actionBtn, actionBtnCompact]" @click="emit('openImport')">
          {{ $t('extras.import') }}
        </button>
      </div>
      <h3 class="mt-6" :class="[sectionTitle]">
        {{ $t('extras.hotkeys') }}
      </h3>
      <p class="mb-2 text-[11px] text-tcu-txt-dim">
        {{ $t('extras.hotkeyHint') }}
      </p>
      <div v-for="h in HOTKEY_FIELDS" :key="h.key" class="grid grid-cols-[1fr_auto] items-center gap-2 py-1.5">
        <span class="text-xs text-tcu-txt-muted">{{ $t(`extras.${h.i18nKey}`) }}</span>
        <input
          type="text"
          :class="hotkeyInput"
          :value="configText(h.key)"
          maxlength="6"
          :placeholder="h.placeholder"
          @change="emit('setConfig', h.key, hotkeyInputValue($event))"
        >
      </div>
      <h3 class="mt-6" :class="[sectionTitle]">
        {{ $t('extras.fullTuning') }}
      </h3>
      <SettingSlider
        v-for="s in extrasSliders"
        :key="s.key"
        :label="$t(`settings.${s.i18nKey}`)"
        :config-key="s.key"
        :value="configValue(s.key)"
        :min="s.min"
        :max="s.max"
        :step="s.step ?? 1"
        :unit="s.unit"
        @input="emit('setConfig', s.key, $event)"
      />
    </div>
  </div>
</template>
