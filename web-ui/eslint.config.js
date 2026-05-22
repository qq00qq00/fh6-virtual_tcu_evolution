import antfu from '@antfu/eslint-config'
import prettier from 'eslint-config-prettier'

export default antfu({
  vue: true,

  stylistic: false,
  formatters: false,

  rules: {
    /** 使用 console.warn 和 console.error 时警告, 其他情况禁止 */
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    /** 允许使用 any 类型 */
    '@typescript-eslint/no-explicit-any': 0,
  },

  ignores: [
    'README.md',
    '.cursor/**',
    '.husky/',
    '.vscode/',
    'dist/',
    'node_modules/',
    'tsconfig.*.json',
    'components.d.ts',
    'CLAUDE.md',
  ],
}).append(prettier)
