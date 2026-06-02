<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import { toRefs } from 'vue'

  const props = withDefaults(
    defineProps<{
      advice?: ShiftAdvice
      hint?: string
      showHint?: boolean
      size?: 'sm' | 'md' | 'lg'
    }>(),
    {
      advice: '',
      hint: '',
      showHint: false,
      size: 'md',
    },
  )

  const { advice, hint, showHint, size } = toRefs(props)
</script>

<template>
  <div class="shift-advisor" :class="[`size-${size}`, { active: advice }]">
    <div
      v-if="advice === 'down'"
      class="arrow arrow-down"
      role="img"
      :aria-label="$t('electronApp.shiftDown')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M12 5v14M6 13l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <div class="shift-advisor-slot">
      <slot />
    </div>

    <div
      v-if="advice === 'up'"
      class="arrow arrow-up"
      role="img"
      :aria-label="$t('electronApp.shiftUp')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M12 19V5M6 11l6-6 6 6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <p v-if="showHint && hint" class="shift-hint">{{ hint }}</p>
  </div>
</template>

<style scoped>
  .shift-advisor {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
  }

  .shift-advisor.size-sm {
    gap: 0.35rem;
  }

  .shift-advisor.size-lg {
    gap: 0.75rem;
  }

  .shift-advisor-slot {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
  }

  .arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--color-accent, #22c55e);
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-accent, #22c55e) 55%, transparent));
    animation: shift-pulse 1.1s ease-in-out infinite;
  }

  .arrow-down {
    color: var(--color-warn, #eab308);
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-warn, #eab308) 55%, transparent));
  }

  .arrow svg {
    width: 2rem;
    height: 2rem;
  }

  .size-sm .arrow svg {
    width: 1.35rem;
    height: 1.35rem;
  }

  .size-lg .arrow svg {
    width: 2.75rem;
    height: 2.75rem;
  }

  .shift-hint {
    grid-column: 1 / -1;
    margin: 0;
    text-align: center;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--color-accent-2, #3b82f6);
  }

  @keyframes shift-pulse-up {
    0%,
    100% {
      opacity: 1;
      transform: translateY(0);
    }
    50% {
      opacity: 0.72;
      transform: translateY(-3px);
    }
  }

  @keyframes shift-pulse-down {
    0%,
    100% {
      opacity: 1;
      transform: translateY(0);
    }
    50% {
      opacity: 0.72;
      transform: translateY(3px);
    }
  }

  .arrow-up {
    animation-name: shift-pulse-up;
  }

  .arrow-down {
    animation-name: shift-pulse-down;
  }

  @media (prefers-reduced-motion: reduce) {
    .arrow {
      animation: none;
    }
  }
</style>
