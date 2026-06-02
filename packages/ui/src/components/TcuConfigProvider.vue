<script setup lang="ts">
  import {
    darkTheme,
    dateEnUS,
    dateZhCN,
    enUS,
    lightTheme,
    NConfigProvider,
    NDialogProvider,
    NMessageProvider,
    zhCN,
  } from 'naive-ui'
  import { computed } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { tcuDarkThemeOverrides, tcuThemeOverrides } from '../theme'

  const props = withDefaults(
    defineProps<{
      dark?: boolean
    }>(),
    { dark: false },
  )

  const { locale } = useI18n()

  const naiveLocale = computed(() => (locale.value === 'zh-CN' ? zhCN : enUS))
  const naiveDateLocale = computed(() => (locale.value === 'zh-CN' ? dateZhCN : dateEnUS))
  const theme = computed(() => (props.dark ? darkTheme : lightTheme))
  const overrides = computed(() => (props.dark ? tcuDarkThemeOverrides : tcuThemeOverrides))
</script>

<template>
  <NConfigProvider
    :theme="theme"
    :theme-overrides="overrides"
    :locale="naiveLocale"
    :date-locale="naiveDateLocale"
    style="height: 100%"
  >
    <NMessageProvider>
      <NDialogProvider>
        <slot />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>
