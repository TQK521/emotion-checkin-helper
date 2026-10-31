# -*- coding: utf-8 -*-
"""pages_tool.py —— 工具功能模块（工具组员负责）

职责范围（只准改本文件内的工具箱）：
- 四个工具：呼吸训练、三步冷静法、蝴蝶拍、情绪日记。
- 呼吸引导弹窗（BreathingDialog）、情绪日记弹窗（JournalDialog）。
- 情绪日记的保存动作（调用 data_store 保存，不定义存储格式）。
- 不包含手册内容数据（在 chapters_data.py）与打卡数据格式（在 data_store.py）。

说明：本模块以 ToolMixin 形式提供方法，由 main.py 的 App 类继承组合；
两个弹窗类是独立类，直接在本模块内使用。
"""

import time
import datetime as dt
import tkinter as tk

from theme import *                      # 颜色/字体常量
from data_store import today_str, save_data, all_emotions, journal_fields
from toolkit_data import (TOOL_STATES, STATE_RECS, TOOL_GROUPS,
                          TOOL_METHODS, methods_by_group, method_by_key)
from ui_dialogs import soft_askyesno, soft_showinfo   # H9：柔和弹窗轮子


# ---------------------------------------------------------------------------
# 胶囊按钮 helper（工具页专用，Canvas 画真圆角，radius = 高度一半）
# ---------------------------------------------------------------------------
def _pill(parent, text, command, primary=True):
    """胶囊按钮（pill button）：返回 Canvas，直接 pack/grid 到父容器。

    primary=True  → COL_PRIMARY 底 + 白字（主操作）
    primary=False → COL_SOFT 底 + 深绿字（次操作）
    """
    pad_x = 20
    height = 36
    font = (FONT_FAMILY, 10, "bold" if primary else "normal")
    bg = COL_PRIMARY if primary else COL_SOFT
    fg = "#FFFFFF" if primary else COL_PRIMARY_DK
    bg_hover = COL_PRIMARY_DK if primary else COL_HOVER

    # 先临时测文字宽度
    tmp = tk.Label(parent, text=text, font=font)
    tmp.pack_forget()
    tmp.update_idletasks()
    text_w = tmp.winfo_reqwidth()
    tmp.destroy()
    width = text_w + pad_x * 2

    try:
        outer_bg = parent.cget("bg")
    except Exception:
        outer_bg = COL_BG

    c = tk.Canvas(parent, width=width, height=height, bg=outer_bg,
                  highlightthickness=0, bd=0, cursor="hand2")
    r = height // 2
    pts = [r, 0, width - r, 0, width, 0, width, r, width, height - r, width, height,
           width - r, height, r, height, 0, height, 0, height - r, 0, r, 0, 0]
    shape = c.create_polygon(pts, smooth=True, fill=bg, outline=bg)
    c.create_text(width // 2, height // 2, text=text, fill=fg, font=font)

    def on_enter(_e):
        c.itemconfig(shape, fill=bg_hover, outline=bg_hover)

    def on_leave(_e):
        c.itemconfig(shape, fill=bg, outline=bg)

    def on_click(_e):
        command()

    c.bind("<Enter>", on_enter)
    c.bind("<Leave>", on_leave)
    c.bind("<Button-1>", on_click)
    return c


# ---------------------------------------------------------------------------
# 呼吸引导弹窗
# ---------------------------------------------------------------------------
class BreathingDialog(tk.Toplevel):
    """带动画的呼吸引导：吸气→屏息→呼气，循环若干轮。"""

    def __init__(self, master, mode="478"):
        super().__init__(master)
        self.title("呼吸引导")
        self.configure(bg=COL_BG)
        self.resizable(False, False)
        self.transient(master)

        if mode == "478":
            self.phases = ["吸气", "屏息", "呼气"]
            self.durs = {"吸气": 4, "屏息": 7, "呼气": 8}
            self.rounds = 3
            title = "4-7-8 呼吸法"
            desc = "吸气 4 秒 · 屏住 7 秒 · 呼气 8 秒 · 循环 3 轮"
        elif mode == "box":
            self.phases = ["吸气", "屏息", "呼气", "屏息"]
            self.durs = {"吸气": 4, "屏息": 4, "呼气": 4}
            self.rounds = 4
            title = "盒式呼吸"
            desc = "吸气 4 秒 · 屏住 4 秒 · 呼气 4 秒 · 屏住 4 秒 · 循环 4 轮"
        elif mode == "sigh":
            self.phases = ["快吸", "补吸", "长呼"]
            self.durs = {"快吸": 2, "补吸": 2, "长呼": 6}
            self.rounds = 3
            title = "生理性叹息"
            desc = "连吸两口气 · 再缓慢深长呼气 · 循环 3 轮"
        else:
            self.phases = ["吸气", "屏息", "呼气"]
            self.durs = {"吸气": 4, "屏息": 2, "呼气": 6}
            self.rounds = 5
            title = "腹式呼吸"
            desc = "吸气 4 秒 · 屏住 2 秒 · 呼气 6 秒 · 循环 5 轮"

        self.R_MIN, self.R_MAX, self.C = 45, 140, 170
        self.running = False
        self.anim = None

        pad = tk.Frame(self, bg=COL_BG)
        pad.pack(fill="both", expand=True, padx=24, pady=18)

        tk.Label(pad, text=title, font=(FONT_FAMILY, 16, "bold"),
                 bg=COL_BG, fg=COL_PRIMARY_DK).pack()
        tk.Label(pad, text=desc, font=(FONT_FAMILY, 10),
                 bg=COL_BG, fg=COL_SUB).pack(pady=(4, 12))

        self.canvas = tk.Canvas(pad, width=340, height=340, bg=COL_BG,
                                highlightthickness=0)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(
            self.C - self.R_MIN, self.C - self.R_MIN,
            self.C + self.R_MIN, self.C + self.R_MIN,
            fill=COL_SOFT, outline=COL_PRIMARY, width=3)
        self.phase_var = tk.StringVar(value="准备就绪")
        self.count_var = tk.StringVar(value="点击开始")
        self.round_var = tk.StringVar(value="")
        tk.Label(pad, textvariable=self.phase_var, font=(FONT_FAMILY, 14, "bold"),
                 bg=COL_BG, fg=COL_PRIMARY_DK).pack(pady=(10, 0))
        tk.Label(pad, textvariable=self.count_var, font=(FONT_FAMILY, 22, "bold"),
                 bg=COL_BG, fg=COL_ACCENT).pack()
        tk.Label(pad, textvariable=self.round_var, font=(FONT_FAMILY, 10),
                 bg=COL_BG, fg=COL_SUB).pack()

        btn_row = tk.Frame(pad, bg=COL_BG)
        btn_row.pack(pady=(12, 0))
        self.start_btn = tk.Button(btn_row, text="开始", command=self.start,
                                   font=(FONT_FAMILY, 11, "bold"), relief="flat",
                                   bg=COL_PRIMARY, fg="white", padx=26, pady=6,
                                   activebackground=COL_PRIMARY_DK,
                                   activeforeground="white", cursor="hand2")
        self.start_btn.grid(row=0, column=0, padx=6)
        self.stop_btn = tk.Button(btn_row, text="停止", command=self.stop,
                                  font=(FONT_FAMILY, 11), relief="flat",
                                  bg=COL_CHIP, fg=COL_TEXT, padx=26, pady=6,
                                  activebackground=COL_LINE, cursor="hand2")
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.plan = []  # 展开后的 (轮次, 阶段) 序列
        self.phase_idx = 0
        self.t0 = 0

    def start(self):
        """开始/重开呼吸动画。"""
        self.stop()
        self.plan = [(r, p) for r in range(1, self.rounds + 1) for p in self.phases]
        self.phase_idx = 0
        self.t0 = time.time()
        self.running = True
        self.start_btn.config(text="重来")
        self.tick()

    def stop(self):
        """停止动画，圆恢复初始大小。"""
        self.running = False
        if self.anim:
            self.after_cancel(self.anim)
            self.anim = None
        self.canvas.coords(self.circle,
                           self.C - self.R_MIN, self.C - self.R_MIN,
                           self.C + self.R_MIN, self.C + self.R_MIN)
        self.phase_var.set("已暂停")
        self.count_var.set("")

    def tick(self):
        """按阶段推进动画：吸气圆变大、屏息保持、呼气圆变小。"""
        if not self.running:
            return
        rnd, phase = self.plan[self.phase_idx]
        dur = self.durs[phase]
        elapsed = time.time() - self.t0
        if elapsed >= dur:
            self.phase_idx += 1
            if self.phase_idx >= len(self.plan):
                self.running = False
                self.phase_var.set("完成 ✓")
                self.count_var.set("感谢你的这几分钟")
                self.round_var.set("")
                self.canvas.coords(self.circle,
                                   self.C - self.R_MIN, self.C - self.R_MIN,
                                   self.C + self.R_MIN, self.C + self.R_MIN)
                self.start_btn.config(text="再来一轮")
                return
            self.t0 = time.time()
            elapsed = 0.0
            rnd, phase = self.plan[self.phase_idx]

        frac = elapsed / dur
        if phase in ("吸气", "快吸", "补吸"):
            r = self.R_MIN + (self.R_MAX - self.R_MIN) * frac
        elif phase == "屏息":
            r = self.R_MAX
        else:
            r = self.R_MAX - (self.R_MAX - self.R_MIN) * frac
        self.canvas.coords(self.circle, self.C - r, self.C - r, self.C + r, self.C + r)
        self.phase_var.set(f"第 {rnd} 轮 · {phase}")
        self.count_var.set(str(max(1, int(dur - elapsed) + (0 if (dur - elapsed) % 1 == 0 else 1))))
        self.round_var.set(f"还剩 {len(self.plan) - self.phase_idx} 个阶段")
        self.anim = self.after(50, self.tick)


# ---------------------------------------------------------------------------
# 情绪日记弹窗
# ---------------------------------------------------------------------------
class JournalDialog(tk.Toplevel):
    """情绪日记：三问（事件/感受/打算）+ 情绪词标签辅助。"""

    def __init__(self, master, on_save):
        super().__init__(master)
        self.on_save = on_save
        self.title("情绪日记")
        self.configure(bg=COL_BG)
        self.resizable(False, False)
        self.transient(master)
        self._master = master

        pad = tk.Frame(self, bg=COL_BG)
        pad.pack(fill="both", expand=True, padx=24, pady=18)
        tk.Label(pad, text="记三句话就够", font=(FONT_FAMILY, 15, "bold"),
                 bg=COL_BG, fg=COL_PRIMARY_DK).pack(anchor="w")

        # 第一问：发生了什么
        tk.Label(pad, text="刚才发生了什么事？", font=(FONT_FAMILY, 10, "bold"),
                 bg=COL_BG, fg=COL_TEXT).pack(anchor="w", pady=(14, 2))
        tk.Label(pad, text="1-2句写客观事实就好，不用加对错评价（示例：机房值班出了小故障 / 今天只睡了两小时睡不着）",
                 font=(FONT_FAMILY, 9), bg=COL_BG, fg=COL_SUB,
                 anchor="w", justify="left", wraplength=340).pack(anchor="w")
        self.event_text = tk.Text(pad, width=40, height=2, font=(FONT_FAMILY, 10),
                                  bg="white", relief="flat",
                                  highlightbackground=COL_LINE, highlightthickness=1,
                                  wrap="word")
        self.event_text.pack(fill="x", pady=(4, 0))

        # 第二问：感受如何
        tk.Label(pad, text="我身体和心里是什么感觉？", font=(FONT_FAMILY, 10, "bold"),
                 bg=COL_BG, fg=COL_TEXT).pack(anchor="w", pady=(12, 2))
        tk.Label(pad, text="可以写身体反应，也可以选情绪词，不用勉强精准（点下面的词，或自己写）",
                 font=(FONT_FAMILY, 9), bg=COL_BG, fg=COL_SUB,
                 anchor="w", justify="left", wraplength=340).pack(anchor="w")
        self.feeling_text = tk.Text(pad, width=40, height=2, font=(FONT_FAMILY, 10),
                                     bg="white", relief="flat",
                                     highlightbackground=COL_LINE, highlightthickness=1,
                                     wrap="word")
        self.feeling_text.pack(fill="x", pady=(4, 0))

        # 情绪词标签区（第二问下方，流式）
        self.emotion_chip_frame = tk.Frame(pad, bg=COL_BG)
        self.emotion_chip_frame.pack(fill="x", pady=(6, 0))

        # 第三问：可以怎么做（视觉弱化）
        tk.Label(pad, text="接下来我想做点什么？（选填）", font=(FONT_FAMILY, 9),
                 bg=COL_BG, fg=COL_SUB).pack(anchor="w", pady=(12, 2))
        tk.Label(pad, text="可以是1件小事，也可以是一句想对自己说的话，不想写就空着",
                 font=(FONT_FAMILY, 8), bg=COL_BG, fg=COL_SUB,
                 anchor="w", justify="left", wraplength=340).pack(anchor="w")
        self.action_text = tk.Text(pad, width=40, height=2, font=(FONT_FAMILY, 10),
                                   bg="white", relief="flat",
                                   highlightbackground=COL_LINE, highlightthickness=1,
                                   wrap="word")
        self.action_text.pack(fill="x", pady=(4, 0))

        btn = tk.Button(pad, text="记下了", command=self._save,
                        font=(FONT_FAMILY, 11, "bold"), relief="flat",
                        bg=COL_PRIMARY, fg="white", padx=30, pady=6,
                        activebackground=COL_PRIMARY_DK, activeforeground="white",
                        cursor="hand2")
        btn.pack(pady=(16, 0))

        # 渲染情绪词标签（需要 master.data）
        self._render_emotion_chips()
        # H5：Esc 关闭弹窗；Ctrl+Enter 快速保存（不用挪鼠标点「记下了」）
        self.bind("<Escape>", lambda ev: self.destroy())
        self.bind("<Control-Return>", lambda ev: self._save())

    def _render_emotion_chips(self):
        """流式渲染情绪词标签，点击追加到 feeling_text 末尾。"""
        try:
            words = all_emotions(self._master.data)
        except Exception:
            words = []
        max_row_w = 360
        row = None
        row_w = 0
        for word in words:
            probe = tk.Button(self.emotion_chip_frame, text=word,
                              font=(FONT_FAMILY, 9), padx=8, pady=4,
                              highlightthickness=1)
            req = probe.winfo_reqwidth()
            probe.destroy()
            if row is None or row_w + req + 4 > max_row_w:
                row = tk.Frame(self.emotion_chip_frame, bg=COL_BG)
                row.pack(anchor="w", pady=2)
                row_w = 0
            b = tk.Button(row, text=word, font=(FONT_FAMILY, 9),
                          relief="flat", bg=COL_CARD, fg=COL_TEXT, bd=0,
                          highlightbackground=COL_LINE, highlightthickness=1,
                          padx=8, pady=4, cursor="hand2",
                          activebackground=COL_HOVER,
                          command=lambda w=word: self._append_emotion(w))
            b.pack(side="left", padx=3, pady=2)
            row_w += req + 3

    def _append_emotion(self, word):
        """点击情绪词 → 追加到感受框末尾（顿号分隔）。"""
        current = self.feeling_text.get("1.0", "end-1c").strip()
        if current:
            if not current.endswith("、"):
                self.feeling_text.insert("end-1c", "、")
        self.feeling_text.insert("end", word)
        self.feeling_text.focus_set()

    def _save(self):
        """保存三框内容（分别 strip）并关闭弹窗。"""
        event = self.event_text.get("1.0", "end-1c").strip()
        feeling = self.feeling_text.get("1.0", "end-1c").strip()
        action = self.action_text.get("1.0", "end-1c").strip()
        self.on_save(event, feeling, action)
        self.destroy()


# ---------------------------------------------------------------------------
# 工具页 mixin
# ---------------------------------------------------------------------------
class ToolMixin:
    """工具箱页的页面方法集合。"""

    def _build_tool(self):
        """构建工具箱页：状态分流 → 3 条最快推荐 → 原四工具常驻 → 科学方法库（分组折叠）。

        v1.6.5 波1：内容由四卡平铺扩展为「状态分流 + 推荐卡 + 方法库折叠」，
        并引入滚动容器（复用手册页标准模式：居中 place → Canvas+Scrollbar → inner）。
        """
        page = self.pages["tool"]
        # 滚动容器：居中 place + Canvas + Scrollbar（复用手册页标准模式）
        self.tool_center = tk.Frame(page, bg=COL_BG)
        self.tool_center.place(relx=0.5, anchor="n", relheight=1, width=1600)
        page.bind("<Configure>", self._on_tool_page_cfg)
        self.tool_canvas = tk.Canvas(self.tool_center, bg=COL_BG,
                                     highlightthickness=0)
        self.tool_sb = tk.Scrollbar(self.tool_center, orient="vertical",
                                    command=self.tool_canvas.yview)
        self.tool_canvas.configure(yscrollcommand=self.tool_sb.set)
        self.tool_canvas.pack(side="left", fill="both", expand=True)
        self.tool_sb.pack(side="right", fill="y")
        self.tool_inner = tk.Frame(self.tool_canvas, bg=COL_BG, width=1600)
        self.tool_win = self.tool_canvas.create_window(
            (0, 0), window=self.tool_inner, anchor="nw")
        self.tool_inner.bind("<Configure>", self._on_tool_inner_cfg)
        self.tool_canvas.bind("<Configure>", self._on_tool_canvas_cfg)
        self._tool_cw = content_width(1600)

        # 滚轮全局化（核心约束八）：进入工具页区域才 bind_all，离开 unbind_all
        self.tool_center.bind("<Enter>", lambda e: self.tool_center.bind_all(
            "<MouseWheel>", self._on_tool_wheel))
        self.tool_center.bind("<Leave>", lambda e: self.tool_center.unbind_all(
            "<MouseWheel>"))

        col = self.tool_inner
        # 长文本登记列表（窗口缩放防抖统一重排 wraplength，见 _refresh_tool_after_resize）
        self._tool_wrap_labels = []

        tk.Label(col, text="情绪工具箱", font=self.f_title, bg=COL_BG,
                 fg=COL_TEXT).pack(anchor="w", padx=12, pady=(20, 4))
        tk.Label(col, text="情绪上来了不用硬扛，挑一个慢慢用。", font=self.f_small,
                 bg=COL_BG, fg=COL_SUB).pack(anchor="w", padx=12, pady=(0, 10))

        # ① 状态分流 chips（新增）
        self._tool_state_var = tk.StringVar(value="acute")
        scard = rounded_card(col)
        scard.pack(fill="x", padx=12, pady=7)
        tk.Label(scard, text="我现在是……", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_PRIMARY_DK).pack(anchor="w", padx=10, pady=(12, 6))
        self._tool_chip_wrap = tk.Frame(scard, bg=COL_CARD)
        self._tool_chip_wrap.pack(fill="x", anchor="w", padx=10, pady=(0, 12))
        self._tool_state_chips = []
        # 窗口显示后按真实宽度流式重排 chips（字体初始化后 reqwidth 才真实）
        self.after(0, self._reflow_tool_chips)

        # ② 推荐卡（新增：按所选状态 3 条最快 + 立即开始）
        self._tool_rec_card = rounded_card(col)
        self._tool_rec_card.pack(fill="x", padx=12, pady=7)
        tk.Label(self._tool_rec_card, text="推荐给你", font=self.f_body_b,
                 bg=COL_CARD, fg=COL_PRIMARY_DK).pack(anchor="w", padx=10,
                                                      pady=(12, 2))
        self._tool_rec_hint = tk.Label(self._tool_rec_card, text="", font=self.f_small,
                                       bg=COL_CARD, fg=COL_SUB, anchor="w",
                                       justify="left", wraplength=self._tool_cw - 80)
        self._tool_rec_hint.pack(fill="x", padx=10)
        self._tool_wrap_labels.append(self._tool_rec_hint)
        self._tool_rec_body = tk.Frame(self._tool_rec_card, bg=COL_CARD)
        self._tool_rec_body.pack(fill="x", padx=10, pady=(6, 0))
        self._tool_rec_detail = tk.Label(self._tool_rec_card, text="", font=self.f_small,
                                         bg=COL_CARD, fg=COL_TEXT, anchor="w",
                                         justify="left",
                                         wraplength=self._tool_cw - 80)
        self._tool_rec_detail.pack(fill="x", padx=10, pady=(6, 12))
        self._tool_wrap_labels.append(self._tool_rec_detail)
        self._build_tool_recs()

        # ③ 呼吸（原四工具常驻，布局不动）
        card = rounded_card(col)
        card.pack(fill="x", padx=12, pady=7)
        tk.Label(card, text="呼吸训练", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_PRIMARY_DK).pack(anchor="w", padx=10, pady=(14, 4))
        self._tool_breath_label = tk.Label(
            card, text="跟着圆圈呼吸：吸气时圆变大，呼气时圆变小。",
            font=self.f_small, bg=COL_CARD, fg=COL_SUB,
            anchor="w", wraplength=self._tool_cw - 80)
        self._tool_breath_label.pack(fill="x", padx=10)
        self._tool_wrap_labels.append(self._tool_breath_label)
        brow = tk.Frame(card, bg=COL_CARD)
        brow.pack(fill="x", padx=12, pady=(12, 16))
        _pill(brow, "4-7-8 呼吸", lambda: BreathingDialog(self, "478"),
              primary=True).pack(side="left", padx=(0, 10))
        _pill(brow, "腹式呼吸", lambda: BreathingDialog(self, "belly"),
              primary=False).pack(side="left")
        _pill(brow, "盒式呼吸", lambda: BreathingDialog(self, "box"),
              primary=False).pack(side="left", padx=(10, 0))
        _pill(brow, "生理性叹息", lambda: BreathingDialog(self, "sigh"),
              primary=False).pack(side="left", padx=(10, 0))

        # ④ 三步冷静法
        card2 = rounded_card(col)
        card2.pack(fill="x", padx=12, pady=7)
        tk.Label(card2, text="三步冷静法", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_PRIMARY_DK).pack(anchor="w", padx=10, pady=(14, 4))
        self._tool_calm_label = tk.Label(
            card2, text="情绪上头时：① 暂停手上的动作 ② 做 3 次深呼吸 ③ 再决定下一步。",
            font=self.f_small, bg=COL_CARD, fg=COL_TEXT, anchor="w",
            justify="left", wraplength=self._tool_cw - 80)
        self._tool_calm_label.pack(fill="x", padx=10, pady=(0, 16))
        self._tool_wrap_labels.append(self._tool_calm_label)

        # ⑤ 蝴蝶拍
        card3 = rounded_card(col)
        card3.pack(fill="x", padx=12, pady=7)
        tk.Label(card3, text="蝴蝶拍", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_PRIMARY_DK).pack(anchor="w", padx=10, pady=(14, 4))
        self._tool_butterfly_label = tk.Label(
            card3, text="双臂在胸前交叉，双手轮流轻轻拍打自己肩膀，左右各一次为一组，做 6 到 8 组，边拍边告诉自己“我在安全的地方”。",
            font=self.f_small, bg=COL_CARD, fg=COL_TEXT, anchor="w",
            justify="left", wraplength=self._tool_cw - 80)
        self._tool_butterfly_label.pack(fill="x", padx=10, pady=(0, 16))
        self._tool_wrap_labels.append(self._tool_butterfly_label)

        # ⑥ 科学方法库（新增：分组折叠）
        self._toolkit_collapsed = set()
        for gkey, _, _ in TOOL_GROUPS[1:]:
            self._toolkit_collapsed.add(gkey)   # 默认第一组展开，其余收起
        self._toolkit_open = set()              # 已展开步骤的方法 key
        self._toolkit_box = tk.Frame(col, bg=COL_BG)
        self._toolkit_box.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(self._toolkit_box, text="科学方法库", font=self.f_body_b,
                 bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=4, pady=(0, 2))
        tk.Label(self._toolkit_box, text="都是经过科学验证、随时能用的方法，想细看哪组就点开。",
                 font=self.f_small, bg=COL_BG, fg=COL_SUB).pack(anchor="w",
                                                                padx=4, pady=(0, 6))
        self._toolkit_body = tk.Frame(self._toolkit_box, bg=COL_BG)
        self._toolkit_body.pack(fill="x")
        self._build_toolkit_lib()

        # ⑦ 情绪日记（原卡常驻）
        card4 = rounded_card(col)
        card4.pack(fill="x", padx=12, pady=7)
        tk.Label(card4, text="情绪日记", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_PRIMARY_DK).pack(anchor="w", padx=10, pady=(14, 4))
        tk.Label(card4, text="写三句话：刚才发生了什么、身体心里什么感觉、接下来想做点什么。",
                 font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                 anchor="w").pack(anchor="w", padx=10)
        _pill(card4, "写今天的日记",
              lambda: JournalDialog(self, self._save_journal),
              primary=True).pack(anchor="w", padx=10, pady=(12, 8))
        _pill(card4, "查看全部日记", self._show_journal_all,
              primary=False).pack(anchor="w", padx=10, pady=(0, 8))
        self.journal_label = tk.Label(card4, text="", font=self.f_small, bg=COL_CARD,
                                      fg=COL_SUB, anchor="w",
                                      wraplength=self._tool_cw - 80)
        self.journal_label.pack(fill="x", padx=12, pady=(0, 14))
        self._tool_wrap_labels.append(self.journal_label)

    # ---------------- 工具页新增方法（v1.6.5 波1） ----------------

    def _on_tool_inner_cfg(self, ev):
        """内容尺寸变化时刷新滚动区域（0 起，避免 bbox 起点偏移）。"""
        self.tool_canvas.configure(scrollregion=(0, 0, ev.width, ev.height))

    def _on_tool_canvas_cfg(self, ev):
        """画布（=居中容器）尺寸变化时：内容宽度跟随画布、左缘 0；维护当前内容宽。"""
        self.tool_canvas.itemconfigure(self.tool_win, width=ev.width)
        self.tool_canvas.coords(self.tool_win, 0, 0)
        self._tool_cw = content_width(ev.width)

    def _on_tool_wheel(self, ev):
        """工具页滚轮滚动（全局 bind_all；守卫：切页后隐藏容器不响应残留触发）。"""
        if not self.tool_center.winfo_viewable():
            return
        self.tool_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")

    def _reflow_tool_chips(self):
        """按画布实际宽流式重排状态 chips（窗口显示后触发，字体已初始化）。"""
        if not (hasattr(self, "_tool_chip_wrap") and self._tool_chip_wrap.winfo_exists()):
            return
        wrap = self._tool_chip_wrap
        max_row = max(80, getattr(self, "_tool_cw", 1600) - 40)
        for w in wrap.winfo_children():
            w.destroy()
        self._tool_state_chips = []
        row, row_w = None, 0
        for key, label in TOOL_STATES:
            probe = tk.Radiobutton(wrap, text=label, value=key,
                                   variable=self._tool_state_var,
                                   font=self.f_small, indicatoron=0,
                                   relief="flat", cursor="hand2", bg=COL_CHIP,
                                   fg=COL_SUB, activebackground=COL_HOVER,
                                   activeforeground=COL_PRIMARY_DK,
                                   highlightthickness=1,
                                   highlightbackground=COL_LINE,
                                   highlightcolor=COL_LINE, padx=10, pady=2)
            req = probe.winfo_reqwidth()
            probe.destroy()
            if row is None or row_w + req + 4 > max_row:
                row = tk.Frame(wrap, bg=COL_CARD)
                row.pack(anchor="w", pady=2)
                row_w = 0
            chip = tk.Radiobutton(row, text=label, value=key,
                                  variable=self._tool_state_var,
                                  font=self.f_small, indicatoron=0,
                                  relief="flat", cursor="hand2", bg=COL_CHIP,
                                  fg=COL_SUB, activebackground=COL_HOVER,
                                  activeforeground=COL_PRIMARY_DK,
                                  highlightthickness=1,
                                  highlightbackground=COL_LINE,
                                  highlightcolor=COL_LINE, padx=10, pady=2,
                                  command=self._refresh_tool_state_chips)
            chip.pack(side="left", padx=(6, 0))
            self._tool_state_chips.append(chip)
            row_w += req + 6
        self._refresh_tool_state_chips()

    def _refresh_tool_state_chips(self):
        """状态 chip 选中态刷新：选中=主色浅底+主色描边+深字；未选=浅灰底+淡描边。"""
        for chip in self._tool_state_chips:
            sel = (self._tool_state_var.get() == chip["value"])
            chip.configure(bg=COL_SOFT if sel else COL_CHIP,
                           fg=COL_PRIMARY_DK if sel else COL_SUB,
                           highlightbackground=COL_PRIMARY if sel else COL_LINE,
                           highlightcolor=COL_PRIMARY if sel else COL_LINE)
        self._build_tool_recs()

    def _build_tool_recs(self):
        """按当前所选状态渲染 3 条最快推荐 + 立即开始按钮。"""
        for w in self._tool_rec_body.winfo_children():
            w.destroy()
        self._tool_rec_detail.config(text="")
        st = self._tool_state_var.get()
        label = dict(TOOL_STATES).get(st, "")
        keys = STATE_RECS.get(st, [])
        if not keys:
            self._tool_rec_hint.config(text="")
            return
        self._tool_rec_hint.config(text=f"现在最合适的是这 {len(keys)} 条，挑一个马上用：")
        for key in keys:
            m = method_by_key(key)
            if not m:
                continue
            head = tk.Frame(self._tool_rec_body, bg=COL_CARD)
            head.pack(fill="x", pady=(4, 0))
            tk.Label(head, text=m["name"], font=self.f_body_b, bg=COL_CARD,
                     fg=COL_PRIMARY_DK, anchor="w").pack(side="left")
            tk.Label(head, text=m["time"], font=self.f_small, bg=COL_CARD,
                     fg=COL_ACCENT, anchor="w").pack(side="left", padx=(6, 0))
            _pill(head, "立即开始", lambda k=key: self._start_tool_method(k),
                  primary=True).pack(side="right")
            why_l = tk.Label(self._tool_rec_body, text=m["why"], font=self.f_small,
                             bg=COL_CARD, fg=COL_SUB, anchor="w", justify="left",
                             wraplength=self._tool_cw - 80)
            why_l.pack(fill="x", padx=2, pady=(2, 0))
            self._tool_wrap_labels.append(why_l)
        self.update_idletasks()

    def _start_tool_method(self, key):
        """点「立即开始」：呼吸类开对应呼吸弹窗；其他在推荐卡下方展开步骤。"""
        m = method_by_key(key)
        if not m:
            return
        action = m.get("action")
        if action == "breath_sigh":
            BreathingDialog(self, "sigh")
        elif action == "breath_478":
            BreathingDialog(self, "478")
        elif action == "breath_box":
            BreathingDialog(self, "box")
        else:
            steps = "\n".join("· " + s for s in m["steps"])
            self._tool_rec_detail.config(
                text=f"{m['name']}（{m['time']}）怎么做：\n{steps}")

    def _build_toolkit_lib(self):
        """方法库分组折叠渲染：每组头（▼/▲ 切换），展开组显示方法条目卡。"""
        for w in self._toolkit_body.winfo_children():
            w.destroy()
        cw = getattr(self, "_tool_cw", 1600)
        wrap = max(40, cw - 56)
        for gkey, gname, gdesc in TOOL_GROUPS:
            ms = methods_by_group(gkey)
            collapsed = gkey in self._toolkit_collapsed
            mark = "▼" if not collapsed else "▲"
            head = tk.Label(self._toolkit_body,
                            text=f"{gname}（{len(ms)} 条）  {mark}",
                            font=self.f_body_b, bg=COL_GROUP_HEAD, fg=COL_TEXT,
                            anchor="w", padx=12, pady=6, cursor="hand2")
            head.pack(fill="x", pady=(6, 0))
            head.bind("<Button-1>", lambda e, g=gkey: self._toggle_toolkit_group(g))
            if collapsed:
                continue
            tk.Label(self._toolkit_body, text=gdesc, font=self.f_small,
                     bg=COL_BG, fg=COL_SUB, anchor="w").pack(fill="x", padx=4,
                                                             pady=(4, 0))
            for m in ms:
                card = rounded_card(self._toolkit_body)
                card.pack(fill="x", pady=4)
                head2 = tk.Frame(card, bg=COL_CARD)
                head2.pack(fill="x", padx=10, pady=(10, 0))
                tk.Label(head2, text=m["name"], font=self.f_body_b, bg=COL_CARD,
                         fg=COL_PRIMARY_DK, anchor="w").pack(side="left")
                tk.Label(head2, text=m["time"], font=self.f_small, bg=COL_CARD,
                         fg=COL_ACCENT, anchor="w").pack(side="left", padx=(6, 0))
                tk.Label(head2, text=m["evidence"], font=(FONT_FAMILY, 9),
                         bg=COL_CARD, fg=COL_SUB, anchor="e").pack(side="right")
                why_l = tk.Label(card, text=m["why"], font=self.f_small,
                                 bg=COL_CARD, fg=COL_TEXT, anchor="w",
                                 justify="left", wraplength=wrap)
                why_l.pack(fill="x", padx=10, pady=(4, 0))
                if m["key"] in self._toolkit_open:
                    steps = "\n".join("· " + s for s in m["steps"])
                    st_l = tk.Label(card, text=steps, font=self.f_small,
                                    bg=COL_CARD, fg=COL_SUB, anchor="w",
                                    justify="left", wraplength=wrap)
                    st_l.pack(fill="x", padx=10, pady=(4, 0))
                _pill(card,
                      "收起步骤" if m["key"] in self._toolkit_open else "展开步骤",
                      lambda k=m["key"]: self._toggle_toolkit_steps(k),
                      primary=False).pack(anchor="w", padx=10, pady=(8, 10))
        self.update_idletasks()
        if hasattr(self, "tool_canvas"):
            self.tool_canvas.configure(scrollregion=self.tool_canvas.bbox("all"))

    def _toggle_toolkit_group(self, gkey):
        """切换方法库分组折叠状态并重建（H14：重建后保持滚动位置）。"""
        yv0 = self.tool_canvas.yview()[0] if hasattr(self, "tool_canvas") else 0.0
        if gkey in self._toolkit_collapsed:
            self._toolkit_collapsed.discard(gkey)
        else:
            self._toolkit_collapsed.add(gkey)
        self._build_toolkit_lib()
        self.update_idletasks()
        if hasattr(self, "tool_canvas"):
            self.tool_canvas.configure(scrollregion=self.tool_canvas.bbox("all"))
            self.tool_canvas.yview_moveto(yv0)

    def _toggle_toolkit_steps(self, key):
        """切换单条方法的步骤展开/收起并重建方法库（H14：重建后保持滚动位置）。"""
        yv0 = self.tool_canvas.yview()[0] if hasattr(self, "tool_canvas") else 0.0
        if key in self._toolkit_open:
            self._toolkit_open.discard(key)
        else:
            self._toolkit_open.add(key)
        self._build_toolkit_lib()
        self.update_idletasks()
        if hasattr(self, "tool_canvas"):
            self.tool_canvas.configure(scrollregion=self.tool_canvas.bbox("all"))
            self.tool_canvas.yview_moveto(yv0)

    def _on_tool_page_cfg(self, ev):
        """工具页宽变化：居中容器跟随收窄/放宽（封顶 content_width），并防抖重排长文本。

        v1.6.2：此前仅容器收窄，已渲染文本仍按旧宽换行 → 窗口非 1600 时
        长文本横向溢出被遮挡。窗口宽变化后延迟 180ms 原地更新登记过的
        全部长文本 wraplength（状态提示/推荐明细/原四工具/日记预览/方法库），
        工具页已有滚动容器，不做 yview。
        """
        cw = content_width(ev.width)
        self.tool_center.place_configure(width=cw)
        self._tool_cw = cw
        if getattr(self, "_tool_resize_after", None) is not None:
            try:
                self.after_cancel(self._tool_resize_after)
            except Exception:
                pass
        self._tool_resize_after = self.after(
            180, self._refresh_tool_after_resize)

    def _refresh_tool_after_resize(self):
        """窗口宽变化防抖回调：按最新内容宽原地更新所有登记长文本 wraplength。

        留白口径：页面 padx20×2 + 卡内 padx20×2 = 80；原地 configure 不重建卡片，
        折叠态、展开步骤态、日记预览文本均不受影响。
        """
        if not (hasattr(self, "tool_center") and self.tool_center.winfo_exists()):
            return
        cw = getattr(self, "_tool_cw", 1600)
        wrap = max(40, cw - 80)
        for lbl in getattr(self, "_tool_wrap_labels", []):
            try:
                if lbl.winfo_exists():
                    lbl.config(wraplength=wrap)
            except Exception:
                pass
        self.update_idletasks()

    def _save_journal(self, event, feeling, action):
        """保存一篇情绪日记（追加到 journal 列表，三字段独立）。"""
        event = event.strip()
        feeling = feeling.strip()
        action = action.strip()
        self.data.setdefault("journal", []).append({
            "date": today_str(),
            "time": dt.datetime.now().strftime("%H:%M"),
            "event": event,
            "feeling": feeling,
            "action": action,
        })
        save_data(self.data)
        self.refresh_tool()

    def _show_journal_all(self):
        """弹窗查看全部日记：每天大日期一次 + 每条具体时间，可滚动，支持单篇删除。"""
        j = self.data.get("journal", [])
        if not j:
            soft_showinfo(self, "情绪日记", "还没有写过日记。难受的时候，来写三句话。")
            return
        win = tk.Toplevel(self)
        win.title("情绪日记 · 全部")
        win.configure(bg=COL_BG)
        win.geometry("640x520")
        win.transient(self)
        self._jall_toplevel = win
        pad = tk.Frame(win, bg=COL_BG)
        pad.pack(fill="both", expand=True, padx=20, pady=14)
        self._jall_count = tk.Label(pad, font=(FONT_FAMILY, 12, "bold"),
                                    bg=COL_BG, fg=COL_PRIMARY_DK)
        self._jall_count.pack(anchor="w")
        body = tk.Frame(pad, bg=COL_BG)
        body.pack(fill="both", expand=True, pady=(8, 0))
        self._jall_canvas = tk.Canvas(body, bg=COL_BG, highlightthickness=0)
        self._jall_sb = tk.Scrollbar(body, orient="vertical",
                                     command=self._jall_canvas.yview)
        self._jall_canvas.configure(yscrollcommand=self._jall_sb.set)
        self._jall_canvas.pack(side="left", fill="both", expand=True)
        self._jall_sb.pack(side="right", fill="y")
        self._jall_inner = tk.Frame(self._jall_canvas, bg=COL_BG)
        self._jall_win = self._jall_canvas.create_window(
            (0, 0), window=self._jall_inner, anchor="nw")
        self._jall_inner.bind(
            "<Configure>", lambda e: self._jall_canvas.configure(
                scrollregion=(0, 0, e.width, e.height)))
        # 弹窗可缩放：画布宽变化 → 内窗口跟随 + 防抖原地更新条目标签 wraplength
        self._jall_wrap_labels = []
        self._jall_wrap = 552   # 640 默认弹窗下的估算（canvas≈584 − 卡 padx4×2 − 内容 padx12×2）
        self._jall_resize_after = None
        self._jall_canvas.bind("<Configure>", self._on_jall_canvas_cfg)
        self._render_journal_list(j)
        self._bind_jall_wheel(self._jall_inner)

    def _render_journal_list(self, j):
        """渲染全部日记列表：每条独立卡片（头部时间+删除，内容按字段分行）。"""
        for w in self._jall_inner.winfo_children():
            w.destroy()
        self._jall_wrap_labels = []
        self._jall_count.config(
            text=f"情绪日记 · 共 {len(j)} 篇（一直保存，删除需确认）")
        last_day = None
        for idx in range(len(j) - 1, -1, -1):
            e = j[idx]
            if e["date"] != last_day:
                tk.Label(self._jall_inner, text=e["date"],
                         font=(FONT_FAMILY, 12, "bold"), bg=COL_BG,
                         fg=COL_PRIMARY_DK).pack(fill="x", pady=(10, 2))
                last_day = e["date"]
            # 独立卡片
            card = tk.Frame(self._jall_inner, bg=COL_CARD,
                            highlightbackground=COL_LINE, highlightthickness=1)
            card.pack(fill="x", pady=4, padx=4)
            # 头部行：时间 + 删除按钮
            header = tk.Frame(card, bg=COL_CARD)
            header.pack(fill="x", padx=12, pady=(8, 4))
            t = e.get("time") or "—"
            tk.Label(header, text=t, font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                     anchor="w").pack(side="left")
            tk.Button(header, text="删除", font=(FONT_FAMILY, 9),
                      bg=COL_CARD, fg=COL_SUB, relief="flat", bd=0,
                      cursor="hand2", activebackground=COL_CARD,
                      activeforeground="#B00020",
                      command=lambda i=idx: self._delete_journal(i)).pack(side="right")
            # 内容按字段分行（journal_fields 兼容旧数据）
            event, feeling, action = journal_fields(e)
            has_content = False
            if event:
                lbl = tk.Label(card, text=f"📌 事件：{event}",
                         font=self.f_small, bg=COL_CARD, fg=COL_TEXT,
                         anchor="w", justify="left", wraplength=self._jall_wrap)
                lbl.pack(fill="x", padx=12, pady=(0, 2))
                self._jall_wrap_labels.append(lbl)
                has_content = True
            if feeling:
                lbl = tk.Label(card, text=f"💭 感受：{feeling}",
                         font=self.f_small, bg=COL_CARD, fg=COL_TEXT,
                         anchor="w", justify="left", wraplength=self._jall_wrap)
                lbl.pack(fill="x", padx=12, pady=(0, 2))
                self._jall_wrap_labels.append(lbl)
                has_content = True
            if action:
                lbl = tk.Label(card, text=f"✨ 打算：{action}",
                         font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                         anchor="w", justify="left", wraplength=self._jall_wrap)
                lbl.pack(fill="x", padx=12, pady=(0, 8))
                self._jall_wrap_labels.append(lbl)
                has_content = True
            if not has_content:
                tk.Label(card, text="（这篇没写内容）",
                         font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                         anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    def _delete_journal(self, idx):
        """删除一篇日记（确认后落盘，刷新弹窗与工具页预览）。"""
        if not soft_askyesno(self._jall_canvas, "删除这篇日记",
                             "确定删除这篇日记吗？删除后无法恢复。"):
            return
        j = self.data.get("journal", [])
        if 0 <= idx < len(j):
            del j[idx]
            save_data(self.data)
            self.refresh_tool()
            if j:
                self._render_journal_list(j)
            else:
                self._jall_toplevel.destroy()

    def _bind_jall_wheel(self, widget):
        """递归给全部日记弹窗的控件绑定鼠标滚轮。"""
        try:
            widget.bind("<MouseWheel>", lambda e: self._jall_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))
        except Exception:
            pass
        for ch in widget.winfo_children():
            self._bind_jall_wheel(ch)

    def _on_jall_canvas_cfg(self, ev):
        """弹窗画布宽变化：内窗口跟随 + 防抖原地更新条目标签 wraplength（不重建列表）。"""
        self._jall_canvas.itemconfigure(self._jall_win, width=ev.width)
        self._jall_wrap = max(120, ev.width - 32)
        if self._jall_resize_after is not None:
            try:
                self.after_cancel(self._jall_resize_after)
            except Exception:
                pass
        self._jall_resize_after = self.after(150, self._refresh_jall_wraps)

    def _refresh_jall_wraps(self):
        """弹窗防抖回调：原地更新已渲染条目标签 wraplength（不重渲染、不影响删除联动）。"""
        for lbl in getattr(self, "_jall_wrap_labels", []):
            try:
                if lbl.winfo_exists():
                    lbl.config(wraplength=self._jall_wrap)
            except Exception:
                pass

    def refresh_tool(self):
        """切到工具页时刷新最近一篇日记预览（摘要：event 优先，空则 feeling）。"""
        if hasattr(self, "journal_label"):
            j = self.data.get("journal", [])
            if j:
                last = j[-1]
                event, feeling, _ = journal_fields(last)
                t = last.get("time") or "—"
                summary = (event or feeling or "")[:40]
                if summary:
                    self.journal_label.config(
                        text=f"最近一篇（{last['date']} {t}）：{summary}")
                else:
                    self.journal_label.config(text="")
            else:
                self.journal_label.config(text="")
