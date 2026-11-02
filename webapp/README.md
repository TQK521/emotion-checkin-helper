# 学习情绪打卡 · Web 全栈 PC 版（webapp/）

「学习情绪打卡助手」的第二阶段重构工程（v2 方案 B1：HTML/CSS + TS + Vue3 + Tauri 2），
与旧版 Python+Tkinter 工程（项目根 `src/`）并存，**互不干扰、数据独立**。

- 技术栈：Vite 8 + Vue 3.5 + TypeScript + Pinia + vue-router + Vitest + Tauri 2（Rust）
- 包管理器：pnpm（>=12）
- 目录：`src/app`（装配）/ `src/core`（领域/统计/store）/ `src/features`（四功能域）/
  `src/services`（存储端口+适配器+导入器）/ `src/shared`（公共 UI/样式）/ `src-tauri`（Rust 后端）

---

## 一、环境要求

| 组件 | 版本 | 说明 |
|---|---|---|
| Node.js | >=18 | 开发必需 |
| pnpm | >=12 | 包管理（本项目锁 12.16.1） |
| Rust | 1.99.x（stable-msvc） | 由 `src-tauri/rust-toolchain.toml` 锁定 |
| MSVC Build Tools | 17.x（VC.Tools + 一个 Windows SDK） | 仅打包需要 |
| WebView2 | 系统自带 | 最终用户运行期唯一依赖（Win10/11 已内置） |

> 本机 PATH 提示：`git` 在 `D:\Git\cmd`（**已加入用户级 PATH，2026-11-02 持久化**，
> 新开终端/重启后可直接 `git`；旧终端会话仍须完整路径）；node 在 `C:\Program Files\nodejs`、
> pnpm 在 `C:\Users\<用户>\AppData\Roaming\npm`、cargo 在 `C:\Users\<用户>\.cargo\bin`，
> 若命令找不到请把对应目录加入 PATH 前缀。

## 二、安装依赖

```bash
cd webapp
pnpm install
```

## 三、开发启动（浏览器模式，无需 Rust）

```bash
pnpm dev
```

- 访问 `http://localhost:1420`（vite strictPort 固定端口）。
- 数据走浏览器 `localStorage`，key = `checkin-dev-db`（开发态专用，不碰正式数据）。

## 四、质量门（每轮改动必跑）

```bash
pnpm typecheck   # vue-tsc --noEmit，类型检查
pnpm lint        # eslint（含 boundaries 分层依赖检查）
pnpm test        # vitest run，co-located 单元测试（89+ 用例）
pnpm build       # 前端产物构建
```

> PowerShell 下命令输出可能被吞，建议 `pnpm test *> 日志.txt` 落盘后查看。

## 五、桌面模式（Tauri）

### 5.1 数据路径

- 正式数据存于 **appDataDir**：`%APPDATA%\com.tqk.emotioncheckin\checkin_data.json`
  （Windows 即 `C:\Users\<用户>\AppData\Roaming\com.tqk.emotioncheckin\`），
  独立于安装目录，升级/换机不丢数据。
- 首次启动若无数据，前端会弹出**导入向导**，可导入旧版 `checkin_data.json`
  （旧版数据契约直接兼容，importer 自动迁移）。

### 5.2 Rust 命令（`src-tauri/src/lib.rs`）

| 命令 | 作用 | 安全机制 |
|---|---|---|
| `load_data` | 读取完整数据 | 缺失→空数据；损坏→改名 `checkin_data_损坏_<ts>.json` 保留现场 |
| `save_data` | 全量写回 | 原子写（临时文件 + rename 替换），崩溃不损坏原数据 |
| `backup_data` | 备份当日数据 | 仅备份合法数据；`checkin_data_备份_<日期>.json` 同天覆盖；保留最近 7 份 |
| `pick_import_file` | 弹文件框选旧数据文件 | 返回文件原文，由前端 importer 迁移后写回 |

- 启动时自动备份一次（setup 钩子，失败静默）。

### 5.3 打包便携绿色版

```bash
cd webapp
pnpm tauri build
```

产物：

- `src-tauri/target/release/xuexiqingxudaka.exe`（绿色版单文件，前端资源已内嵌）
- 安装包在 `src-tauri/target/release/bundle/`（NSIS/MSI 等）

交付形态：**免安装绿色版**——把 exe（及可选说明文档）放进一个文件夹即可分发，
用户无需安装 Node/Rust/Python，运行期仅依赖系统自带 WebView2。

> **⚠️ 重要：exe 必须放在纯英文路径下运行**。本机实测：exe 放在含中文的目录
> （如 `C:\Users\29236\Desktop\桌面小程序开发\...`）启动即崩溃
> （`0xc0000409`，`Failed to setup app: 拒绝访问 (os error 5)`，发生在窗口/WebView2
> 创建阶段）；复制到纯英文路径（如 `C:\Tools\学习情绪打卡\` 的实际英文名目录、
> `C:\Program Files\...`、`D:\Apps\...`）则完全正常。分发时请将绿色版放进英文路径目录。

## 六、目录结构（速览）

```
webapp/
├─ src/
│  ├─ app/            # 装配：main.ts / App.vue / router / providers / components(ImportWizard)
│  ├─ core/           # domain（数据契约）/ stats（纯函数统计）/ store（Pinia 单一数据源）
│  ├─ features/       # home / record / tool / manual 四功能域（测试 co-located）
│  ├─ services/       # storage.port + tauri/browser/memory 三适配器 + importer
│  ├─ shared/         # ui 组件 / lib 工具 / styles（tokens.css 主题变量）
│  └─ assets/data/    # 静态软件数据（chapters 70 / toolkit 30 / emotions 56 / glossary 56）
└─ src-tauri/         # Rust 后端：lib.rs 命令 + capabilities + tauri.conf.json
```

## 七、数据红线

- 开发/测试**不写真实正式数据**：浏览器开发态走 localStorage `checkin-dev-db`，
  测试注入 InMemory 适配器；正式数据只在 Tauri 桌面态由 Rust 命令读写。
- 项目根 `checkin_data.json`（旧版数据）不得被 webapp 开发/测试污染。
