<script setup lang="ts">
  import {
    CLUTCH_ASSIST_FIELDS,
    CLUTCH_TIMING_SLIDERS,
    VJOY_BUTTON_OPTIONS,
    VJOY_SHIFT_BUTTON_FIELDS,
  } from '@virtual-tcu/shared/config/settings'
  import {
    NButton,
    NCard,
    NFlex,
    NGrid,
    NGridItem,
    NInput,
    NSelect,
    NSlider,
    NSwitch,
    NText,
  } from 'naive-ui'
  import { computed, inject } from 'vue'
  import { settingsContextKey } from './context'
  import UdpHubTargetsField from './UdpHubTargetsField.vue'

  const ctx = inject(settingsContextKey)!
  const {
    t,
    store,
    hotkeyFields,
    shiftKeyFields,
    outputModeOptions,
    advancedSliders,
    networkDraftHost,
    networkDraftWebPort,
    networkDraftUdpPort,
    networkDraftUdpHubEnabled,
    networkDraftUdpHubTargetTags,
    networkUdpHubTagError,
    networkDirty,
    networkApplyError,
    networkApplyOk,
    networkApplying,
    allowsNetworkBindHostInput,
    allowsNetworkPortInput,
    allowsNetworkUdpHubTargetInput,
    setNetworkUdpHubEnabled,
    setNetworkUdpHubTargetTags,
    onNetworkUdpHubTagCreate,
    applyNetworkSettings,
    onExportProfile,
    onOpenImport,
    restartBackend,
    configNumber,
    configBool,
    configText,
    sliderUnit,
  } = ctx

  const outputModeValue = computed(() => {
    const v = (store.config as Record<string, unknown>).output_mode
    return typeof v === 'string' && v === 'vjoy' ? v : 'keyboard'
  })

  const outputModeOptionsComputed = computed(() =>
    outputModeOptions.map((o) => ({
      label: t(`extras.${o.i18nKey}`),
      value: o.value,
    })),
  )

  function onOutputModeChange(v: string) {
    store.setConfig('output_mode', v)
  }
</script>

