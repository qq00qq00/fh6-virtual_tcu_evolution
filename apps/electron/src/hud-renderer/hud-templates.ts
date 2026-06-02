import type { HudTemplateId } from '@virtual-tcu/shared/config/hud'
import type { Component } from 'vue'
import HudTemplateClassic from './templates/HudTemplateClassic.vue'
import HudTemplateGlass from './templates/HudTemplateGlass.vue'
import HudTemplateMinimal from './templates/HudTemplateMinimal.vue'
import HudTemplateRacing from './templates/HudTemplateRacing.vue'

export const HUD_TEMPLATE_COMPONENTS: Record<HudTemplateId, Component> = {
  classic: HudTemplateClassic,
  minimal: HudTemplateMinimal,
  racing: HudTemplateRacing,
  glass: HudTemplateGlass,
}
