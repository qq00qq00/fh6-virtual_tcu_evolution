/**
 * Python backend spawn, health probing, and serialized stop/restart.
 */

import type { ChildProcess } from 'node:child_process'
import type { BackendEndpoints } from './backend-config'
import { execFile, spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import * as readline from 'node:readline'
import { PassThrough } from 'node:stream'
import { promisify } from 'node:util'
import { is } from '@electron-toolkit/utils'
import { app } from 'electron'
import { endpointsFromHttpUrl, parseWebUiUrl, resolveBackendEndpoints } from './backend-config'

const execFileAsync = promisify(execFile)
const READY_MARKER = '[backend-ready]'
const READY_TIMEOUT_MS = 30_000
const STOP_TIMEOUT_MS = 5_000
const HEALTH_POLL_MS = 200
const PORT_RELEASE_MS = 300

type BackendPhase = 'idle' | 'starting' | 'ready' | 'stopping'

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

function resolveBackendCommand(): { cmd: string; args: string[]; cwd: string } {
  const packagedExe = join(process.resourcesPath, 'backend', 'VirtualTCU.exe')
  if (app.isPackaged && existsSync(packagedExe)) {
    return {
      cmd: packagedExe,
      args: ['--backend-only'],
      cwd: join(process.resourcesPath, 'backend'),
    }
  }

  if (!is.dev || process.env.TCU_USE_FROZEN_BACKEND === '1') {
    const devExe = join(__dirname, '..', '..', '..', '..', 'dist', 'VirtualTCU', 'VirtualTCU.exe')
    if (existsSync(devExe)) {
      return {
        cmd: devExe,
        args: ['--backend-only'],
        cwd: join(__dirname, '..', '..', '..', '..', 'dist', 'VirtualTCU'),
      }
    }
  }

  return {
    cmd: 'python',
    args: ['-m', 'virtual_tcu', '--backend-only'],
    cwd: join(__dirname, '..', '..', '..', '..'),
  }
}

async function probeBackendHttp(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(500) })
    // Any HTTP response means aiohttp is listening (200 dashboard, 503 missing dist).
    return res.status > 0
  } catch {
    return false
  }
}

async function killBackendProcess(pid: number, proc?: ChildProcess | null): Promise<void> {
  if (process.platform === 'win32') {
    try {
      await execFileAsync('taskkill', ['/F', '/T', '/PID', String(pid)], { windowsHide: true })
    } catch {
      // Process already exited.
    }
    return
  }

  try {
    if (proc && !proc.killed) proc.kill('SIGTERM')
    else process.kill(pid, 'SIGTERM')
  } catch {
    // Already dead.
  }

  await sleep(2000)

  try {
    process.kill(-pid, 'SIGKILL')
  } catch {
    try {
      process.kill(pid, 'SIGKILL')
    } catch {
      // Already dead.
    }
  }
}

export class BackendLifecycle {
  private backend: ChildProcess | null = null
  private backendPid: number | null = null
  private phase: BackendPhase = 'idle'
  private lifecycleChain = Promise.resolve()
  private startPromise: Promise<void> | null = null
  private endpoints: BackendEndpoints = resolveBackendEndpoints()
  private dataCwd = ''
  private ready = false
  private markerSeen = false
  private isQuitting = false
  private onReady: (() => void) | null = null
  private onExit: ((code: number | null, signal: NodeJS.Signals | null) => void) | null = null

  setQuitting(value: boolean): void {
    this.isQuitting = value
  }

  setOnReady(callback: () => void): void {
    this.onReady = callback
  }

  setOnExit(callback: (code: number | null, signal: NodeJS.Signals | null) => void): void {
    this.onExit = callback
  }

  getEndpoints(): BackendEndpoints {
    return this.endpoints
  }

  refreshEndpoints(): void {
    this.endpoints = resolveBackendEndpoints(this.dataCwd)
  }

  getDataCwd(): string {
    return this.dataCwd
  }

  isReady(): boolean {
    return this.ready
  }

  withLock<T>(fn: () => Promise<T>): Promise<T> {
    const run = this.lifecycleChain.then(fn) as Promise<T>
    this.lifecycleChain = run.then(
      () => undefined,
      () => undefined,
    )
    return run
  }

  async restart(): Promise<void> {
    return this.withLock(async () => {
      await this.stopInternal()
      await this.portReleaseDelay()
      await this.start()
    })
  }

  async start(): Promise<void> {
    if (this.phase === 'ready' && this.backend && this.backendPid != null) {
      return
    }
    if (this.startPromise) return this.startPromise

    this.startPromise = this.startInternal().finally(() => {
      this.startPromise = null
    })
    return this.startPromise
  }

  async stop(): Promise<void> {
    return this.withLock(() => this.stopInternal())
  }

