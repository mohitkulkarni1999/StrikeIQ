const { createNextPlugin } = require('@next/eslint-plugin-next');

module.exports = {
  extends: ['next/core-web-vitals'],
  plugins: ['@next/eslint-plugin-next'],
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: ['../core/ws/*'],
            message: 'WS lifecycle is locked. Do not import from UI layer.'
          }
        ]
      }
    ]
  }
};
