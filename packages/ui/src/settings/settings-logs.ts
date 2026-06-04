import type { Terminal } from '@xterm/xterm'
import type { SettingsContext } from './context'
import { Terminal as XtermTerminal } from '@xterm/xterm'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import '@xterm/xterm/css/xterm.css'

export type LogConsoleView = 'system' | 'telemetry'
export type LogRecordMode = 'events' | 'all'

export const LOG_FORMAT_OPTIONS = [
  { label: 'bin.gz', value: 'bin.gz' },
  { label: 'bin', value: 'bin' },
  { label: 'txt', value: 'txt' },
  { label: 'json', value: 'json' },
  { label: 'jsonl', value: 'jsonl' },
  { label: 'csv', value: 'csv' },
  { label: 'chart.html', value: 'csv_chart' },
  { label: 'summary', value: 'summary' },
]

const LEVEL_COLOR: Record<string, string> = {
  ERROR: '\x1B[31m',
  WARN: '\x1B[33m',
  DEBUG: '\x1B[90m',
  INFO: '\x1B[36m',
}

function terminalTime(ts: number): string {
  const date = new Date(ts)
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  const ms = String(date.getMilliseconds()).padStart(3, '0')
  return `${hh}:${mm}:${ss}.${ms}`
}

function sanitize(value: string): string {
  return value.replace(/\r?\n/g, '\r\n')
}

function formatSystemLine(log: { time: number; level: string; msg: string }): string {
  const color = LEVEL_COLOR[log.level] ?? LEVEL_COLOR.INFO
  return `\x1B[90m[${terminalTime(log.time)}]\x1B[0m ${color}[${log.level}]\x1B[0m ${sanitize(log.msg)}`
}

function formatTelemetryPacket(time: number, telemetry: Record<string, unknown>): string {
  const gear = telemetry.gear ?? '-'
  const speed = Number(telemetry.speed_kmh ?? 0).toFixed(1)
  const rpm = Math.round(Number(telemetry.rpm ?? 0))
  const rpmMax = Math.round(Number(telemetry.rpm_max ?? 0))
  const throttle = Math.round(Number(telemetry.throttle ?? 0) * 100)
  const brake = Math.round(Number(telemetry.brake ?? 0) * 100)
  const state = telemetry.tcu_state ?? 'UNKNOWN'
  return `\x1B[90m[${terminalTime(time)}]\x1B[0m gear=${gear} speed=${speed}km/h rpm=${rpm}/${rpmMax} throttle=${throttle}% brake=${brake}% state=${state}`
}

export function useSettingsLogs(ctx: SettingsContext) {
  const { t, store } = ctx
  const terminalHost = ref<HTMLElement | null>(null)
  const logView = ref<LogConsoleView>('system')
  const recordMode = ref<LogRecordMode>('events')
  const autoScroll = ref(true)
  const telemetryStreaming = ref(false)
  const telemetryLines = ref<string[]>([])
  let terminal: Terminal | null = null
  let renderedSystemCount = 0
  let renderedTelemetryCount = 0

  const isRecording = computed(() => !!store.logStatus.value?.recording)
  const logStatusLabel = computed(() =>
    isRecording.value ? t('logger.recording') : t('logger.stopped'),
  )
  const logModeLabel = computed(() => {
    const mode = store.logStatus.value?.mode
    return !mode || mode === 'off' ? '-' : mode
  })
  const logFileLabel = computed(() => store.logStatus.value?.file ?? t('logs.noActiveFile'))
  const logFormat = computed({
    get: () => String(store.config.log_output_format ?? store.logStatus.value?.format ?? 'bin.gz'),
    set: (value: string) => store.setConfig('log_output_format', value),
  })

  function writeLine(line: string) {
    terminal?.writeln(line)
    if (autoScroll.value) terminal?.scrollToBottom()
  }

  function clearTerminal() {
    terminal?.clear()
    terminal?.reset()
  }

  function renderSystemLogs() {
    if (!terminal) return
    const rows = store.systemLogs.value
    if (rows.length <= renderedSystemCount) {
      clearTerminal()
      rows.forEach((row) => writeLine(formatSystemLine(row)))
    } else {
      rows.slice(renderedSystemCount).forEach((row) => writeLine(formatSystemLine(row)))
    }
    renderedSystemCount = rows.length
  }

  function renderTelemetryLogs() {
    if (!terminal) return
    if (!telemetryStreaming.value) {
      clearTerminal()
      renderedTelemetryCount = telemetryLines.value.length
      writeLine(`\x1B[90m${t('logs.telemetryStreamOff')}\x1B[0m`)
      return
    }
    const rows = telemetryLines.value
    if (rows.length === 0) {
      clearTerminal()
      renderedTelemetryCount = 0
      writeLine(`\x1B[90m${t('logs.waitingTelemetryPackets')}\x1B[0m`)
      return
    }
    if (rows.length <= renderedTelemetryCount) {
      clearTerminal()
      rows.forEach((row) => writeLine(row))
    } else {
      rows.slice(renderedTelemetryCount).forEach((row) => writeLine(row))
    }
    renderedTelemetryCount = rows.length
  }

  function renderActiveView() {
    if (logView.value === 'system') {
      renderedSystemCount = 0
      renderSystemLogs()
    } else {
      renderTelemetryLogs()
    }
  }

  function startTerminal() {
    if (!terminalHost.value || terminal) return
    terminal = new XtermTerminal({
      convertEol: true,
      cursorBlink: false,
      disableStdin: true,
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
      fontSize: 12,
      lineHeight: 1.35,
      scrollback: 1000,
      theme: {
        background: '#05070b',
        foreground: '#d4d4d8',
        cursor: '#22c55e',
        selectionBackground: '#1f2937',
      },
    })
    terminal.open(terminalHost.value)
    terminal.resize(120, 24)
    renderActiveView()
  }

  function startRecording() {
    store.setConfig('log_output_format', logFormat.value)
    ctx.onLogStart(recordMode.value)
  }

  function stopRecording() {
    ctx.onLogStop('file')
  }

  function stopAsFusionSnapshot() {
    ctx.onLogStop('fusion_snapshot')
  }

  function toggleAutoScroll() {
    autoScroll.value = !autoScroll.value
    if (autoScroll.value) terminal?.scrollToBottom()
  }

  function toggleTelemetryStreaming() {
    telemetryStreaming.value = !telemetryStreaming.value
    if (telemetryStreaming.value) {
      telemetryLines.value = []
      renderedTelemetryCount = 0
    }
    if (logView.value === 'telemetry') renderTelemetryLogs()
  }

  watch(logView, () => renderActiveView())
  watch(
    () => {
      const last = store.systemLogs.value.at(-1)
      return `${store.systemLogs.value.length}:${last?.time ?? 0}:${last?.msg ?? ''}`
    },
    () => {
      if (logView.value === 'system') renderSystemLogs()
    },
  )
  watch(
    () => store.telemetry.value,
    (telemetry) => {
      if (!telemetryStreaming.value || !telemetry) return
      telemetryLines.value.push(
        formatTelemetryPacket(Date.now(), telemetry as Record<string, unknown>),
      )
      if (telemetryLines.value.length > 500) {
        telemetryLines.value.splice(0, telemetryLines.value.length - 500)
        renderedTelemetryCount = Math.min(renderedTelemetryCount, telemetryLines.value.length)
      }
      if (logView.value === 'telemetry') renderTelemetryLogs()
    },
  )

  nextTick(startTerminal)

  onBeforeUnmount(() => {
    terminal?.dispose()
    terminal = null
  })

  return {
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
    formatOptions: LOG_FORMAT_OPTIONS,
  }
}