  async forceStop(): Promise<void> {
    const pid = this.backendPid
    const proc = this.backend
    this.clearBackendState()
    if (pid != null) await killBackendProcess(pid, proc)
  }

  private async portReleaseDelay(): Promise<void> {
    if (process.platform === 'win32') await sleep(PORT_RELEASE_MS)
  }

  private clearBackendState(): void {
    this.backend = null
    this.backendPid = null
    this.ready = false
    this.markerSeen = false
    if (this.phase !== 'stopping') this.phase = 'idle'
  }

  private markReady(): void {
    if (this.ready) return
    this.ready = true
    this.phase = 'ready'
    if (!this.markerSeen) this.endpoints = resolveBackendEndpoints(this.dataCwd)
    this.onReady?.()
  }

  private async startInternal(): Promise<void> {
    this.phase = 'starting'
    this.ready = false
    this.markerSeen = false

    const { cmd, args, cwd } = resolveBackendCommand()
    this.dataCwd = cwd
    this.endpoints = resolveBackendEndpoints(cwd)
    console.log(`[backend] spawn: ${cmd} ${args.join(' ')}`)

    let proc: ChildProcess
    try {
      proc = spawn(cmd, args, {
        cwd,
        windowsHide: true,
        stdio: ['ignore', 'pipe', 'pipe'],
      })
    } catch (err) {
      this.phase = 'idle'
      throw err
    }

    this.backend = proc
    this.backendPid = proc.pid ?? null

    return new Promise<void>((resolveStart, rejectStart) => {
      let settled = false

      const stdoutPass = new PassThrough()
      proc.stdout?.pipe(stdoutPass)
      if (is.dev) stdoutPass.pipe(process.stdout)

      const rl = readline.createInterface({ input: stdoutPass, terminal: false })

      let timeout: ReturnType<typeof setTimeout>
      let healthPoll: ReturnType<typeof setInterval>

      const cleanupWaiters = () => {
        clearTimeout(timeout)
        clearInterval(healthPoll)
        rl.close()
      }

      const finishReady = () => {
        if (settled) return
        settled = true
        cleanupWaiters()
        this.markReady()
        resolveStart()
      }

      const fail = (err: Error) => {
        if (settled) return
        settled = true
        cleanupWaiters()
        this.phase = 'idle'
        rejectStart(err)
      }

      timeout = setTimeout(() => {
        void (async () => {
          const pid = this.backendPid
          const hung = this.backend
          this.clearBackendState()
          if (pid != null) await killBackendProcess(pid, hung)
          fail(new Error('Backend did not become ready within 30s'))
        })()
      }, READY_TIMEOUT_MS)

      healthPoll = setInterval(() => {
        if (settled) return
        void probeBackendHttp(this.endpoints.url).then((ok) => {
          if (ok) finishReady()
        })
      }, HEALTH_POLL_MS)

      rl.on('line', (line) => {
        if (line.length === 0) return
        const parsedUrl = parseWebUiUrl(line)
        if (parsedUrl) {
          this.endpoints = endpointsFromHttpUrl(parsedUrl, resolveBackendEndpoints(this.dataCwd))
        }
        if (line.includes(READY_MARKER)) {
          this.markerSeen = true
          finishReady()
        }
      })

      proc.stderr?.pipe(process.stderr)

      proc.on('exit', (code, signal) => {
        console.log(`[backend] exited code=${code} signal=${signal}`)
        cleanupWaiters()

        if (proc.pid === this.backendPid) {
          this.clearBackendState()
          this.phase = 'idle'
        }

        if (!settled) {
          fail(new Error(`Backend exited before ready (code ${code})`))
        } else if (!this.isQuitting) {
          this.onExit?.(code, signal)
        }
      })

      proc.on('error', (err) => {
        console.error('[backend] spawn error:', err)
        fail(err)
      })
    })
  }

  private async stopInternal(): Promise<void> {
    const proc = this.backend
    const pid = this.backendPid
    if (!proc || pid == null) {
      this.clearBackendState()
      this.phase = 'idle'
      return
    }

    this.phase = 'stopping'
    this.backend = null
    this.backendPid = null
    this.ready = false

    await new Promise<void>((resolve) => {
      let settled = false
      let forceTimeout: ReturnType<typeof setTimeout>

      const done = () => {
        if (settled) return
        settled = true
        clearTimeout(forceTimeout)
        this.phase = 'idle'
        resolve()
      }

      forceTimeout = setTimeout(() => {
        console.warn(`[backend] exit event did not fire for pid ${pid} - resolving anyway`)
        done()
      }, STOP_TIMEOUT_MS)

      proc.once('exit', done)
      void killBackendProcess(pid, proc)
    })
  }
}
