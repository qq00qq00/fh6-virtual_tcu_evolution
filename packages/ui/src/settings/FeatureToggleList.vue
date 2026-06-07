<script setup lang="ts">
  import type { FeatureToggle } from '@virtual-tcu/shared/config/settings'
  import { InformationCircleOutline } from '@vicons/ionicons5'
  import { NFlex, NIcon, NSwitch, NText, NTooltip } from 'naive-ui'
  import { useI18n } from 'vue-i18n'

  withDefaults(
    defineProps<{
      toggles: FeatureToggle[]
      configBool: (key: string) => boolean
      columns?: 1 | 2
    }>(),
    { columns: 2 },
  )

  const emit = defineEmits<{
    setConfig: [key: string, value: boolean]
  }>()

  const { t } = useI18n()
</script>

<template>
  <div
    class="feature-toggle-list"
    :class="columns === 2 ? 'feature-toggle-list--grid' : 'feature-toggle-list--stack'"
  >
    <NFlex
      v-for="f in toggles"
      :key="f.key"
      class="feature-toggle-list__row"
      justify="space-between"
      align="center"
    >
      <NFlex align="center" :size="6" :wrap="false">
        <NText>{{ t(`settings.${f.i18nKey}`) }}</NText>
        <NTooltip placement="top" :style="{ maxWidth: '280px' }">
          <template #trigger>
            <NIcon
              :component="InformationCircleOutline"
              :size="15"
              class="feature-toggle-list__hint"
              aria-hidden="true"
            />
          </template>
          {{ t(`settings.hints.${f.hintKey}`) }}
        </NTooltip>
      </NFlex>
      <NSwitch :value="configBool(f.key)" @update:value="emit('setConfig', f.key, $event)" />
    </NFlex>
  </div>
</template>

<style scoped>
  .feature-toggle-list--grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 16px;
  }

  @media (max-width: 640px) {
    .feature-toggle-list--grid {
      grid-template-columns: 1fr;
    }
  }

  .feature-toggle-list--stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .feature-toggle-list__hint {
    color: var(--n-text-color-3, #888);
    cursor: help;
    flex-shrink: 0;
    opacity: 0.75;
    transition: opacity 0.15s ease;
  }

  .feature-toggle-list__hint:hover {
    opacity: 1;
  }
</style>
