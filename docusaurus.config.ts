import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
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
        async sidebarItemsGenerator({ defaultSidebarItemsGenerator, ...args }) {
          const sidebarItems = await defaultSidebarItemsGenerator(args);
          // 递归替换特定的分类名称或文档名称，避免被爬虫覆盖
          function processItems(items: any[]) {
            items.forEach(item => {
              // 匹配按文件夹生成的 category
              if (item.type === 'category') {
                if (item.label === 'other') item.label = '其他';
                if (item.label === 'devicedebug') item.label = '真机调试';
                if (item.label === 'emulator') item.label = '设备管理';
              }
              // 匹配按文件生成的 doc
              if (item.type === 'doc') {
                if (item.id === 'guide/start/use-ide') item.label = '安装环境';
                if (item.id === 'guide/version/index') item.label = '版本说明';
                if (item.id === 'guide/framework/other/language-list') item.label = '支持的语言列表';
                if (item.id === 'tools/start/index') item.label = '快速入门';
              }
              // 如果有子项，递归
              if (item.items) {
                processItems(item.items);
              }
            });
          }
          processItems(sidebarItems);
          return sidebarItems;
        },
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

  themes: [
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['en', 'zh'],
        docsRouteBasePath: ['quickapp', 'lua', 'shell'],
        docsDir: ['docs-quickapp', 'docs-lua', 'docs-shell'],
        docsPluginIdForPreferredVersion: 'quickapp',
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
          label: 'JS 快应用',
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
