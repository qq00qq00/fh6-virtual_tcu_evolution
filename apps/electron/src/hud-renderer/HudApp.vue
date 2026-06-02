<script setup lang="ts">
  import { computed } from 'vue'
  import { HUD_TEMPLATE_COMPONENTS } from './hud-templates'
  import { useHudApp } from './HudApp'
  import './hud-shell.css'

  const {
    connected,
    hudTemplate,
    shellClass,
    clickThrough,
    hudProps,
    close,
    toggleClickThrough,
    syncClickThroughMouse,
    onMouseLeave,
  } = useHudApp()

  const activeTemplate = computed(
    () => HUD_TEMPLATE_COMPONENTS[hudTemplate.value] ?? HUD_TEMPLATE_COMPONENTS.classic,
  )
</script>

<template>
  <div
    class="hud-root"
    :class="[shellClass, hudTemplate, { disconnected: !connected, 'click-through': clickThrough }]"
    @mousemove="syncClickThroughMouse"
    @mouseleave="onMouseLeave"
  >
    <component
      :is="activeTemplate"
      v-bind="hudProps"
      @toggle-click-through="toggleClickThrough"
      @close="close"
    />
  </div>
</template>

<style scoped>
  .hud-root {
    border-radius: 14px;
    border: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  }

  .hud-root.tpl-classic-shell {
    background: rgba(248, 250, 252, 0.97);
    color: #0f172a;
  }

  .hud-root.tpl-minimal-shell {
    background: rgba(15, 23, 42, 0.88);
    border-color: rgba(51, 65, 85, 0.6);
    color: #f8fafc;
    padding: 6px 8px;
  }

  .hud-root.tpl-racing-shell {
    background: linear-gradient(165deg, rgba(15, 23, 42, 0.94) 0%, rgba(30, 27, 46, 0.92) 100%);
    border-color: rgba(220, 38, 38, 0.35);
    color: #f8fafc;
    box-shadow:
      0 0 0 1px rgba(220, 38, 38, 0.15),
      0 12px 40px rgba(0, 0, 0, 0.45);
  }

  .hud-root.tpl-glass-shell {
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(18px) saturate(1.2);
    border-color: rgba(255, 255, 255, 0.12);
    color: #f8fafc;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  }

  .hud-root.click-through.tpl-classic-shell .gear,
  .hud-root.click-through.tpl-minimal-shell .gear,
  .hud-root.click-through.tpl-racing-shell .gear {
    -webkit-text-stroke: 2.5px rgba(0, 0, 0, 0.92);
    paint-order: stroke fill;
  }
</style>
