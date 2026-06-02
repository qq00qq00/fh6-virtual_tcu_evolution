<script setup lang="ts">
  defineProps<{
    mode: string
    modeColor: string
    tcuState: string
    clickThrough: boolean
  }>()

  const emit = defineEmits<{
    toggleClickThrough: [e: MouseEvent]
    close: []
  }>()
</script>

<template>
  <div class="hud-chrome-row">
    <div class="mode-pill" :style="{ color: modeColor, borderColor: modeColor }">
      {{ mode }}
    </div>
    <div class="state-pill" :class="{ shifting: tcuState === 'SHIFTING' }">
      {{ tcuState }}
    </div>
    <div class="actions interactive">
      <button
        type="button"
        class="btn"
        :class="{ active: clickThrough }"
        title="Toggle click-through"
        @click="emit('toggleClickThrough', $event)"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" stroke-linecap="round" />
        </svg>
      </button>
      <button type="button" class="btn" title="Close HUD" @click="emit('close')">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
  .hud-chrome-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
  }

  .mode-pill {
    border: 1px solid currentColor;
    border-radius: 999px;
    padding: 2px 8px;
    font-weight: 700;
    font-size: 10px;
    background: rgba(255, 255, 255, 0.08);
  }

  .state-pill {
    background: rgba(148, 163, 184, 0.15);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
    color: #94a3b8;
  }

  .state-pill.shifting {
    background: rgba(167, 139, 250, 0.2);
    color: #c4b5fd;
  }

  .actions {
    margin-left: auto;
    display: flex;
    gap: 4px;
  }

  .btn {
    -webkit-app-region: no-drag;
    background: rgba(15, 23, 42, 0.06);
    border: 1px solid rgba(15, 23, 42, 0.12);
    color: #334155;
    border-radius: 8px;
    width: 26px;
    height: 26px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition:
      background 150ms,
      border-color 150ms,
      color 150ms;
  }

  .btn:hover {
    background: rgba(15, 23, 42, 0.1);
  }

  .btn.active {
    background: #0f172a;
    border-color: #0f172a;
    color: #f8fafc;
  }
</style>
