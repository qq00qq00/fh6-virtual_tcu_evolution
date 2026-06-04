<script setup lang="ts">
  import type { UdpHubTargetsFieldProps } from './udp-hub-targets-field'
  import { NDynamicTags, NFlex, NSwitch, NText } from 'naive-ui'
  import { computed } from 'vue'
  import {
    udpHubTagErrorKey,
    useUdpHubOnCreate,
    useUdpHubTargetsFieldInputProps,
  } from './udp-hub-targets-field'

  const props = defineProps<
    UdpHubTargetsFieldProps & {
      enabledLabel: string
      targetsLabel: string
      placeholder: string
      hint: string
    }
  >()

  const emit = defineEmits<{
    'update:enabled': [value: boolean]
    'update:tags': [value: unknown]
  }>()

  const inputProps = useUdpHubTargetsFieldInputProps(
    () => props.placeholder,
    (value) => props.allowsInput(value),
  )

  const tagErrorKey = computed(() => udpHubTagErrorKey(props.tagError))
  const onCreate = useUdpHubOnCreate(() => props.onCreateTag)
</script>

<template>
  <NFlex vertical :size="10">
    <NFlex justify="space-between" align="center" :size="8">
      <NText>{{ enabledLabel }}</NText>
      <NSwitch :value="props.enabled" @update:value="emit('update:enabled', $event)" />
    </NFlex>
    <template v-if="props.enabled">
      <NText depth="3" style="font-size: 12px">
        {{ targetsLabel }}
      </NText>
      <NDynamicTags
        :value="props.tags"
        size="small"
        :input-props="inputProps"
        :on-create="onCreate"
        @update:value="emit('update:tags', $event)"
      />
      <NText v-if="props.tagError" depth="3" style="font-size: 12px; color: #dc2626">
        {{ $t(tagErrorKey) }}
      </NText>
      <NText depth="3" style="font-size: 11px">
        {{ hint }}
      </NText>
    </template>
  </NFlex>
</template>
