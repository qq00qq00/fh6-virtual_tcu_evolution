<script setup lang="ts">
  import { CloudDownloadOutline, LogoGithub } from '@vicons/ionicons5'
  import { NButton, NFlex, NIcon, NModal, NProgress, NScrollbar, NText } from 'naive-ui'
  import { useI18n } from 'vue-i18n'

  defineProps<{
    show: boolean
    version: string
    releaseNotes: string
    downloading: boolean
    downloadPercent: number
    downloaded: boolean
    canDownload: boolean
  }>()

  const emit = defineEmits<{
    'update:show': [value: boolean]
    download: []
    openGithub: []
    install: []
  }>()

  const { t } = useI18n()
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    :title="t('updater.modalTitle', { version: version ? `v${version}` : '' })"
    style="width: 520px; max-width: 92vw"
    :mask-closable="!downloading"
    :closable="!downloading"
    @update:show="(v) => emit('update:show', v)"
  >
    <NText depth="3" style="display: block; margin-bottom: 12px; font-size: 13px">
      {{ t('updater.modalHint') }}
    </NText>

    <div class="release-notes-wrap">
      <div class="release-notes-label">
        {{ t('updater.releaseNotes') }}
      </div>
      <NScrollbar style="max-height: 220px">
        <pre class="release-notes">{{ releaseNotes || t('updater.noReleaseNotes') }}</pre>
      </NScrollbar>
    </div>

    <div v-if="downloading" style="margin-top: 16px">
      <NText depth="3" style="font-size: 12px; display: block; margin-bottom: 8px">
        {{ t('updater.progress', { percent: downloadPercent }) }}
      </NText>
      <NProgress type="line" :percentage="downloadPercent" :show-indicator="true" />
    </div>

    <template #footer>
      <NFlex justify="end" :size="8">
        <template v-if="downloaded">
          <NButton @click="emit('update:show', false)">
            {{ t('updater.later') }}
          </NButton>
          <NButton type="primary" @click="emit('install')">
            {{ t('updater.installNow') }}
          </NButton>
        </template>
        <template v-else-if="downloading">
          <NButton disabled>
            {{ t('updater.downloading') }}
          </NButton>
        </template>
        <template v-else>
          <NButton @click="emit('update:show', false)">
            {{ t('updater.later') }}
          </NButton>
          <NButton @click="emit('openGithub')">
            <template #icon>
              <NIcon :component="LogoGithub" />
            </template>
            {{ t('updater.openGithub') }}
          </NButton>
          <NButton type="primary" :disabled="!canDownload" @click="emit('download')">
            <template #icon>
              <NIcon :component="CloudDownloadOutline" />
            </template>
            {{ t('updater.downloadDirect') }}
          </NButton>
        </template>
      </NFlex>
    </template>
  </NModal>
</template>

<style scoped>
  .release-notes-wrap {
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 8px;
    padding: 10px 12px;
    background: rgba(15, 23, 42, 0.35);
  }

  .release-notes-label {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 8px;
  }

  .release-notes {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: ui-sans-serif, system-ui, sans-serif;
    font-size: 13px;
    line-height: 1.55;
    color: #e2e8f0;
  }
</style>
