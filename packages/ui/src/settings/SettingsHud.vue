<script setup lang="ts">
  import { HUD_TEMPLATES } from '@virtual-tcu/shared/config/hud'
  import { NCard, NFlex, NRadioButton, NRadioGroup, NText } from 'naive-ui'
  import { computed, inject } from 'vue'
  import { settingsContextKey } from './context'

  const ctx = inject(settingsContextKey)!
  const { t, store } = ctx

  const templateValue = computed({
    get: () => {
      const v = store.config.hud_template
      return typeof v === 'string' ? v : 'classic'
    },
    set: (v: string) => store.setConfig('hud_template', v),
  })

  const templateOptions = computed(() =>
    HUD_TEMPLATES.map((opt) => ({
      value: opt.value,
      label: t(`electronApp.${opt.i18nKey}`),
    })),
  )
</script>

<template>
  <NCard :title="t('electronApp.hudTitle')" size="small" :bordered="false">
    <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 12px">
      {{ t('electronApp.hudHint') }}
    </NText>
    <NRadioGroup v-model:value="templateValue" size="small">
      <NFlex :size="8" wrap>
        <NRadioButton
          v-for="opt in templateOptions"
          :key="opt.value"
          :value="opt.value"
          :label="opt.label"
        />
      </NFlex>
    </NRadioGroup>
  </NCard>
</template>
