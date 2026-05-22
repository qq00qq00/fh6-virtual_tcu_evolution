<script setup>
import { computed } from 'vue'

const props = defineProps({
  config: { type: Object, required: true },
})

const hotkeyHint = computed(() => {
  const cycle = props.config.hotkey_cycle_mode || 'f9'
  const log = props.config.hotkey_toggle_log || 'f8'
  return `${String(cycle).toUpperCase()} · ${String(log).toUpperCase()}`
})
</script>

<template>
  <footer
    class="border-t border-tcu-border bg-tcu-bg-1 px-6 py-2 text-center font-mono text-[11px] text-tcu-txt-dim"
  >
    {{ $t('footer.hint', { hotkeys: hotkeyHint }) }}
  </footer>
</template>
