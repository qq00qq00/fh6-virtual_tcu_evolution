import { i18n } from '@virtual-tcu/shared/i18n'
import { createApp } from 'vue'
import HudApp from './HudApp.vue'

createApp(HudApp).use(i18n).mount('#app')
