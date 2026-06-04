<script setup lang="ts">
  import {
    NButton,
    NCard,
    NFlex,
    NGrid,
    NGridItem,
    NRadioButton,
    NRadioGroup,
    NSelect,
    NTag,
    NText,
  } from 'naive-ui'
  import { inject } from 'vue'
  import { settingsContextKey } from './context'
  import { useSettingsLogs } from './settings-logs'

  const ctx = inject(settingsContextKey)!
  const { t, store } = ctx
  const {
    terminalHost,
    logView,
    recordMode,
    autoScroll,
    telemetryStreaming,
    isRecording,
    logStatusLabel,
    logModeLabel,
    logFileLabel,
    logFormat,
    startRecording,
    stopRecording,
    stopAsFusionSnapshot,
    toggleAutoScroll,
    toggleTelemetryStreaming,
    formatOptions,
  } = useSettingsLogs(ctx)
</script>

<template>
  <NFlex vertical :size="16">
    <NCard :title="t('logs.recordingTitle')" size="small" :bordered="false">
      <NGrid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" item-responsive>
        <NGridItem>
          <div class="log-stat">
            <NText depth="3">{{ t('logger.status') }}</NText>
            <NTag :type="isRecording ? 'error' : 'default'" size="small" round :bordered="false">
              {{ logStatusLabel }}
            </NTag>
          </div>
        </NGridItem>
        <NGridItem>
          <div class="log-stat">
            <NText depth="3">{{ t('logger.mode') }}</NText>
            <NText code>{{ logModeLabel }}</NText>
          </div>
        </NGridItem>
        <NGridItem>
          <div class="log-stat">
            <NText depth="3">{{ t('logger.packets') }}</NText>
            <NText code>{{ store.logStatus.value?.packets ?? 0 }}</NText>
          </div>
        </NGridItem>
        <NGridItem>
          <div class="log-stat">
            <NText depth="3">{{ t('logger.size') }}</NText>
            <NText code>{{ store.logStatus.value?.size_kb ?? 0 }} KB</NText>
          </div>
        </NGridItem>
      </NGrid>

      <NFlex align="center" :size="10" wrap style="margin-top: 14px">
        <NRadioGroup v-model:value="recordMode" size="small" :disabled="isRecording">
          <NRadioButton value="events" :label="t('logger.startEvents')" />
          <NRadioButton value="all" :label="t('logger.startAll')" />
        </NRadioGroup>
        <NSelect
          v-model:value="logFormat"
          :options="formatOptions"
          size="small"
          :disabled="isRecording"
          style="width: 132px"
        />
        <NButton type="primary" size="small" :disabled="isRecording" @click="startRecording">
          {{ t('logs.startRecording') }}
        </NButton>
        <NButton type="error" ghost size="small" :disabled="!isRecording" @click="stopRecording">
          {{ t('logs.stopSaveFile') }}
        </NButton>
        <NButton
          type="warning"
          ghost
          size="small"
          :disabled="!isRecording"
          @click="stopAsFusionSnapshot"
        >
          {{ t('logs.stopSaveFusionSnapshot') }}
        </NButton>
      </NFlex>

      <NText depth="3" class="log-file"> {{ t('logs.currentFile') }} {{ logFileLabel }} </NText>
      <NText depth="3" class="log-file">
        {{ t('logger.hint') }}
      </NText>
    </NCard>

    <NCard size="small" :bordered="false" class="log-console-card">
      <template #header>
        <NFlex justify="space-between" align="center">
          <NRadioGroup v-model:value="logView" size="small" class="log-view-tabs">
            <NRadioButton value="system" :label="t('logs.systemLogs')" />
            <NRadioButton value="telemetry" :label="t('logs.telemetryLogs')" />
          </NRadioGroup>
          <NFlex :size="8" align="center">
            <NButton
              v-if="logView === 'telemetry'"
              size="tiny"
              :type="telemetryStreaming ? 'success' : 'default'"
              secondary
              @click="toggleTelemetryStreaming"
            >
              {{
                telemetryStreaming
                  ? t('logs.telemetryStreamingOn')
                  : t('logs.telemetryStreamingOff')
              }}
            </NButton>
            <NButton size="tiny" secondary @click="toggleAutoScroll">
              {{ autoScroll ? t('logs.autoScroll') : t('logs.scrollLock') }}
            </NButton>
          </NFlex>
        </NFlex>
      </template>

      <div ref="terminalHost" class="log-terminal" />
    </NCard>
  </NFlex>
</template>

<style scoped>
  .log-stat {
    display: flex;
    min-height: 54px;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.34);
    padding: 10px 12px;
    font-weight: 400;
  }

  .log-file {
    display: block;
    margin-top: 8px;
    font-size: 11px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }

  .log-console-card :deep(.n-card__content) {
    padding: 0;
  }

  .log-view-tabs :deep(.n-radio-button__label) {
    font-weight: 400;
  }

  .log-terminal {
    height: 420px;
    overflow: hidden;
    border-radius: 0 0 10px 10px;
    background: #05070b;
    padding: 10px;
  }

  .log-terminal :deep(.xterm) {
    height: 100%;
    font-weight: 400;
  }
</style>
