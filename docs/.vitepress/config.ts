import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'db-sync-tool',
  description: 'Database synchronization tool for MySQL/MariaDB with automatic credential extraction',

  base: '/db-sync-tool/',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/db-sync-tool/logo.svg' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'db-sync-tool' }],
    ['meta', { property: 'og:description', content: 'Database synchronization tool for MySQL/MariaDB' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Guide', link: '/getting-started/' },
      { text: 'Configuration', link: '/configuration/' },
      { text: 'Reference', link: '/reference/sync-modes' },
      {
        text: 'Links',
        items: [
          { text: 'PyPI', link: 'https://pypi.org/project/db-sync-tool-kmi/' },
          { text: 'Packagist', link: 'https://packagist.org/packages/kmi/db-sync-tool' },
          { text: 'Changelog', link: 'https://github.com/konradmichalik/db-sync-tool/blob/main/CHANGELOG.md' }
        ]
      }
    ],

    sidebar: {
      '/getting-started/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/getting-started/' },
            { text: 'Installation', link: '/getting-started/installation' },
            { text: 'Quick Start', link: '/getting-started/quickstart' }
          ]
        },
        {
          text: 'Framework Guides',
          items: [
            { text: 'TYPO3', link: '/getting-started/typo3' },
            { text: 'Symfony', link: '/getting-started/symfony' },
            { text: 'WordPress', link: '/getting-started/wordpress' },
            { text: 'Drupal', link: '/getting-started/drupal' },
            { text: 'Laravel', link: '/getting-started/laravel' }
          ]
        }
      ],
      '/configuration/': [
        {
          text: 'Configuration',
          items: [
            { text: 'Overview', link: '/configuration/' },
            { text: 'Auto-Discovery', link: '/configuration/auto-discovery' },
            { text: 'Config File Reference', link: '/configuration/reference' },
            { text: 'Authentication', link: '/configuration/authentication' },
            { text: 'Advanced Options', link: '/configuration/advanced' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'Sync Modes', link: '/reference/sync-modes' },
            { text: 'CLI Reference', link: '/reference/cli' }
          ]
        }
      ],
      '/development/': [
        {
          text: 'Development',
          items: [
            { text: 'Testing', link: '/development/testing' },
            { text: 'Release Guide', link: '/development/release' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/konradmichalik/db-sync-tool' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright 2020-present'
    },

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/konradmichalik/db-sync-tool/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    }
  }
})
