import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'VelaOS 应用开发文档',
  tagline: 'QuickApp、Lua 应用与 NuttX Shell 一站式开发参考',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',

  organizationName: 'your-org',
  projectName: 'velaos-app-docs',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans'],
  },

  presets: [
    [
      'classic',
      {
        docs: false,
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  plugins: [
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'quickapp',
        path: 'docs-quickapp',
        routeBasePath: 'quickapp',
        sidebarPath: './sidebars.quickapp.ts',
        sidebarCollapsed: true,
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'lua',
        path: 'docs-lua',
        routeBasePath: 'lua',
        sidebarPath: './sidebars.lua.ts',
        sidebarCollapsed: true,
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'shell',
        path: 'docs-shell',
        routeBasePath: 'shell',
        sidebarPath: './sidebars.shell.ts',
        sidebarCollapsed: true,
      },
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'VelaOS 应用开发文档',
      logo: {
        alt: 'VelaOS 应用开发文档',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'quickappSidebar',
          docsPluginId: 'quickapp',
          position: 'left',
          label: 'QuickApp',
        },
        {
          type: 'docSidebar',
          sidebarId: 'luaSidebar',
          docsPluginId: 'lua',
          position: 'left',
          label: 'Lua 应用',
        },
        {
          type: 'docSidebar',
          sidebarId: 'shellSidebar',
          docsPluginId: 'shell',
          position: 'left',
          label: 'NuttX Shell',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} 极客之爱. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['lua', 'javascript', 'json', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
