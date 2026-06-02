import type { GlobalThemeOverrides } from 'naive-ui'

export const tcuThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#22c55e',
    primaryColorHover: '#16a34a',
    primaryColorPressed: '#15803d',
    primaryColorSuppl: '#16a34a',
    borderRadius: '10px',
    fontWeightStrong: '600',
    fontFamily: "'Fira Sans', ui-sans-serif, system-ui, sans-serif",
    fontFamilyMono: "'Fira Code', ui-monospace, monospace",
  },
}

export const tcuDarkThemeOverrides: GlobalThemeOverrides = {
  ...tcuThemeOverrides,
  common: {
    ...tcuThemeOverrides.common,
    bodyColor: '#030712',
    cardColor: '#0b0f19',
    modalColor: '#111827',
    borderColor: '#334155',
    textColor1: '#f8fafc',
    textColor2: '#94a3b8',
    textColor3: '#64748b',
  },
}
