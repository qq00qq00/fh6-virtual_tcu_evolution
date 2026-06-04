import type { UdpHubTargetError } from '@virtual-tcu/shared/utils/udpHubTargets'
import type { OnCreate } from 'naive-ui/es/dynamic-tags/src/interface'
import type { ComputedRef } from 'vue'
import { computed } from 'vue'

export interface UdpHubTargetsFieldProps {
  enabled: boolean
  tags: string[]
  tagError: UdpHubTargetError | string
  allowsInput: (value: string) => boolean
  onCreateTag: (label: string) => string | false
}

/** Naive types omit `false`, but NDynamicTags still pushes it; we sanitize on update. */
export function wrapUdpHubOnCreateTag(onCreateTag: (label: string) => string | false): OnCreate {
  return ((label: string) => onCreateTag(label)) as OnCreate
}

export function useUdpHubOnCreate(
  onCreateTag: () => (label: string) => string | false,
): ComputedRef<OnCreate> {
  return computed(() => wrapUdpHubOnCreateTag(onCreateTag()))
}

export function udpHubTagErrorKey(error: string): string {
  if (!error) return ''
  return `extras.networkErrors.${error}`
}

export function useUdpHubTargetsFieldInputProps(
  placeholder: () => string,
  allowsInput: (value: string) => boolean,
): ComputedRef<{ placeholder: string; allowInput: (value: string) => boolean; style: string }> {
  return computed(() => ({
    placeholder: placeholder(),
    allowInput: allowsInput,
    style: 'font-family: ui-monospace, monospace',
  }))
}
