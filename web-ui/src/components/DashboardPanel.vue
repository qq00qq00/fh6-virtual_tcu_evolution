<script setup>
import { toRefs, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  live: { type: Boolean, required: true },
  telemetry: { type: Object, default: () => ({}) },
})
const { live, telemetry } = toRefs(props)

const rpmPct = computed(() => telemetry.value?.rpm_pct || 0)
const gear = computed(() => {
  const g = telemetry.value?.gear
  if (g === 0) return 'R'
  if (g === 11) return 'N'
  return g || '-'
})

const getLedClass = (index, pct) => {
  const threshold = index / 15.0
  if (pct < threshold) return 'bg-[#1a1a1a]'
  if (index > 13) return 'bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.8)]'
  if (index > 10) return 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.8)]'
  if (index > 5) return 'bg-yellow-400 shadow-[0_0_10px_rgba(250,204,21,0.6)]'
  return 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]'
}
</script>

<template>
  <div class="h-full flex flex-col gap-4 p-6 bg-[#09090b] font-mono text-[#e4e4e7] border-l border-[#27272a] select-none">
    
    <div v-if="live && telemetry" class="flex flex-col gap-6 h-full">
      <div class="flex gap-1 h-8 w-full px-4 rounded bg-[#18181b] border border-[#27272a] items-center justify-center">
        <div v-for="i in 15" :key="i" class="flex-1 h-3 rounded-sm transition-colors duration-75" :class="getLedClass(i, rpmPct)"></div>
      </div>

      <div class="flex gap-6">
        <div class="flex flex-col justify-center items-center bg-[#111113] border-2 border-[#27272a] rounded-lg w-48 h-48 shadow-lg">
          <div class="text-[120px] font-black leading-none tracking-tighter" :class="telemetry.tcu_state === 'SHIFTING' ? 'text-blue-500' : 'text-red-500'">
            {{ gear }}
          </div>
          <div class="text-xs text-[#a1a1aa] uppercase tracking-widest mt-2">{{ telemetry.drivetrain || 'GEAR' }}</div>
        </div>
        
        <div class="flex-1 flex flex-col justify-between bg-[#111113] border border-[#27272a] rounded-lg p-6">
          <div class="flex justify-between items-end border-b border-[#27272a] pb-4">
            <div class="text-6xl font-bold tracking-tight text-white">{{ Math.round(telemetry.speed_kmh || 0) }}</div>
            <div class="text-sm text-[#a1a1aa] mb-2 uppercase tracking-widest">KM/H</div>
          </div>
          <div class="flex justify-between items-end pt-4">
            <div class="text-5xl font-bold tracking-tight text-[#facc15]">{{ Math.round(telemetry.rpm || 0) }}</div>
            <div class="text-sm text-[#a1a1aa] mb-1 uppercase tracking-widest">RPM</div>
          </div>
        </div>
      </div>

      <div class="bg-[#18181b] border border-blue-900/30 rounded p-4 flex justify-between items-center">
        <div class="text-2xl font-bold text-blue-400 tracking-wider">{{ telemetry.tcu_state || 'STANDBY' }}</div>
        <div class="text-sm text-[#a1a1aa] uppercase">{{ telemetry.tcu_state_sub || 'AWAITING TELEMETRY' }}</div>
      </div>

      <div class="grid grid-cols-4 gap-4 mt-auto">
        <div class="bg-[#111113] border border-[#27272a] p-4 rounded-lg flex flex-col">
          <span class="text-[10px] text-[#a1a1aa] uppercase tracking-widest mb-1">Throttle</span>
          <span class="text-xl font-bold text-green-500">{{ Math.round((telemetry.throttle || 0) * 100) }}%</span>
          <div class="h-1 bg-[#27272a] mt-2 rounded"><div class="h-full bg-green-500" :style="{ width: `${(telemetry.throttle || 0) * 100}%` }"></div></div>
        </div>
        <div class="bg-[#111113] border border-[#27272a] p-4 rounded-lg flex flex-col">
          <span class="text-[10px] text-[#a1a1aa] uppercase tracking-widest mb-1">Brake</span>
          <span class="text-xl font-bold text-red-500">{{ Math.round((telemetry.brake || 0) * 100) }}%</span>
          <div class="h-1 bg-[#27272a] mt-2 rounded"><div class="h-full bg-red-500" :style="{ width: `${(telemetry.brake || 0) * 100}%` }"></div></div>
        </div>
        <div class="bg-[#111113] border border-[#27272a] p-4 rounded-lg flex flex-col">
          <span class="text-[10px] text-[#a1a1aa] uppercase tracking-widest mb-1">Power</span>
          <span class="text-xl font-bold text-white">{{ (telemetry.power_kw || 0).toFixed(0) }} kW</span>
        </div>
        <div class="bg-[#111113] border border-[#27272a] p-4 rounded-lg flex flex-col">
          <span class="text-[10px] text-[#a1a1aa] uppercase tracking-widest mb-1">Lat G</span>
          <span class="text-xl font-bold text-yellow-500">{{ (telemetry.g_lat || 0).toFixed(2) }} g</span>
        </div>
      </div>
      
    </div>

    <div v-else class="flex flex-col items-center justify-center h-full text-[#a1a1aa]">
      <div class="text-3xl font-bold mb-2 tracking-widest">OFFLINE</div>
      <div class="text-sm">Awaiting Forza Horizon UDP Telemetry...</div>
    </div>
    
  </div>
</template>
