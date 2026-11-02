# 安全说明（Security）

## 数据隐私（本项目的核心承诺）

- **数据 100% 本地存储**：打卡/日记数据只保存在本机，**无云端上传、无账号、无埋点、无联网行为**
  - 正式态：`%APPDATA%\com.tqk.emotioncheckin\checkin_data.json`（Tauri appDataDir，独立于安装目录）
  - 旧版源码态：项目根 `checkin_data.json`（只读迁移来源）
  - 开发态：浏览器 localStorage（key=`checkin-dev-db`），仅调试用
- 请勿将 `checkin_data.json` 或其备份提交到任何公开仓库/聊天工具（`.gitignore` 已设隐私红线，勿移除）
- 备份与迁移：正式数据有**当日自动备份 + 保留最近 7 份**（`checkin_data_备份_<日期>.json`）；用户可自行复制 `%APPDATA%\com.tqk.emotioncheckin\` 目录做备份；旧版数据可经 `src/services/importer` 安全导入

## 软件供应链

- 运行时零第三方运行时依赖：桌面壳 Tauri 2（WebView2 由 Windows 系统自带），前端资源打包进 exe，无自动更新
- 依赖锁定：前端 `pnpm-lock.yaml`（pnpm >=12）+ Rust `Cargo.lock`；新增依赖须过 `pnpm-workspace.yaml` 的 allowBuilds 审批（核心约束十六：优先借力但不盲信，外部代码先隔离验证）
- 数据安全层（原子写/损坏隔离/备份）为**自研自控**，不引入第三方（核心约束十六第 4 条）

## 绿色版路径红线

- exe 位于**含中文路径**或**桌面目录**时启动即崩（WebView2 双敏感，详见 `docs/jingyan-zichan/10-shigu-fupan/2026-11-01-绿色版双路径崩溃复盘.md`）
- 交付/使用请放纯英文非桌面目录（如 `D:\EmotionCheckin`）

## 上报问题

- GitHub Issues：https://github.com/TQK521/emotion-checkin-helper/issues
- 本地反馈：直接在主对话提出（勿附真实数据文件）
