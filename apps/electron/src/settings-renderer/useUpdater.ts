import type { UpdaterStatus } from '../preload/main'
import { onMounted, onUnmounted, ref } from 'vue'
import { GITHUB_REPO_URL, githubReleaseUrl } from './github'

export type UpdaterState =
  | { kind: 'idle' }
  | { kind: 'checking' }
  | { kind: 'available'; version: string; releaseNotes: string }
  | { kind: 'not-available' }
  | { kind: 'progress'; percent: number; version: string }
  | { kind: 'downloaded'; version: string }
  | { kind: 'error'; message: string }

function formatReleaseNotes(notes: unknown): string {
  if (!notes) return ''
  if (typeof notes === 'string') return notes.trim()
  if (Array.isArray(notes)) {
    return notes
      .map((entry) => {
        if (entry && typeof entry === 'object' && 'note' in entry)
          return String((entry as { note: string }).note).trim()
        return String(entry).trim()
      })
      .filter(Boolean)
      .join('\n\n')
  }
  return String(notes).trim()
}

export function useUpdater() {
  const state = ref<UpdaterState>({ kind: 'idle' })
  const currentVersion = ref<string>('')
  const showUpdateModal = ref(false)
  const pendingVersion = ref('')
  const pendingReleaseNotes = ref('')
  let unsubscribe: (() => void) | null = null
  let pendingVersionForProgress = ''

  function openUpdateModal(version: string, releaseNotes: string) {
    pendingVersion.value = version
    pendingReleaseNotes.value = releaseNotes
    showUpdateModal.value = true
  }

  function applyStatus(status: UpdaterStatus) {
    switch (status.kind) {
      case 'checking':
        state.value = { kind: 'checking' }
        break
      case 'available': {
        const version = status.info?.version ?? ''
        const releaseNotes = formatReleaseNotes(status.info?.releaseNotes)
        pendingVersionForProgress = version
        state.value = { kind: 'available', version, releaseNotes }
        openUpdateModal(version, releaseNotes)
        break
      }
      case 'not-available':
        state.value = { kind: 'not-available' }
        break
      case 'progress':
        state.value = {
          kind: 'progress',
          percent: Math.round(status.info?.percent ?? 0),
          version: pendingVersionForProgress,
        }
        break
      case 'downloaded': {
        const version = status.info?.version ?? pendingVersionForProgress
        state.value = { kind: 'downloaded', version }
        pendingVersion.value = version
        showUpdateModal.value = true
        break
      }
      case 'error':
        state.value = { kind: 'error', message: status.error ?? 'Unknown error' }
        break
    }
  }

  onMounted(async () => {
    if (!window.tcu) return
    currentVersion.value = await window.tcu.getAppVersion()
    unsubscribe = window.tcu.onUpdaterStatus(applyStatus)
  })

  onUnmounted(() => unsubscribe?.())

  async function check() {
    state.value = { kind: 'checking' }
    const r = await window.tcu?.checkForUpdates()
    if (r && !r.ok && r.error) state.value = { kind: 'error', message: r.error }
  }

  async function download() {
    if (!window.tcu) return
    const version =
      state.value.kind === 'available'
        ? state.value.version
        : pendingVersion.value || pendingVersionForProgress
    if (version) pendingVersionForProgress = version
    showUpdateModal.value = true
    const r = await window.tcu.downloadUpdate()
    if (r && !r.ok && r.error) state.value = { kind: 'error', message: r.error }
  }

  function dismissModal() {
    showUpdateModal.value = false
  }

  function openReleasePage() {
    const version =
      pendingVersion.value ||
      pendingVersionForProgress ||
      (state.value.kind === 'available' ? state.value.version : '') ||
      (state.value.kind === 'downloaded' ? state.value.version : '')
    const url = version ? githubReleaseUrl(version) : `${GITHUB_REPO_URL}/releases/latest`
    void window.tcu?.openExternal(url)
  }

  function install() {
    window.tcu?.quitAndInstallUpdate()
  }

  return {
    state,
    currentVersion,
    showUpdateModal,
    pendingVersion,
    pendingReleaseNotes,
    check,
    download,
    dismissModal,
    openReleasePage,
    install,
  }
}
