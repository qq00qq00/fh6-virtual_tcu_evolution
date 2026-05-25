import antfu from '@antfu/eslint-config'
import prettier from 'eslint-config-prettier'

export default antfu({
  vue: true,

  stylistic: false,
  formatters: false,

  rules: {
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    '@typescript-eslint/no-explicit-any': 0,
  },

  ignores: [
    '**/dist/',
    '**/out/',
    '**/release/',
    '**/node_modules/',
    'virtual_tcu/',
    '.claude/',
    '.husky/',
    '.vscode/',
    'docs/',
    '**/*.d.ts',
    '**/components.d.ts',
  ],
}, {
  files: ['electron/src/main/**/*.ts'],
  rules: {
    'node/prefer-global/process': 'off',
    'node/prefer-global/buffer': 'off',
    'no-console': 'off',
  },
}).append(prettier)
