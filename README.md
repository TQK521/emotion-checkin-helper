# 学习情绪打卡助手（桌面版）

> 一款 100% 本地离线的情绪记录与心理自助桌面应用：按次情绪打卡、三问结构化日记、70 课循证心理自助手册、可生长的情绪词库。
> 无账号、无云端、无埋点——隐私只留在本机。

- 技术栈：Python 3.13 + Tkinter（标准库，**无第三方运行时依赖**）
- 当前版本：v1.6.9（正式版，GitHub Releases 发布）
- GitHub 仓库：`TQK521/emotion-checkin-helper`（公开，https://github.com/TQK521/emotion-checkin-helper）

---

## 快速启动

| 方式 | 操作 |
|---|---|
| 正式版（推荐） | 双击桌面「学习情绪打卡(正式版)」快捷方式，或运行 `release/xuexiqingxudaka_v1.6.9/xuexiqingxudaka.exe` |
| 源码运行 | `py -3.13 src/main.py`（**注意**：裸 `python` 是沙箱 runtime，tkinter 会启动失败，一律用 `py -3.13`） |
| 启动器 | 双击 `scripts/qidongdaka.bat` |

**用户数据**：`checkin_data.json`（项目根目录，**隐私红线，绝不入库**）。备份 = 直接复制该文件；exe 运行版数据在 exe 同目录（两套数据位置，替换交付物时记得把数据一并带过去）。

## 目录结构（标准工程布局）

| 目录 | 内容 |
|---|---|
| `src/` | 源码：`main.py`（入口）+ `data_store.py`（数据层）+ `pages_home/pages_record/pages_tool.py`（页面）+ `theme.py`（视觉常量）+ `chapters_data.py`（手册数据）+ `toolkit_data.py`（方法库数据）+ `ui_dialogs.py`（柔和弹窗） |
| `docs/` | 文档体系：`guifan/`（规范与执行卡）、`jiaojie/`（交接总账）、`jingyan-zichan/`（经验资产：流水账/代码资产库/指令模板库/复盘/验收库/Word库/历史归档）、`moban/`（交付模板） |
| `scripts/` | `qidongdaka.bat`（启动器）、`xuexiqingxudaka_onedir.spec`（PyInstaller 构建配置） |
| `test/accept/` | 验收与实验脚本（`_exp_*.py`，验收模板复用 `_exp_TEMPLATE_accept.py`） |
| `assets/` | `xuexiqingxudaka.ico`（图标，根目录另保留一份供源码图标定位） |
| `release/` | 发布成品：正式版 exe 目录（v1.6.9）+ 说明.txt（历史版本已于 2026-10-31 清理） |
| `archive/` | 冗余/过时归档：历史数据快照、渲染测试残留、旧版文档副本（保留原貌备查） |
| 根目录 | `AGENTS.md`（项目宪法）、`CHANGELOG.md`、`CONTRIBUTING.md`、`LICENSE`、`SECURITY.md`、`requirements.txt`、`.gitignore` |

## 命名规范

- 文件夹（重要语义）用汉语拼音：`src`、`docs`、`scripts`、`test`、`assets`、`release`、`archive`
- 序号/版本号用英文字符：`v1.6.9`
- 交付物：`软件名_v版本号.zip`（示例 `xuexiqingxudaka_v1.6.9.zip`）

## 开发流程入口

1. **开工前 T0 门**：查坑（`docs/jingyan-zichan/14-jingyan-liushui.md`）→ 查轮子（`docs/jingyan-zichan/代码资产库.md` + accept_lib）→ 查状态（`docs/jiaojie/00-对话交接总账.md`）
2. **执行面**：`docs/guifan/00a-执行检查卡.md`（五卡）；流程见 `docs/guifan/1-开发流程.md`
3. **文档导航**：`docs/guifan/00b-文档导航.md`（全项目文档地图 + 上手顺序）
4. **验收**：一律从 `test/accept/_exp_TEMPLATE_accept.py` 复制 + `docs/jingyan-zichan/11-yanshou-kufu/accept_lib.py` import 复用
5. **打包**：定版后执行（见 `docs/guifan/7-打包交付规范.md`），spec 在 `scripts/`
6. **版本记录**：`CHANGELOG.md`（简要）+ 交接总账（详细）

## 构建

```powershell
# 开发依赖（仅打包需要；运行无需安装任何第三方包）
pip install -r requirements.txt

# 打包（onedir 模式，onefile 会被安全软件拦截）
cd scripts
& "C:\Users\29236\AppData\Local\Programs\Python\Python313\python.exe" -m PyInstaller --clean --distpath dist --workpath build xuexiqingxudaka_onedir.spec
```

*详细纪律以 `AGENTS.md` 与各规范文档为准。*
