<script setup>
const props = defineProps({
  on: { type: Boolean, required: true },
})
const emit = defineEmits(['toggle'])
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="props.on"
    class="relative h-5 w-9 shrink-0 rounded-full transition-colors"
    :class="props.on ? 'bg-accent' : 'bg-tcu-bg-3'"
    @click="emit('toggle')"
  >
    <span
      class="absolute top-0.5 left-0.5 size-4 rounded-full transition-all"
      :class="props.on ? 'translate-x-4 bg-white' : 'bg-tcu-txt-muted'"
    />
  </button>
</template>
