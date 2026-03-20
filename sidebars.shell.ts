import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  shellSidebar: [
    'index',
    {
      type: 'category',
      label: '使用基础',
      items: ['syntax-and-environment', 'file-and-process', 'network-and-scripting', 'low-level-and-debug'],
    },
    {
      type: 'category',
      label: '平台运行时与服务',
      items: ['runtimes-and-media', 'system-properties', 'services-and-testing'],
    },
  ],
};

export default sidebars;
