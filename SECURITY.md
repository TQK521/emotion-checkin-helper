# 安全说明（Security）

## 数据隐私（本项目的核心承诺）

- **数据 100% 本地存储**：打卡/日记数据只保存在本机 `checkin_data.json`（源码运行版）或 exe 同目录（正式版），**无云端上传、无账号、无埋点**
- 请勿将 `checkin_data.json` 或其备份提交到任何公开仓库/聊天工具（`.gitignore` 已设隐私红线，勿移除）
- 备份与迁移：直接复制 `checkin_data.json` 文件即可；替换 exe 交付物时须将数据文件一并带过去（源码版与 exe 版数据位置不同，详见根 `README.md`）

## 软件供应链

- 运行时零第三方依赖（仅 Python 标准库 Tkinter），无自动更新、无联网行为
- 打包产物来自本地 PyInstaller 构建（spec 见 `scripts/`），可审计可复现

## 上报问题

- GitHub Issues：https://github.com/TQK521/emotion-checkin-helper/issues
- 本地反馈：直接在主对话提出（勿附真实数据文件）
