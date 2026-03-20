import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';

const entries = [
  {
    title: 'QuickApp 开发',
    href: '/quickapp/',
    eyebrow: 'VelaOS QuickApp',
    summary: '中文全量接入的 QuickApp 文档，覆盖快速入门、框架、组件、系统接口、工具链与示例。',
    bullets: ['快速入门', '框架语法与模板', '组件与系统接口'],
  },
  {
    title: 'Lua 应用开发',
    href: '/lua/',
    eyebrow: 'Lua Runtime',
    summary: '汇总 Lua 应用开发接口、LVGL 能力、系统模块与标准库说明，适合日常开发和设备验证交叉查阅。',
    bullets: ['LVGL 控件与枚举', '系统模块速查', '标准库可用性'],
  },
  {
    title: 'NuttX Shell',
    href: '/shell/',
    eyebrow: 'Device Shell',
    summary: '围绕 nsh 的语法差异、常用命令、平台运行时和设备调试服务重新整理，便于联调排障。',
    bullets: ['语法与环境', '命令分类速查', '设备服务与调试'],
  },
];

const highlights = [
  '一个站点统一收纳 QuickApp、Lua 应用和 NuttX Shell 开发资料。',
  'QuickApp 文档保留中文全量内容，并补齐异常页面与链接清洗。',
  'Shell 分区改为结构化导航，更适合设备调试时按主题查找命令。',
];

export default function Home() {
  return (
    <Layout
      title="VelaOS 应用开发文档"
      description="VelaOS QuickApp、Lua 应用与 NuttX Shell 一站式开发参考">
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroPanel}>
            <p className={styles.eyebrow}>VelaOS Developer Docs</p>
            <h1 className={styles.title}>VelaOS 应用开发文档</h1>
            <p className={styles.subtitle}>
              面向 VelaOS 应用开发的统一入口，集中整理 QuickApp、Lua 应用与 NuttX Shell 的开发资料、
              接口细节和设备侧验证信息。
            </p>
            <div className={styles.actions}>
              <Link className={styles.primaryAction} to="/quickapp/">
                进入 QuickApp 文档
              </Link>
              <Link className={styles.secondaryAction} to="/shell/">
                查看 Shell 分区
              </Link>
            </div>
          </div>
          <div className={styles.highlightPanel}>
            <p className={styles.highlightLabel}>当前站点结构</p>
            <ul className={styles.highlightList}>
              {highlights.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className={styles.gridSection}>
          {entries.map((entry) => (
            <Link key={entry.href} className={styles.card} to={entry.href}>
              <p className={styles.cardEyebrow}>{entry.eyebrow}</p>
              <h2 className={styles.cardTitle}>{entry.title}</h2>
              <p className={styles.cardSummary}>{entry.summary}</p>
              <ul className={styles.cardList}>
                {entry.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              <span className={styles.cardLink}>打开分区</span>
            </Link>
          ))}
        </section>
      </main>
    </Layout>
  );
}