<template>
  <NFlex vertical :size="16">
    <NCard :title="t('extras.networkTitle')" size="small" :bordered="false">
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
        {{ t('extras.networkHint') }}
      </NText>
      <NGrid :cols="2" :x-gap="16" :y-gap="10">
        <NGridItem>
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t('extras.webHost') }}</NText>
            <NInput
              v-model:value="networkDraftHost"
              placeholder="0.0.0.0"
              maxlength="15"
              :allow-input="allowsNetworkBindHostInput"
              size="small"
              style="width: 120px; font-family: ui-monospace, monospace"
            />
          </NFlex>
        </NGridItem>
        <NGridItem>
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t('extras.webPort') }}</NText>
            <NInput
              v-model:value="networkDraftWebPort"
              placeholder="8765"
              maxlength="5"
              :allow-input="allowsNetworkPortInput"
              size="small"
              style="width: 120px; font-family: ui-monospace, monospace"
            />
          </NFlex>
        </NGridItem>
        <NGridItem>
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t('extras.udpPort') }}</NText>
            <NInput
              v-model:value="networkDraftUdpPort"
              placeholder="5555"
              maxlength="5"
              :allow-input="allowsNetworkPortInput"
              size="small"
              style="width: 120px; font-family: ui-monospace, monospace"
            />
          </NFlex>
        </NGridItem>
      </NGrid>
      <NText depth="3" style="font-size: 11px; display: block; margin-top: 8px">
        {{ t('extras.udpPortHint') }}
      </NText>
      <UdpHubTargetsField
        style="margin-top: 12px"
        :enabled="networkDraftUdpHubEnabled"
        :tags="networkDraftUdpHubTargetTags"
        :tag-error="networkUdpHubTagError"
        :allows-input="allowsNetworkUdpHubTargetInput"
        :on-create-tag="onNetworkUdpHubTagCreate"
        :enabled-label="t('extras.udpHubEnabled')"
        :targets-label="t('extras.udpHubTargets')"
        :placeholder="t('extras.udpHubTargetsPlaceholder')"
        :hint="t('extras.udpHubHint')"
        @update:enabled="setNetworkUdpHubEnabled"
        @update:tags="setNetworkUdpHubTargetTags"
      />
      <NFlex :size="8" align="center" style="margin-top: 12px">
        <NButton
          type="primary"
          size="small"
          :disabled="!networkDirty || networkApplying"
          :loading="networkApplying"
          @click="applyNetworkSettings"
        >
          {{ t('extras.saveAndRestart') }}
        </NButton>
        <NText v-if="networkApplyOk" depth="3" style="font-size: 12px; color: #16a34a">
          {{ t('extras.networkApplyOk') }}
        </NText>
        <NText v-else-if="networkApplyError" depth="3" style="font-size: 12px; color: #dc2626">
          {{ t(`extras.networkErrors.${networkApplyError}`) }}
        </NText>
      </NFlex>
    </NCard>

    <NCard :title="t('extras.profileTitle')" size="small" :bordered="false">
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 12px">
        {{ t('extras.profileHint') }}
      </NText>
      <NFlex :size="8">
        <NButton @click="onExportProfile">
          {{ t('extras.export') }}
        </NButton>
        <NButton @click="onOpenImport">
          {{ t('extras.import') }}
        </NButton>
      </NFlex>
    </NCard>

    <NCard :title="t('extras.outputMode')" size="small" :bordered="false">
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
        {{ t('extras.outputModeHint') }}
      </NText>
      <NSelect
        :value="outputModeValue"
        :options="outputModeOptionsComputed"
        size="small"
        style="width: 200px"
        @update:value="onOutputModeChange"
      />
      <template v-if="outputModeValue === 'vjoy'">
        <NText depth="3" style="font-size: 12px; display: block; margin: 12px 0 8px">
          {{ t('extras.vjoyHint') }}
        </NText>
        <NFlex vertical :size="12">
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t('extras.vjoyDirectShift') }}</NText>
            <NSwitch
              :value="configBool('vjoy_direct_shift')"
              @update:value="(v: boolean) => store.setConfig('vjoy_direct_shift', v)"
            />
          </NFlex>
          <NText depth="3" style="font-size: 11px">
            {{
              configBool('vjoy_direct_shift')
                ? t('extras.vjoyDirectShiftOn')
                : t('extras.vjoyDirectShiftOff')
            }}
          </NText>
          <template v-if="!configBool('vjoy_direct_shift')">
            <NFlex
              v-for="g in VJOY_SHIFT_BUTTON_FIELDS"
              :key="g.key"
              justify="space-between"
              align="center"
              :size="8"
            >
              <NText>{{ t(`extras.${g.i18nKey}`) }}</NText>
              <NSelect
                :value="configText(g.key) || g.placeholder"
                :options="VJOY_BUTTON_OPTIONS.map((o) => ({ label: o.label, value: o.value }))"
                size="small"
                style="width: 140px"
                @update:value="(v: string) => store.setConfig(g.key, v)"
              />
            </NFlex>
          </template>
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t('extras.vjoyUseClutch') }}</NText>
            <NSwitch
              :value="configBool('vjoy_use_clutch')"
              @update:value="(v: boolean) => store.setConfig('vjoy_use_clutch', v)"
            />
          </NFlex>
          <NFlex
            v-if="configBool('vjoy_use_clutch')"
            justify="space-between"
            align="center"
            :size="8"
          >
            <NText>{{ t('extras.vjoyClutchKey') }}</NText>
            <NSelect
              :value="configText('vjoy_clutch_key') || 'B12'"
              :options="VJOY_BUTTON_OPTIONS.map((o) => ({ label: o.label, value: o.value }))"
              size="small"
              style="width: 140px"
              @update:value="(v: string) => store.setConfig('vjoy_clutch_key', v)"
            />
          </NFlex>
        </NFlex>
      </template>
      <NFlex :size="8" align="center" style="margin-top: 10px">
        <NButton type="warning" size="small" @click="restartBackend()">
          {{ t('extras.saveAndRestart') }}
        </NButton>
        <NText depth="3" style="font-size: 11px; color: #d97706">
          {{ t('extras.outputModeRestart') }}
        </NText>
      </NFlex>
    </NCard>

    <NCard
      v-if="outputModeValue === 'keyboard'"
      :title="t('extras.shiftKeys')"
      size="small"
      :bordered="false"
    >
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
        {{ t('extras.shiftKeyHint') }}
      </NText>
      <NGrid :cols="2" :x-gap="16" :y-gap="10">
        <NGridItem v-for="h1 in shiftKeyFields" :key="h1.key">
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t(`extras.${h1.i18nKey}`) }}</NText>
            <NInput
              :value="configText(h1.key)"
              :placeholder="h1.placeholder"
              size="small"
              style="width: 100px; font-family: ui-monospace, monospace"
              @update:value="(v) => store.setConfig(h1.key, v.trim().toLowerCase())"
            />
          </NFlex>
        </NGridItem>
      </NGrid>
      <NFlex justify="space-between" align="center" :size="8" style="margin-top: 16px">
        <NText>{{ t('extras.clutchAssist') }}</NText>
        <NSwitch
          :value="configBool('feat_clutch_assist')"
          @update:value="(v: boolean) => store.setConfig('feat_clutch_assist', v)"
        />
      </NFlex>
      <template v-if="configBool('feat_clutch_assist')">
        <NText depth="3" style="font-size: 11px; display: block; margin: 4px 0 12px">
          {{ t('extras.clutchAssistHint') }}
        </NText>
        <NFlex
          v-for="ck in CLUTCH_ASSIST_FIELDS"
          :key="ck.key"
          justify="space-between"
          align="center"
          :size="8"
        >
          <NText>{{ t(`extras.${ck.i18nKey}`) }}</NText>
          <NInput
            :value="configText(ck.key)"
            :placeholder="ck.placeholder"
            size="small"
            style="width: 100px; font-family: ui-monospace, monospace"
            @update:value="(v) => store.setConfig(ck.key, v.trim().toLowerCase())"
          />
        </NFlex>
        <NFlex vertical :size="14" style="margin-top: 12px">
          <div v-for="s in CLUTCH_TIMING_SLIDERS" :key="s.key">
            <NFlex justify="space-between" align="center" style="margin-bottom: 4px">
              <NText>{{ t(`extras.${s.i18nKey}`) }}</NText>
              <NText code style="font-family: ui-monospace, monospace">
                {{ configNumber(s.key) }}ms
              </NText>
            </NFlex>
            <NSlider
              :value="configNumber(s.key)"
              :min="s.min"
              :max="s.max"
              :step="s.step ?? 1"
              @update:value="(v) => store.setConfig(s.key, v)"
            />
          </div>
        </NFlex>
      </template>
    </NCard>

    <NCard :title="t('extras.hotkeys')" size="small" :bordered="false">
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
        {{ t('extras.hotkeyHint') }}
      </NText>
      <NGrid :cols="2" :x-gap="16" :y-gap="10">
        <NGridItem v-for="h1 in hotkeyFields" :key="h1.key">
          <NFlex justify="space-between" align="center" :size="8">
            <NText>{{ t(`extras.${h1.i18nKey}`) }}</NText>
            <NInput
              :value="configText(h1.key)"
              :placeholder="h1.placeholder"
              size="small"
              style="width: 100px; font-family: ui-monospace, monospace"
              @update:value="(v) => store.setConfig(h1.key, v.trim().toLowerCase())"
            />
          </NFlex>
        </NGridItem>
      </NGrid>
    </NCard>

    <NCard :title="t('extras.fullTuning')" size="small" :bordered="false">
      <NFlex vertical :size="14">
        <div v-for="s in advancedSliders" :key="s.key">
          <NFlex justify="space-between" align="center" style="margin-bottom: 4px">
            <NText>{{ t(`settings.${s.i18nKey}`) }}</NText>
            <NText code style="font-family: ui-monospace, monospace">
              {{ configNumber(s.key) }}{{ sliderUnit(s) }}
            </NText>
          </NFlex>
          <NSlider
            :value="configNumber(s.key)"
            :min="s.min"
            :max="s.max"
            :step="s.step ?? 1"
            @update:value="(v) => store.setConfig(s.key, v)"
          />
        </div>
      </NFlex>
    </NCard>
  </NFlex>
</template>
