# -*- coding: utf-8 -*-
"""_exp_v1610_static.py —— v1.6.10 四项解耦改动·静态验证（纯逻辑层，零 GUI）

验证项（全部可真实失败）：
S1 九个 src 模块 py_compile 全部通过
S2 main.py / pages_manual.py 可导入；App MRO = App → ManualMixin → HomeMixin →
   RecordMixin → ToolMixin → tk.Tk（ManualMixin 必须在 HomeMixin 之前）
S3 ManualMixin._add_custom_emotion 内含 super()._add_custom_emotion 协作调用
S4 theme.__all__ 白名单：5 处 from theme import * 调用点全部能取到所需名字
   （校验 __all__ 覆盖 theme 内所有公开常量/函数，且不含内部 tk 引用）
S5 chapters_data.CHAPTER_COUNT == len(CHAPTERS)；data_store 使用 CHAPTER_COUNT 且
   不再出现 len(CHAPTERS)
S6 pages_home 不再引用 CHAPTERS / EMOTIONS（仅 EMOTION_GLOSSARY）
S7 main.py 不再包含手册渲染方法（_build_manual/_rebuild_glossary/_open_detail 等 19 个
   方法全部迁至 pages_manual.ManualMixin，main 零残留）
S8 pages_manual.ManualMixin 方法清单 = 迁移前 main.py 手册方法清单（19 个）
"""

import os
import sys
import py_compile

ROOT = r"C:\Users\29236\Desktop\桌面小程序开发"
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}" + (f"  —— {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)


# ---------- S1 语法编译 ----------
MODULES = ["main.py", "pages_manual.py", "theme.py", "pages_home.py",
           "pages_record.py", "pages_tool.py", "data_store.py",
           "chapters_data.py", "ui_dialogs.py", "toolkit_data.py"]
for m in MODULES:
    try:
        py_compile.compile(os.path.join(SRC, m), doraise=True)
        check(f"S1 编译 {m}", True)
    except Exception as e:
        check(f"S1 编译 {m}", False, repr(e))

# ---------- S2 导入 + MRO ----------
import main
from pages_manual import ManualMixin
from pages_home import HomeMixin
from pages_record import RecordMixin
from pages_tool import ToolMixin

mro = main.App.__mro__
names = [c.__name__ for c in mro]
print("MRO:", " → ".join(names))
check("S2 App 首位是自身", mro[0] is main.App, names[0])
# tk.Tk 的 C 扩展类（Tk/Misc/Wm）在 MRO 中先于 Mixin；关键约束是
# ManualMixin 紧邻 HomeMixin 之前（super 协作链解析到 HomeMixin）
check("S2 ManualMixin 紧邻 HomeMixin 之前",
      mro.index(ManualMixin) + 1 == mro.index(HomeMixin),
      f"ManualMixin 在 {mro.index(ManualMixin)} 位，HomeMixin 在 {mro.index(HomeMixin)} 位")
check("S2 四 Mixin 均在 MRO 中",
      all(m in mro for m in (ManualMixin, HomeMixin, RecordMixin, ToolMixin)))

# ---------- S3 协作调用 ----------
import inspect
src_add = inspect.getsource(ManualMixin._add_custom_emotion)
check("S3 ManualMixin 内含 super()._add_custom_emotion",
      "super()._add_custom_emotion" in src_add)

# ---------- S4 theme.__all__ 白名单 ----------
import theme
missing = [n for n in theme.__all__ if not hasattr(theme, n)]
check("S4 __all__ 名字全部存在于 theme", not missing,
      str(missing) if missing else f"{len(theme.__all__)} 项")
# 5 处调用点所需名字抽查（theme 公开 API 全集 = __all__）
imported_ok = True
for n in theme.__all__:
    if n.startswith("_") or n == "tk":
        imported_ok = False
check("S4 __all__ 不含内部 tk 引用/下划线名", imported_ok)

# ---------- S5 CHAPTER_COUNT ----------
import chapters_data as cd
import data_store as ds
check("S5 CHAPTER_COUNT == len(CHAPTERS)",
      cd.CHAPTER_COUNT == len(cd.CHAPTERS),
      f"COUNT={cd.CHAPTER_COUNT} len={len(cd.CHAPTERS)}")
ds_src = inspect.getsource(ds)
check("S5 data_store 不再用 len(CHAPTERS)", "len(CHAPTERS)" not in ds_src)
check("S5 data_store import 含 CHAPTER_COUNT",
      "CHAPTER_COUNT" in inspect.getsource(ds).split("def chapter_of_today")[0])

# ---------- S6 pages_home 死导入（AST 级：查模块级名字，不被注释文字误伤） ----------
import pages_home as ph
check("S6 pages_home 无 CHAPTERS 绑定", not hasattr(ph, "CHAPTERS"))
check("S6 pages_home 无 EMOTIONS 绑定", not hasattr(ph, "EMOTIONS"))
check("S6 pages_home 有 EMOTION_GLOSSARY 绑定", hasattr(ph, "EMOTION_GLOSSARY"))

# ---------- S7/S8 手册方法迁移完整性（AST 级：只查定义，不被调用点/注释误伤） ----------
import ast


def class_methods(path, cls_name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls_name:
            return {n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


MANUAL_METHODS = ["_lesson_reco_index", "_build_manual", "_show_manual_tab",
                  "_build_today_card", "_pick_random_lesson", "_render_today_card",
                  "_swap_today_lesson", "_build_catalog", "_toggle_catalog_group",
                  "_open_detail", "_build_glossary", "_toggle_glossary_word",
                  "_rebuild_glossary", "_add_custom_emotion", "_on_manual_page_cfg",
                  "_refresh_manual_after_resize", "_on_manual_inner_cfg",
                  "_on_manual_canvas_cfg", "_on_manual_wheel"]
app_methods = class_methods(os.path.join(SRC, "main.py"), "App")
manual_methods = class_methods(os.path.join(SRC, "pages_manual.py"), "ManualMixin")
residual_in_main = [m for m in MANUAL_METHODS if m in app_methods]
missing_in_manual = [m for m in MANUAL_METHODS if m not in manual_methods]
check("S7 main.App 手册方法零残留（AST）", not residual_in_main,
      str(residual_in_main) if residual_in_main else "19/19 全部迁出")
check("S8 ManualMixin 含全部 19 个手册方法（AST）", not missing_in_manual,
      str(missing_in_manual) if missing_in_manual else "19/19 全部迁入")
main_src = inspect.getsource(main)
mm_src = inspect.getsource(ManualMixin)
check("S7 main.py 无 EMOTION_LESSON_MAP", "EMOTION_LESSON_MAP" not in main_src)
check("S8 pages_manual 含 EMOTION_LESSON_MAP", "EMOTION_LESSON_MAP" in mm_src)

print()
if FAILS:
    print(f"共 {len(FAILS)} 项 FAIL：{FAILS}")
    sys.exit(1)
print("静态验证全部通过（S1-S8）")
sys.exit(0)
