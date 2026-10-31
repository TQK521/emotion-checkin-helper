# HANDOFF · 对话交接（速查版）

> 本文件为**交接速查**；完整历史与细节一律以 `docs/jiaojie/00-对话交接总账.md` 为准（唯一对话记录文件）。
> 规则：每轮对话结束更新本文件 + 总账，随 git 提交推送；只追加不覆盖。

## 最新状态（2026-10-31 · 复盘体系完善 + 文件存放纪律落地）

| 项 | 内容 |
|---|---|
| 本轮任务 | 复盘体系完善（A 索引 + B 模板机制 + 10 篇补提炼）+ 文件存放纪律（核心约束十四）+ 根目录归位清理 |
| A 复盘索引 | `10-shigu-fupan/00-复盘索引.md` 新建：28 篇一页全表（日期/主题/根因/预防/流水账对应段）+ 维护规则 |
| B 模板机制 | AGENTS.md 核心约束一第 2 条追加第 6 项必填「已提炼去向」；未填视为复盘未完成 |
| 补提炼 10 篇 | 流水账 10-22 段 +5、新建 10-21 段 +5；索引回填 28/28「未提炼」清零；关键词速查索引 +4 行 |
| 文件存放纪律 | AGENTS.md 新增核心约束十四（4 条）；00a 卡五 #3 合并「现场清理+文件归位」，恒定量回 ≤8 |
| 根目录归位 | 4 张验收截图 → test/accept/；`_tmp_asset_bak_20261031/` 已删；数据备份 → `archive/历史数据快照/`；`项目全景/`（用户资产）保留 |
| archive 清理 | 用户已删 archive 全部旧文件（docx 副本/3 旧快照/渲染残留），目录壳保留，00b 已同步 |
| 待办 | `docs/参考调研/`、`docs/chengzhang/` 已确认不恢复；**git 不提交不推送**（用户拍板，工作区原样保留） |

## 上一轮（2026-10-31 · 文档资产优化 P0/P1/P2 完成）

- P0 字符污染修复（流水账/00a/语言转译，含 AGENTS.md 对齐）；P1 引用对齐（accept_lib RUNLOG、00b 重写、指令模板库、总账/HANDOFF 同步）；P2 整理（12 号去重+docx 归档、渲染残留归档、15-归档子目录化）
- 验收：三文件重扫 0 命中、runlog() 成功、00b 无失效引用、git 红线复核通过

## 上上轮（2026-10-31 · v1.6.10 四项解耦改动，已验收）

| 项 | 内容 |
|---|---|
| 本轮任务 | 按用户拍板方案 A（主对话串行）：4 项高内聚低耦合改动（①theme `__all__` 白名单 ②拆 pages_manual.py ③删 pages_home 死导入 ④data_store 依赖 CHAPTER_COUNT）+ 集成验收；底线=任何可见功能零变化 |
| 改动 | theme.py 追加 `__all__`（34 项）；**新模块 `src/pages_manual.py`**（ManualMixin，自 main.py 迁 19 方法+EMOTION_LESSON_MAP）；main.py 641→163 行，`App(tk.Tk, ManualMixin, HomeMixin, RecordMixin, ToolMixin)`；pages_home.py:21 只留 EMOTION_GLOSSARY；chapters_data 加 `CHAPTER_COUNT`，data_store 改依赖它 |
| ⚠ MRO 硬约束 | **ManualMixin 必须紧邻 HomeMixin 之前**——`_add_custom_emotion` 经 `super()` 调 HomeMixin 实现（写入+save_data+首页标签重建），成功后 ManualMixin 再重建词库区；颠倒则词库区不刷新（已实测验证） |
| 验收 | 静态 S1-S8 全过；v1.6.9 重跑 17/17；手册专项+四页冒烟 25/25；截图 4 张已核对；真实数据哈希全程不变 `EDD323D3EC0B91ED` |
| 执行方式 | 方案 A 串行自干（未委派）；注明"单点小改自干+无并行空间判定" |
| 待办 | git commit 未做（5 src 改 + pages_manual.py + 3 验收脚本 + 4 截图未暂存）；提交前 `git diff --cached --stat` |

## 常规信息（不变）

- 启动：`py -3.13 src/main.py` 或 `scripts/qidongdaka.bat`（**禁用裸 python**，沙箱 runtime 无 tkinter）
- 当前版本 v1.6.9 体验迭代期，**禁止打包**（定版后才打包）
- 用户偏好：交接必更新本文件+总账并 git 推送；经验沉淀进 14 流水账；算力评估先行；轻量任务只给浅档交付
- git：远端 `https://github.com/TQK521/emotion-checkin-helper.git`（main）；必要时代理 `http://127.0.0.1:7897`
