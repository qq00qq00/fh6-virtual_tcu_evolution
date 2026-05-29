/**
 * Launch the bundled ViGEmBus MSI after path + SHA-256 integrity checks.
 *
 * Update VIGEM_MSI_SHA256 when replacing driver/ViGEmBusSetup_x64.msi:
 *   shasum -a 256 driver/ViGEmBusSetup_x64.msi
 */

import { createHash } from 'node:crypto'
import { existsSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { app, shell } from 'electron'
import { projectRoot } from './backend-config'

export const VIGEM_MSI_FILENAME = 'ViGEmBusSetup_x64.msi'

/** SHA-256 of driver/ViGEmBusSetup_x64.msi in the repo. */
export const VIGEM_MSI_SHA256 = '5abbba8a4a07aaaeb50b4666183b2f243e0e5ad288026d2a9f3595ed237c4b28'

export function resolveVigemMsiPath(): string {
  if (app.isPackaged) {
    return join(process.resourcesPath, 'driver', VIGEM_MSI_FILENAME)
  }
  return join(projectRoot(), 'driver', VIGEM_MSI_FILENAME)
}

async function sha256File(path: string): Promise<string> {
  const data = await readFile(path)
  return createHash('sha256').update(data).digest('hex')
}

export async function launchVigemInstaller(): Promise<{ ok: boolean; error?: string }> {
  const msiPath = resolve(resolveVigemMsiPath())

  if (!existsSync(msiPath)) {
    console.error(`[install-vigembus] MSI not found at: ${msiPath}`)
    return { ok: false, error: `Installer not found: ${msiPath}` }
  }

  const hash = await sha256File(msiPath)
  if (hash !== VIGEM_MSI_SHA256) {
    console.error(`[install-vigembus] hash mismatch: expected ${VIGEM_MSI_SHA256}, got ${hash}`)
    return {
      ok: false,
      error: 'Installer integrity check failed. Reinstall Virtual TCU or update the app.',
    }
  }

  console.log(`[install-vigembus] launching: ${msiPath}`)
  const error = await shell.openPath(msiPath)
  if (error) {
    console.error(`[install-vigembus] failed: ${error}`)
    return { ok: false, error }
  }
  return { ok: true }
}
