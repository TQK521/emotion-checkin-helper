# 贡献指南（Contributing）

本项目为**个人项目 + AI 协作开发模式**（2026-10-27 起，原九角色分组协作已废弃；2026-11-01 技术栈切换 webapp 主线）。

## 如何提需求 / 反馈问题

1. 用大白话描述需求或问题（现象 → 期望 → 影响），≥30 字时先在 `docs/jingyan-zichan/语言转译档案_大白话到专业表述.md` 登记转译
2. 直接在主对话提出；深度改动前 AI 会先给预估时间与建议，确认后再动手
3. 问题提交建议附：复现步骤、截图、数据文件位置（注意数据隐私，`checkin_data.json` 不要外发）

## 开发纪律（简版，完整见 AGENTS.md）

- 开工前 T0 门：查坑（流水账）→ 查轮子（资产库 + accept_lib + 豆包内置 + GitHub）→ 查状态（交接总账）
- 只做单点改动；布局/尺寸/性能类改动先最小实验验证（先实测后下结论）
- 质量门四件套：`pnpm typecheck` / `pnpm lint` / `pnpm test` / `pnpm build` 全绿
- 验收：从 `test/accept/_exp_TEMPLATE_accept.py` 复制，import `accept_lib`（两段式+段门+`--fast`）
- 数据红线：根 `checkin_data.json` 绝不入库、不删除、不覆盖；正式数据走 Tauri Rust 命令原子写
- 收尾：经验入流水账、复盘归档、交接总账登记

## 代码规范（webapp 主线）

- 模块分工：`webapp/src` 六层（app 装配 / core 领域 / features 四域 / services 存储 / shared 公共 / src-tauri Rust 壳），非指定需求禁止跨模块改动；**boundaries 分层红线：shared 只许依赖 shared**
- 注释：新增/修改代码必须有中文注释（用途/参数/返回值/为什么）；禁止 `any` 逃逸（vue-tsc 严格）
- 命名：组件 `PascalCase.vue`、模块 `kebab-case.ts`、变量 `camelCase`、常量 `SCREAMING_SNAKE_CASE`；文档目录拼音短名、文件"编号-中文短名"（见 `docs/guifan/4-项目结构规范.md` 第五节）

## 打包与发布

- 体验/迭代期禁止打包；仅用户明确"定版/交付"后 `cd webapp && pnpm tauri build`
- 绿色版交付目录 `D:\EmotionCheckin\`（**纯英文非桌面目录**，WebView2 路径双敏感）
- 发布走 GitHub Releases（绿色版 exe）；git 本地每次 commit、每累计 5 次 push（核心约束十五）
