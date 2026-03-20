# VelaOS 应用开发文档（Docusaurus + Tauri）

QuickApp文档爬取使用：
    https://github.com/CheongSzesuen/VelaDocs

## 环境要求

- Node.js `>= 20`
- （可选，桌面版）Rust 工具链 + Tauri 依赖
- （可选，QuickApp 补抓脚本）Python 3

## 本地预览

```bash
npm ci
npm run start
```

默认开发地址通常为 `http://localhost:3000`。

## 构建静态站点

```bash
npm run build
```

构建产物输出到 `build/`。

## 打包桌面版

```bash
npx tauri dev
```

```bash
npx tauri build
```

Windows 绿色版：

```bash
npm run tauri:portable
```

可执行文件位置：`src-tauri/target/release/app.exe`

## 文档分区

- `/quickapp/`：VelaOS QuickApp 开发文档
- `/lua/`：Lua 应用接口、LVGL 与标准库文档
- `/shell/`：NuttX Shell 参考

## 目录结构

- `docs-quickapp/`：QuickApp 文档内容
- `docs-lua/`：Lua 应用文档内容
- `docs-shell/`：NuttX Shell 文档内容
- `scripts/import_quickapp_docs.py`：QuickApp 文档导入与清洗脚本
- `scripts/docs.py`：403/异常页面的定向补抓脚本
- `scripts/requirements-docs.txt`：补抓脚本依赖
- `sidebars.quickapp.ts` / `sidebars.lua.ts` / `sidebars.shell.ts`：各分区侧边栏
- `docusaurus.config.ts`：站点配置
- `src-tauri/`：Tauri 应用配置与 Rust 端

`docs/` 旧目录和 `sidebars.ts` 已废弃，不再参与当前站点构建。

## 更新 QuickApp 文档

默认直接在当前 `docs-quickapp/` 上执行补抓和清洗：

```bash
python scripts/import_quickapp_docs.py
```

如果需要从上游中文文档重新全量导入，再显式提供源目录：

```bash
python scripts/import_quickapp_docs.py --source-root <path-to-upstream-docs-zh>
```

脚本会：

- 可选地从指定 `docs/zh` 目录重建 `docs-quickapp/`
- 调用本项目内的 `scripts/docs.py` 定向补抓 `guide/start.html`
- 统一清洗 Markdown 链接、图片路径、反斜杠路径和异常锚点
- 删除 `guide/start/index.md` 这类重复 403 页面

首次使用补抓脚本前可安装依赖：

```bash
python -m pip install -r scripts/requirements-docs.txt
```

## 维护说明

- 新增或修改文档时，请直接编辑对应分区目录，并同步调整对应 sidebar
- QuickApp 当前只接入中文文档
- 建议优先阅读：`docs-lua/intro/conventions.md`
