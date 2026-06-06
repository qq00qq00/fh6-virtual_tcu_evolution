import type { Ref } from 'vue'
import type { UpdaterState } from './useUpdater'
import { computed } from 'vue'

export function useUpdateAvailableModal(options: {
  show: Ref<boolean>
  state: Ref<UpdaterState>
  pendingVersion: Ref<string>
  pendingReleaseNotes: Ref<string>
}) {
  const version = computed(() => {
    const s = options.state.value
    if (s.kind === 'available' || s.kind === 'progress' || s.kind === 'downloaded') return s.version
    return options.pendingVersion.value
  })

  const releaseNotes = computed(() => {
    if (options.state.value.kind === 'available') return options.state.value.releaseNotes
    return options.pendingReleaseNotes.value
  })

  const downloading = computed(() => options.state.value.kind === 'progress')
  const downloadPercent = computed(() =>
    options.state.value.kind === 'progress' ? options.state.value.percent : 0,
  )
  const downloaded = computed(() => options.state.value.kind === 'downloaded')
  const canDownload = computed(() => options.state.value.kind === 'available')

  return {
    version,
    releaseNotes,
    downloading,
    downloadPercent,
    downloaded,
    canDownload,
  }
}
