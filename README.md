# 学习情绪打卡助手（桌面版 v2 · webapp 重构）

> 一款 100% 本地离线的情绪记录与心理自助桌面应用：按次情绪打卡、三问结构化日记、70 课循证心理自助手册、可生长的情绪词库。
> 无账号、无云端、无埋点——隐私只留在本机。

- **技术栈（当前主线）**：HTML/CSS + TypeScript + Vue 3 + Tauri 2（Rust 壳），WebView2 渲染
- **当前版本**：v2 重构版（绿色版 exe，正式交付）
- **GitHub 仓库**：`TQK521/emotion-checkin-helper`（公开，https://github.com/TQK521/emotion-checkin-helper）
- **旧版 Python/Tk 技术栈已于 2026-11-01 删除**（用户已保留备份；Tk 规则归档见 `archive/过时规范/Tk开发与验收约束_归档_20261101.md`）

---

## 快速启动

| 方式 | 操作 |
|---|---|
| 绿色版 exe（正式交付） | `D:\EmotionCheckin\xuexiqingxudaka.exe`（**必须保持纯英文路径且不在桌面**，见下方红色警告） |
| 源码开发 | `cd webapp && pnpm dev`（Vite 热更新） |
| 源码构建 | `cd webapp && pnpm build`（产物 `webapp/dist/`） |
| Tauri 打包 | `cd webapp && pnpm tauri build`（产物 `webapp/src-tauri/target/release/`） |

> **🔴 红色警告（2026-11-01 崩溃复盘结论）**：本机 WebView2 对 exe 所在路径**双敏感**——
> 中文/非 ASCII 路径 → 启动即崩（拒绝访问）；**桌面目录（含英文子目录）→ 启动即崩（资源在使用中，安全软件盯防桌面强嫌疑）**。
> 绿色版 exe **必须**放在纯英文且非桌面的目录（如 `D:\EmotionCheckin`、`C:\Temp\xxx`）。数据自动存至
> `%APPDATA%\com.tqk.emotioncheckin\checkin_data.json`（当日自动备份）。详见
> `docs/jingyan-zichan/10-shigu-fupan/2026-11-01-绿色版双路径崩溃复盘.md`。

## 目录结构（标准工程布局，webapp 主线）

| 目录 | 内容 |
|---|---|
| `webapp/` | **v2 重构主线**：`src/app`（装配层）/ `src/features`（四功能域 home·record·tool·manual）/ `src/core`（公共契约）/ `src/services`（存储适配器：tauri/browser/memory/importer）/ `src/shared` / `src-tauri`（Rust 壳：lib.rs 四命令 load_data·save_data·backup_data·pick_import_file） |
| `docs/` | 文档体系：`guifan/`（规范与执行卡）、`jiaojie/`（交接总账）、`jingyan-zichan/`（经验资产：流水账/代码资产库/指令模板库/复盘/验收库/Word库/历史归档）、`moban/`（交付模板） |
| `scripts/` | `export_webapp_data.py`（旧版静态数据→webapp JSON 的历史转换工具） |
| `test/accept/` | 验收与实验脚本（`_exp_*.py`，复用 `docs/jingyan-zichan/11-yanshou-kufu/accept_lib.py`） |
| `archive/` | 过时规范与历史归档（含 Tk 约束归档、历史数据快照） |
| 根目录 | `AGENTS.md`（项目宪法）、`CHANGELOG.md`、`CONTRIBUTING.md`、`LICENSE`、`SECURITY.md`、`.gitignore`、`checkin_data.json`（数据红线，绝不入库） |

**用户数据**：`checkin_data.json`（项目根目录，**隐私红线，绝不入库**）。备份 = 直接复制该文件；
绿色版运行数据在 `%APPDATA%\com.tqk.emotioncheckin\`（自动当日备份）。

## 开发流程入口

1. **开工前 T0 门**：查坑（`docs/jingyan-zichan/14-jingyan-liushui.md`）→ 查轮子（代码资产库 + accept_lib + 豆包内置技能 + 外部 GitHub，见 AGENTS.md 核心约束十六）→ 查状态（`docs/jiaojie/00-对话交接总账.md`）
2. **执行面**：`docs/guifan/00a-执行检查卡.md`（五卡）；流程见 `docs/guifan/1-开发流程.md`
3. **文档导航**：`docs/guifan/00b-文档导航.md`
4. **验收**：复用 `accept_lib.py` + `_exp_*.py` 分层自检；数据隔离三件套；webapp 用 vitest（`pnpm test`）+ typecheck（`pnpm typecheck`）+ lint（`pnpm lint`）
5. **打包**：定版后执行（约束五~十·打包时机），绿色版交付目录 `D:\EmotionCheckin`
6. **版本记录**：`CHANGELOG.md`（简要）+ 交接总账（详细）

## 构建与质量门

```powershell
cd webapp
pnpm install        # 首次
pnpm typecheck      # TS 类型检查
pnpm lint           # ESLint
pnpm test           # Vitest（89 用例）
pnpm build          # 前端产物
pnpm tauri build    # 绿色版 exe（Rust 编译，产物在 src-tauri/target/release/）
```

*详细纪律以 `AGENTS.md` 与各规范文档为准。*
