# -*- coding: utf-8 -*-
"""main.py —— 主框架模块（主框架组员负责）

职责范围（只准改本文件内的框架层）：
- App 类组装（继承各页面 mixin）、整体布局、页面切换、底部导航。
- 窗口属性（尺寸 / 全屏）、字体构建。
- 入口 main() 与启动器 bat 的配合。
- 不写各页内部细节（页面细节在各 pages_*.py）。

启动方式：
  双击 scripts/qidongdaka.bat，或运行：python src/main.py
  打卡数据保存在【项目根目录】的 checkin_data.json（见 data_store.py）。
"""

import os
import sys

import datetime as dt
import tkinter as tk
from tkinter import font as tkfont

from theme import *                     # 颜色/字体常量
from data_store import (load_data,        # 数据读取 / 启动序列
                        check_data_file, quarantine_corrupt_file, auto_backup)
from ui_dialogs import soft_showinfo    # 柔和提示弹窗（H9 轮子）
from pages_manual import ManualMixin    # 手册页（成长 Tab，v1.6.10 自 main 拆分）
from pages_home import HomeMixin        # 打卡页
from pages_record import RecordMixin    # 记录页
from pages_tool import ToolMixin        # 工具箱

try:  # Windows 高 DPI 下让文字更清晰
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


class App(tk.Tk, ManualMixin, HomeMixin, RecordMixin, ToolMixin):
    """主应用：组合五个页面 mixin，管理窗口与页面切换。

    ⚠ MRO 顺序约束：ManualMixin 必须排在 HomeMixin 之前——
    手册页 _add_custom_emotion 通过 super() 调用 HomeMixin 实现（写入+save_data+
    首页标签重建），成功后重建手册词库区；颠倒顺序则词库区添加后不刷新。
    """

    def __init__(self):
        super().__init__()
        # 窗口左上角图标（打包/源码双形态定位；.ico 放 exe 同目录或项目根）
        _base = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _icon_path = os.path.join(_base, "xuexiqingxudaka.ico")
        if os.path.exists(_icon_path):
            self.iconbitmap(_icon_path)
        self.title("学习情绪打卡 · 随时记录")
        self.geometry("500x700")
        self.minsize(500, 600)
        self.configure(bg=COL_BG)
        self.state("zoomed")  # 打开即占满屏幕

        # 数据安全启动序列（v1.6.7）：自检 → 损坏保留现场并提示 → 自动备份 → 加载
        _st, _detail = check_data_file()
        if _st == "corrupt":
            _saved = quarantine_corrupt_file()
            _msg = (f"检测到打卡数据文件已损坏（{_detail}），\n"
                    f"已把原文件保留为：{_saved}\n"
                    "本次将以空数据启动，原文件不会被覆盖。")
            soft_showinfo(self, "数据文件损坏", _msg)
            _st = "missing"  # 现场已隔离，后续按首次启动处理
        auto_backup()  # 数据正常时自动留档，保留最近 7 份
        self.data = load_data()

        self._build_fonts()
        self._build_layout()
        self.show_page("home")

    # ---------- 字体 ----------
    def _build_fonts(self):
        """预构建各字号字体，供所有页面共用（self.f_xxx）。"""
        self.f_small = tkfont.Font(family=FONT_FAMILY, size=10)
        self.f_body = tkfont.Font(family=FONT_FAMILY, size=11)
        self.f_body_b = tkfont.Font(family=FONT_FAMILY, size=10, weight="bold")
        self.f_title = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
        self.f_big = tkfont.Font(family=FONT_FAMILY, size=18, weight="bold")

    # ---------- 整体布局 ----------
    def _build_layout(self):
        """页面区域 + 底部四键导航 + 预构建四个页面。"""
        self.page_area = tk.Frame(self, bg=COL_BG)
        self.page_area.pack(fill="both", expand=True)

        # 底部导航：打卡 / 成长 / 记录 / 工具
        # 底色与页面一致（COL_BG），无粗边框；选中 Tab 显示浅薄荷绿文字 + 2px 下划线
        nav = tk.Frame(self, bg=COL_BG)
        nav.pack(side="bottom", fill="x")
        self.nav_btns = {}
        self.nav_inds = {}
        items = [("home", "打卡"), ("manual", "成长"), ("record", "记录"), ("tool", "工具")]
        for i, (key, text) in enumerate(items):
            col = tk.Frame(nav, bg=COL_BG)
            col.grid(row=0, column=i, sticky="nsew", padx=2, pady=(8, 8))
            nav.grid_columnconfigure(i, weight=1)
            b = tk.Button(col, text=text, font=(FONT_FAMILY, 11, "bold"),
                          relief="flat", bd=0, bg=COL_BG, fg=COL_SUB,
                          activebackground=COL_BG, activeforeground=COL_PRIMARY,
                          command=lambda k=key: self.show_page(k), cursor="hand2")
            b.pack(fill="x")
            ind = tk.Frame(col, bg=COL_BG, height=2)   # 选中态 2px 下划线（平时同底色）
            ind.pack(fill="x", padx=12, pady=(6, 0))
            self.nav_btns[key] = b
            self.nav_inds[key] = ind

        # 四个页面容器
        self.pages = {}
        for key in items:
            key = key[0]
            self.pages[key] = tk.Frame(self.page_area, bg=COL_BG)
        # 预先构建内容
        self._build_home()
        self._build_manual()
        self._build_record()
        self._build_tool()

    def show_page(self, key):
        """切换到指定页面，并刷新该页数据展示。"""
        for k, f in self.pages.items():
            f.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, b in self.nav_btns.items():
            b.config(fg=COL_PRIMARY if k == key else COL_SUB)
            self.nav_inds[k].config(bg=COL_PRIMARY if k == key else COL_BG)
        if key == "record":
            self.refresh_record()
        if key == "tool":
            self.refresh_tool()
        if key == "home":
            self.refresh_home()

    # ---------- 启动 ----------
    def run(self):
        self.mainloop()


def main():
    """程序入口：创建主窗口并进入事件循环；启动失败时给出友好提示。"""
    try:
        app = App()
        app.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", f"程序启动时出错：\n{e}")
            root.destroy()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
