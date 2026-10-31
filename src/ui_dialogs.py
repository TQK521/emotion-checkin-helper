# -*- coding: utf-8 -*-
"""ui_dialogs.py —— 通用柔和弹窗轮子（视觉组件，全项目复用，H9）

用途：替代 Windows 原生 messagebox，与护眼柔和 UI 调性统一。
- soft_askyesno(parent, title, message) -> bool   确认弹窗（确定/取消）
- soft_showinfo(parent, title, message)           提示弹窗（只一个确定）
样式：米白底 + 圆角白卡 + 薄荷绿主按钮 + 浅灰次按钮，居中于主窗口。
用法：from ui_dialogs import soft_askyesno, soft_showinfo
"""

import tkinter as tk

from theme import *


def _center_on(parent, win, ww, wh):
    """弹窗相对主窗口居中（约 1/3 高度）。"""
    try:
        master = parent.winfo_toplevel()
        x = master.winfo_rootx() + (master.winfo_width() - ww) // 2
        y = master.winfo_rooty() + (master.winfo_height() - wh) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    except Exception:
        pass


def _soft_dialog(parent, title, message, ok_text="好的", cancel_text=None):
    """通用柔和弹窗：返回 True=确定 / False=取消或关闭；仅确定按钮时返回 None。

    - 圆角白卡 + 标题 + 消息（自动换行）+ 按钮行；
    - Return=确定、Escape=取消/关闭；grab_set 模态。
    """
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=COL_BG)
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    card = rounded_card(win)
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text=title, font=(FONT_FAMILY, 12, "bold"),
             bg=COL_CARD, fg=COL_PRIMARY_DK).pack(padx=24, pady=(18, 6))
    tk.Label(card, text=message, font=(FONT_FAMILY, 10), bg=COL_CARD,
             fg=COL_TEXT, anchor="w", justify="left", wraplength=380
             ).pack(padx=24, pady=(0, 14))

    result = {"v": False}

    def _ok():
        result["v"] = True
        win.destroy()

    def _cancel():
        win.destroy()

    btns = tk.Frame(card, bg=COL_CARD)
    btns.pack(fill="x", padx=24, pady=(0, 16))
    if cancel_text:
        tk.Button(btns, text=cancel_text, font=(FONT_FAMILY, 10), relief="flat",
                  bd=0, bg=COL_CARD, fg=COL_SUB, cursor="hand2",
                  activebackground=COL_CARD, activeforeground=COL_PRIMARY_DK,
                  command=_cancel).pack(side="right", padx=(12, 0))
    tk.Button(btns, text=ok_text, font=(FONT_FAMILY, 10, "bold"), relief="flat",
              bg=COL_PRIMARY, fg="white", padx=18, pady=6, cursor="hand2",
              activebackground=COL_PRIMARY_DK, activeforeground="white",
              command=_ok).pack(side="right")
    win.bind("<Return>", lambda ev: _ok())
    win.bind("<Escape>", lambda ev: _cancel())

    win.update_idletasks()
    _center_on(parent, win, win.winfo_reqwidth(), win.winfo_reqheight())
    parent.wait_window(win)
    return result["v"]


def soft_askyesno(parent, title, message):
    """确认弹窗：True=确定，False=取消/关闭（替代 messagebox.askyesno）。"""
    return _soft_dialog(parent, title, message, ok_text="确定", cancel_text="取消")


def soft_showinfo(parent, title, message):
    """提示弹窗：单确定按钮（替代 messagebox.showinfo）。"""
    _soft_dialog(parent, title, message, ok_text="好的")


def tooltip_tip(widget, text, delay_ms=500):
    """为控件绑定悬停释义提示（Hover Tooltip，v1.6.8）。

    - 鼠标进入 delay_ms 后显示小标签（overrideredirect 无边框，跟随意念在
      控件正下方 +4px，自动换行限宽 280px，不打断操作流）；
    - 移出即销毁（已注册 after 一并取消）；返回句柄 dict 供外部销毁。
    已踩坑（实验 _exp_tooltip.py）：Toplevel 必须以 widget.winfo_toplevel()
    为 master——Toplevel(widget) 会挂到 widget 子级，顶层遍历抓不到。
    """
    st = {"after_id": None, "win": None}

    def _show():
        top = widget.winfo_toplevel()
        st["win"] = tk.Toplevel(top)
        st["win"].overrideredirect(True)
        x, y = widget.winfo_rootx(), widget.winfo_rooty()
        tk.Label(st["win"], text=text, bg="#fffbe6", fg=COL_TEXT,
                 font=(FONT_FAMILY, 9), wraplength=280, justify="left",
                 padx=8, pady=4).pack()
        st["win"].geometry(f"+{x}+{y + widget.winfo_height() + 4}")

    def _enter(_ev):
        st["after_id"] = widget.after(delay_ms, _show)

    def _leave(_ev):
        if st["after_id"]:
            widget.after_cancel(st["after_id"])
            st["after_id"] = None
        if st["win"]:
            st["win"].destroy()
            st["win"] = None

    widget.bind("<Enter>", _enter)
    widget.bind("<Leave>", _leave)
    return st
