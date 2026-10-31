# -*- coding: utf-8 -*-
"""pages_home.py —— 打卡流程模块（打卡组员负责）

职责范围（只准改本文件内的打卡页交互流程）：
- 首页布局：问候卡、情绪命名卡、一句话输入、记录按钮、今日一课卡。
- 情绪多选标签、自定义输入、记录写入动作。
- 记录写入时只调用 data_store 的数据函数，不自行定义存储格式。
- 不包含手册内容数据（在 chapters_data.py）与存储格式（在 data_store.py）。

说明：本模块以 HomeMixin 形式提供方法，由 main.py 的 App 类继承组合，
因此方法内部通过 self 访问字体属性（self.f_xxx）、数据（self.data）等。
"""

import datetime as dt
import random
import tkinter as tk
from collections import Counter
from tkinter import font as tkfont

from theme import *                      # 颜色/字体常量
from chapters_data import EMOTION_GLOSSARY   # 悬停释义（CHAPTERS/EMOTIONS 未使用，已清理）
from data_store import (records_today, calc_streak, chapter_of_today,
                        fmt_emotions, greeting, save_data, make_record,
                        all_emotions)
from ui_dialogs import (soft_showinfo, soft_askyesno,
                        tooltip_tip)    # H9 柔和弹窗 + v1.6.8 悬停释义轮子

# 内容区宽度统一走 theme.content_width（CONTENT_MAX=1920 公共契约），
# 本文件不再定义本地 content_width（v1.6.2 删除本地写死 1600 的遮蔽函数）。

# 场景单选选项（可选字段，未选不强求）——统一走 theme.SCENES 公共契约（波1冻结），本地不另定义


class HomeMixin:
    """打卡首页（按次记录）的页面方法集合。"""

    def _build_home(self):
        """构建首页滚动容器：居中容器(place) + Canvas 滚动，内容宽跟随居中容器、封顶随 theme。"""
        self.home = self.pages["home"]
        # 居中容器：固定宽居中（复用记录/工具页已验证的 place 方案），窄窗动态收窄
        self.home_center = tk.Frame(self.home, bg=COL_BG)
        self.home_center.place(relx=0.5, anchor="n", relheight=1, width=1600)
        # 当前内容宽（首次 Configure 前的初始估计，首帧后由 _on_home_canvas_cfg 修正）
        self._home_cw = 1200
        self._home_resize_after = None
        self.home.bind("<Configure>", self._on_home_page_cfg)
        self.home_canvas = tk.Canvas(self.home_center, bg=COL_BG,
                                     highlightthickness=0)
        self.home_sb = tk.Scrollbar(self.home_center, orient="vertical",
                                    command=self.home_canvas.yview)
        self.home_canvas.configure(yscrollcommand=self.home_sb.set)
        self.home_canvas.pack(side="left", fill="both", expand=True)
        self.home_sb.pack(side="right", fill="y")
        self.home_inner = tk.Frame(self.home_canvas, bg=COL_BG, width=1600)
        self.home_win = self.home_canvas.create_window(
            (0, 0), window=self.home_inner, anchor="nw")
        self.home_inner.bind("<Configure>", self._on_home_inner_cfg)
        self.home_canvas.bind("<Configure>", self._on_home_canvas_cfg)
        # 滚轮全局化（核心约束八）：进入首页区域才 bind_all，离开 unbind_all；
        # 禁止构建期一次性递归绑定（防抖重排后新建控件会失去递归绑定）。
        self.home_center.bind("<Enter>", lambda e: self.home_center.bind_all(
            "<MouseWheel>", self._on_home_wheel))
        self.home_center.bind("<Leave>", lambda e: self.home_center.unbind_all(
            "<MouseWheel>"))
        self._rebuild_home()

    def _on_home_page_cfg(self, ev):
        """页面宽变化：居中容器跟随收窄/放宽（封顶随 theme CONTENT_MAX），并防抖原地重排。

        v1.6.2：此前仅容器收窄，已渲染文本仍按旧宽换行 → 非默认宽时长文本横向溢出。
        窗口宽变化后延迟 180ms 原地更新 wraplength + 重排 chips（禁止 _rebuild_home，
        会清空用户已选情绪）。
        """
        self.home_center.place_configure(width=content_width(ev.width))
        if getattr(self, "_home_resize_after", None) is not None:
            try:
                self.after_cancel(self._home_resize_after)
            except Exception:
                pass
        self._home_resize_after = self.after(
            180, self._refresh_home_after_resize)

    def _refresh_home_after_resize(self):
        """窗口宽变化防抖回调：原地更新 4 个 wraplength + 重排 chips，保持滚动位置。

        状态红线：禁止调用 _rebuild_home（会重置 selected_emotions 与表单输入）。
        """
        if not (getattr(self, "home_center", None) and self.home_center.winfo_exists()):
            return
        cw = getattr(self, "_home_cw", 1200)
        if hasattr(self, "emo_selected_label"):
            self.emo_selected_label.config(wraplength=cw - 72)
        if hasattr(self, "record_done_label"):
            self.record_done_label.config(wraplength=cw - 40)
        if hasattr(self, "record_summary_label"):
            self.record_summary_label.config(wraplength=cw - 40)
        if hasattr(self, "home_bottom_tip_label"):
            self.home_bottom_tip_label.config(wraplength=cw - 40)
        for lbl in ("greeting_label", "greeting_date_label", "emo_subtitle_label"):
            if hasattr(self, lbl):
                getattr(self, lbl).config(wraplength=cw - 72)
        self._layout_head_count()
        yv0 = self.home_canvas.yview()
        self._reflow_chips()
        self.home_canvas.update_idletasks()
        self.home_canvas.yview_moveto(yv0[0])

    def _on_home_inner_cfg(self, ev):
        """内容尺寸变化时刷新滚动区域（0 起，避免 bbox 起点偏移导致内容贴右）。"""
        self.home_canvas.configure(scrollregion=(0, 0, ev.width, ev.height))

    def _on_home_canvas_cfg(self, ev):
        """画布（=居中容器）尺寸变化时：内容宽度跟随画布、左缘 0；维护当前内容宽。"""
        self.home_canvas.itemconfigure(self.home_win, width=ev.width)
        self.home_canvas.coords(self.home_win, 0, 0)
        self._home_cw = content_width(ev.width)

    def _on_home_wheel(self, ev):
        """首页滚动支持鼠标滚轮（全局 bind_all；守卫：切页后隐藏容器不响应残留触发）。"""
        if not self.home_center.winfo_viewable():
            return
        self.home_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")

    def _rebuild_home(self):
        """重建首页：清空后重画头部与记录表单（按次记录，始终可记）。"""
        for w in self.home_inner.winfo_children():
            w.destroy()
        self.home_ready = False
        self.selected_emotions = []
        self._last_rec = None   # H4：重建后无待撤销记录

        # 顶部：标题块居中 + 右上角弱化计数（count 用 place 悬浮）
        self.head_frame = tk.Frame(self.home_inner, bg=COL_BG)
        self.head_frame.pack(fill="x", padx=12, pady=(16, 6))
        self.head_frame.grid_columnconfigure(0, weight=1)
        self.head_frame.grid_columnconfigure(1, weight=0)
        self.head_frame.grid_columnconfigure(2, weight=1)
        block = tk.Frame(self.head_frame, bg=COL_BG)
        block.grid(row=0, column=1)
        tk.Label(block, text="学习情绪打卡", font=(FONT_FAMILY, 18, "bold"),
                 bg=COL_BG, fg=COL_TEXT).pack()
        tk.Label(block, text="接纳当下，难受就说出来", font=self.f_small,
                 bg=COL_BG, fg=COL_SUB).pack(pady=(2, 0))
        # 窄窗计数行容器：立即 pack（位于 head 与问候卡之间），宽窗时留空（0 高度）
        self.home_count_row = tk.Frame(self.home_inner, bg=COL_BG)
        self.home_count_row.pack(fill="x", padx=12)
        # 计数标签 master=home_inner（可 place 进 head_frame 或 pack 进 count_row）
        self.head_count_label = tk.Label(self.home_inner, text="", font=(FONT_FAMILY, 9),
                                         bg=COL_BG, fg=COL_SUB)
        self._update_head_count()
        self._layout_head_count()

        self._show_home_record()

    def _update_head_count(self):
        """刷新右上角"今天已记录 N 次"。"""
        if hasattr(self, "head_count_label"):
            self.head_count_label.config(
                text=f"今天已记录 {len(records_today(self.data))} 次")

    def _layout_head_count(self):
        """窄窗避让：_home_cw<900 时计数标签从标题行右侧移到独立行；否则保持右上角。

        home_count_row 在 _rebuild_home 中已 pack 在 head 与问候卡之间（位置固定）；
        宽窗时行内留空（0 高度），窄窗时 pack 标签进入行。
        计数标签 master=home_inner，可 place(in_=head_frame) 或 pack(in_=home_count_row)。
        """
        if not hasattr(self, "head_count_label"):
            return
        cw = getattr(self, "_home_cw", 1600)
        if cw < 900:
            # 窄窗：从 head 的 place 移出 → pack 进已在正确位置的 count_row
            try:
                self.head_count_label.place_forget()
            except Exception:
                pass
            self.head_count_label.pack(in_=self.home_count_row, anchor="w", pady=(0, 4))
        else:
            # 宽窗：从 count_row pack 移出 → place 回 head 右上角（count_row 留空=0高度）
            try:
                self.head_count_label.pack_forget()
            except Exception:
                pass
            self.head_count_label.place(
                in_=self.head_frame, relx=1.0, x=-8, y=8, anchor="ne")

    def _show_home_record(self):
        """记录表单：问候卡 + 情绪命名（多选+自定义） + 一句话 + 记录按钮 + 今日一课。"""
        recs = self.data.get("records", [])

        # 问候卡（圆角卡片，卡内留白加大）
        card = rounded_card(self.home_inner)
        card.pack(fill="x", padx=12, pady=6)
        self.greeting_label = tk.Label(
            card, text=f"{greeting()}，难受的时候，把它说出来。",
            font=(FONT_FAMILY, 12, "bold"), bg=COL_CARD, fg=COL_TEXT,
            anchor="center", wraplength=self._home_cw - 72)
        self.greeting_label.pack(fill="x", padx=10, pady=(12, 4))
        self.greeting_date_label = tk.Label(
            card, text=f"{dt.date.today().strftime('%m月%d日 %A')} · 今天已记录 {len(records_today(self.data))} 次 · 累计 {len(recs)} 次",
            font=self.f_small, bg=COL_CARD, fg=COL_SUB, anchor="center",
            wraplength=self._home_cw - 72)
        self.greeting_date_label.pack(fill="x", padx=10, pady=(0, 12))

        # 情绪命名卡（圆角卡片）
        emo_card = rounded_card(self.home_inner)
        emo_card.pack(fill="x", padx=12, pady=6)
        tk.Label(emo_card, text="给此刻的情绪起个名字",
                 font=self.f_body_b, bg=COL_CARD, fg=COL_PRIMARY_DK, anchor="center"
                 ).pack(fill="x", padx=10, pady=(12, 0))
        self.emo_subtitle_label = tk.Label(
            emo_card, text="说出名字，它就开始变小（情绪标记）· 情绪复杂时可以多选",
            font=self.f_small, bg=COL_CARD, fg=COL_SUB, anchor="center",
            wraplength=self._home_cw - 72)
        self.emo_subtitle_label.pack(fill="x", padx=10, pady=(0, 8))

        # 情绪标签：构建期只建 chip_frame，按钮由 after(0,_reflow_chips)
        # 按实际宽流式创建（master=行 Frame，避免 pack(in_) 不改父级的残留）
        chip_frame = tk.Frame(emo_card, bg=COL_CARD)
        chip_frame.pack(fill="x", padx=10, pady=(0, 4))
        self.chip_frame = chip_frame
        self.chip_btns = {}

        entry_row = tk.Frame(emo_card, bg=COL_CARD)
        entry_row.pack(fill="x", padx=10, pady=(4, 8))
        wrap = tk.Frame(entry_row, bg=COL_CARD)
        wrap.pack(anchor="center")
        tk.Label(wrap, text="或自己起个名字：", font=self.f_small,
                 bg=COL_CARD, fg=COL_SUB).pack(side="left")
        self.emo_entry = tk.Entry(wrap, font=(FONT_FAMILY, 10), relief="flat",
                                  bg=COL_INPUT_BG, highlightbackground=COL_LINE,
                                  highlightthickness=1, width=14)
        self.emo_entry.pack(side="left", padx=6, ipady=6)
        self.emo_entry.bind("<KeyRelease>", lambda ev: self._update_emotion_label())
        self.emo_selected_label = tk.Label(emo_card, text="", font=self.f_body_b,
                                           bg=COL_CARD, fg=COL_ACCENT, anchor="w",
                                           wraplength=self._home_cw - 72)
        self.emo_selected_label.pack(fill="x", padx=10, pady=(0, 8))

        # 场景单选（可选，chip 样式：浅灰底+描边，选中=主色浅底+主色描边+深字，未选不强求）
        self.scene_var = tk.StringVar(value="")
        scene_row = tk.Frame(emo_card, bg=COL_CARD)
        scene_row.pack(fill="x", padx=10, pady=(0, 4))
        scene_wrap = tk.Frame(scene_row, bg=COL_CARD)
        scene_wrap.pack(anchor="center")
        tk.Label(scene_wrap, text="此刻发生了什么（可选）：", font=self.f_small,
                 bg=COL_CARD, fg=COL_SUB).pack(side="left")
        self._scene_chips = []
        for opt in SCENES:
            # v1.6.9：Radiobutton → Button 手动管理单选+取消（场景可选；
            # Radiobutton 无法"再次点击取消"且 class 点击绑定不可程序化验证）
            chip = tk.Button(scene_wrap, text=opt, font=self.f_small,
                             relief="flat", cursor="hand2",
                             bg=COL_CHIP, fg=COL_SUB,
                             activebackground=COL_HOVER,
                             activeforeground=COL_PRIMARY_DK,
                             highlightthickness=1,
                             highlightbackground=COL_LINE,
                             highlightcolor=COL_LINE,
                             padx=10, pady=2,
                             command=lambda o=opt: self._on_scene_click(o))
            chip.opt = opt
            chip.pack(side="left", padx=(6, 0))
            self._scene_chips.append(chip)

        # 强度选择（1-5，默认 3，chip 样式 + 弱/强刻度标注，选中主色高亮）
        self.intensity_var = tk.IntVar(value=3)
        inten_row = tk.Frame(emo_card, bg=COL_CARD)
        inten_row.pack(fill="x", padx=10, pady=(0, 12))
        inten_wrap = tk.Frame(inten_row, bg=COL_CARD)
        inten_wrap.pack(anchor="center")
        tk.Label(inten_wrap, text="强度 1–5，5 最强烈：", font=self.f_small,
                 bg=COL_CARD, fg=COL_SUB).pack(side="left")
        tk.Label(inten_wrap, text="弱", font=self.f_small, bg=COL_CARD,
                 fg=COL_SUB).pack(side="left", padx=(8, 2))
        self._inten_chips = []
        for i in range(1, 6):
            # v1.6.9：方形数字按钮 → 圆形按钮（Canvas 自绘，荧光黄+外发光选中态）
            chip = circle_pick_btn(inten_wrap, str(i),
                                   selected=(i == self.intensity_var.get()),
                                   command=self._on_inten_click)
            chip.pack(side="left", padx=4)
            self._inten_chips.append((chip, str(i)))
        tk.Label(inten_wrap, text="强", font=self.f_small, bg=COL_CARD,
                 fg=COL_SUB).pack(side="left", padx=(2, 0))
        self._refresh_inten_chips()  # 初始高亮默认强度 3

        # 一句话输入卡（圆角卡片）
        note_card = rounded_card(self.home_inner)
        note_card.pack(fill="x", padx=12, pady=6)
        tk.Label(note_card, text="此刻想说的一句话（可选）",
                 font=self.f_body_b, bg=COL_CARD, fg=COL_PRIMARY_DK, anchor="center"
                 ).pack(fill="x", padx=10, pady=(12, 4))
        self.note_entry = tk.Text(note_card, font=(FONT_FAMILY, 10), relief="flat",
                                  bg=COL_INPUT_BG, highlightbackground=COL_LINE,
                                  highlightthickness=1, fg=COL_SUB,
                                  height=3, wrap="word", padx=6, pady=6)
        self.note_entry.insert("1.0", "例如：复习不下去，心里堵得慌")
        self.note_entry.bind("<FocusIn>", lambda ev: self._clear_note_hint())
        # H5：Ctrl+Enter 直接提交记录（回车不再只换行）
        self.note_entry.bind("<Control-Return>", lambda ev: self._record_emotion())
        self.note_entry.pack(fill="x", padx=10, pady=(0, 12))

        # 记录按钮（常亮常绿，未命名情绪时点击会给温柔提示）
        self.record_btn = tk.Button(self.home_inner, text="记录这次情绪",
                                    font=(FONT_FAMILY, 13, "bold"), relief="flat",
                                    bg=COL_PRIMARY, fg="white", pady=12,
                                    cursor="hand2", command=self._record_emotion,
                                    activebackground=COL_PRIMARY_DK,
                                    activeforeground="white")
        self.record_btn.pack(fill="x", padx=12, pady=(10, 4))

        self.record_done_label = tk.Label(self.home_inner, text="",
                                          font=self.f_body_b, bg=COL_BG,
                                          fg=COL_PRIMARY_DK, wraplength=self._home_cw - 40,
                                          justify="center")
        self.record_done_label.pack(pady=(6, 0))
        self.record_summary_label = tk.Label(self.home_inner, text="",
                                             font=self.f_small, bg=COL_BG,
                                             fg=COL_SUB, wraplength=self._home_cw - 40,
                                             justify="center")
        self.record_summary_label.pack(pady=(0, 6))

        # H3/H4：记录后的快捷操作行（撤销上一条 / 清空选择），初始隐藏
        self._post_row = tk.Frame(self.home_inner, bg=COL_BG)
        self._post_row.pack(fill="x")
        self.undo_btn = tk.Label(self._post_row, text="撤销上一条", font=self.f_small,
                                 bg=COL_BG, fg=COL_SUB, cursor="hand2",
                                 padx=8, pady=2)
        self.undo_btn.pack_forget()
        self.undo_btn.bind("<Button-1>", lambda ev: self._undo_last_record())
        self.clear_btn = tk.Label(self._post_row, text="清空选择", font=self.f_small,
                                  bg=COL_BG, fg=COL_SUB, cursor="hand2",
                                  padx=8, pady=2)
        self.clear_btn.pack_forget()
        self.clear_btn.bind("<Button-1>", lambda ev: self._clear_form())

        # 今日一课已移至「成长」页（v1.6.1：打卡页专注记录，避免重复模块）
        self.home_bottom_tip_label = tk.Label(
            self.home_inner,
            text="每一次难受都值得被看见。记完之后，去「工具」页做几次呼吸也行。",
            font=self.f_small, bg=COL_BG, fg=COL_SUB, wraplength=self._home_cw - 40,
            justify="center")
        self.home_bottom_tip_label.pack(pady=(0, 8))
        # mainloop 启动、窗口显示后按实际宽重排标签（此时字体已初始化，reqwidth 真实）
        self.after(0, self._reflow_chips)
        # 滚轮绑定已全局化（_build_home 中 home_center <Enter>/<Leave>），此处不再递归绑定

    def _on_scene_click(self, opt):
        """场景单选 + 再次点击取消（v1.6.9：Button 手动管理，command 触发时
        variable 尚未更新，天然区分首次选中/再次取消）。"""
        if self.scene_var.get() == opt:
            self.scene_var.set("")   # 再次点击已选项 → 取消
        else:
            self.scene_var.set(opt)  # 首次/切换 → 选中（天然单选）
        self._refresh_scene_chips()

    def _refresh_scene_chips(self):
        """场景 chip 选中态刷新：选中=主色浅底+主色描边+深字；未选=浅灰底+淡描边。"""
        for chip in self._scene_chips:
            sel = (self.scene_var.get() == chip.opt)
            chip.configure(bg=COL_SOFT if sel else COL_CHIP,
                           fg=COL_PRIMARY_DK if sel else COL_SUB,
                           highlightbackground=COL_PRIMARY if sel else COL_LINE,
                           highlightcolor=COL_PRIMARY if sel else COL_LINE)

    def _on_inten_click(self, text):
        """强度圆钮单选（1-5，值语义不变；点击已选项保持选中，不取消）。"""
        self.intensity_var.set(int(text))
        self._refresh_inten_chips()

    def _refresh_inten_chips(self):
        """强度圆钮选中态重绘：选中=荧光黄+外发光环（v1.6.9 圆钮组件）。"""
        for canvas, txt in self._inten_chips:
            redraw_circle(canvas, txt, self.intensity_var.get() == int(txt))

    def _clear_note_hint(self):
        """清空"一句话"输入框的示例提示。"""
        if self.note_entry.get("1.0", "end-1c").strip() == "例如：复习不下去，心里堵得慌":
            self.note_entry.delete("1.0", "end")

    def _reflow_chips(self):
        """按画布实际宽流式创建情绪标签（after(0) 触发，窗口已显示、字体已初始化）。

        标签来源 = all_emotions(self.data)（内置 + 用户自定义，词库生长）；
        尾部追加「＋ 添加情绪词」柔和小按钮（参与流式换行）。
        按钮直接创建在行 Frame 下（master=row），避免 pack(in_) 不改父级导致的
        chip_frame 残留 Button 子级；先销毁旧行及旧按钮再重建，最后恢复选中态高亮。
        """
        if not getattr(self, "chip_frame", None):
            return
        # v1.6.2：宽度统一取 _home_cw（theme.content_width，封顶随 CONTENT_MAX=1920），
        # 不再 winfo_width() 兜底写死 1600。
        cw = getattr(self, "_home_cw", 1200)
        if cw < 400:
            cw = 1200
        max_row_w = cw - 72   # 40 卡外 padx + 32 chip padx
        # 销毁旧行 Frame 及其中的旧按钮（self.chip_btns 引用一并清空）
        for w in self.chip_frame.winfo_children():
            w.destroy()
        self.chip_btns = {}
        row = None
        row_w = 0

        def new_row():
            nonlocal row, row_w
            row = tk.Frame(self.chip_frame, bg=COL_CARD)
            row.pack(anchor="center", pady=3)
            row_w = 0

        # H2：按历史使用频次降序置顶（用过的词靠前），未用过的词保持原序在后
        freq = Counter()
        for r in self.data.get("records", []):
            for e in r.get("emotions", []):
                freq[e] += 1
        words = sorted(all_emotions(self.data), key=lambda w: -freq.get(w, 0))
        for emo in words:
            # 探针测请求宽（reqwidth 与父容器无关），决定行归属
            probe = tk.Button(self.chip_frame, text=emo, font=(FONT_FAMILY, 10),
                              padx=10, pady=6, highlightthickness=1)
            req = probe.winfo_reqwidth()
            probe.destroy()
            if row is None or row_w + req + 6 > max_row_w:
                new_row()
            b = tk.Button(row, text=emo, font=(FONT_FAMILY, 10),
                          relief="flat", bg=COL_CARD, fg=COL_TEXT, bd=0,
                          highlightbackground=COL_LINE, highlightthickness=1,
                          padx=10, pady=6, cursor="hand2",
                          activebackground=COL_HOVER,
                          command=lambda e=emo: self._pick_emotion(e))
            b.pack_forget()   # 幂等保险：首次 pack 前调用无害
            b.pack(side="left", padx=6, pady=3)
            b.bind("<Enter>", lambda _ev, e=emo: self._chip_enter(e))
            b.bind("<Leave>", lambda _ev, e=emo: self._chip_leave(e))
            # v1.6.8：内置词悬停释义提示（成长页情绪词库同源；自定义词不在本次范围）
            gloss = EMOTION_GLOSSARY.get(emo)
            if gloss:
                tooltip_tip(b, gloss)
            self.chip_btns[emo] = b
            row_w += req + 6

        # 尾部：「＋ 添加情绪词」柔和小按钮（样式同标签，浅薄荷绿文字）
        add_text = "＋ 添加情绪词"
        probe = tk.Button(self.chip_frame, text=add_text, font=(FONT_FAMILY, 10),
                          padx=10, pady=6, highlightthickness=1)
        req = probe.winfo_reqwidth()
        probe.destroy()
        if row is None or row_w + req + 6 > max_row_w:
            new_row()
        self.add_btn = tk.Button(row, text=add_text, font=(FONT_FAMILY, 10),
                                 relief="flat", bg=COL_CARD, fg=COL_PRIMARY, bd=0,
                                 highlightbackground=COL_LINE, highlightthickness=1,
                                 padx=10, pady=6, cursor="hand2",
                                 activebackground=COL_HOVER,
                                 command=self._open_add_emotion_dialog)
        self.add_btn.pack_forget()
        self.add_btn.pack(side="left", padx=6, pady=3)
        self.add_btn.bind("<Enter>", lambda _ev: self._add_chip_enter())
        self.add_btn.bind("<Leave>", lambda _ev: self._add_chip_leave())
        # 重建后恢复选中态高亮（新词可立即复选）
        self._update_emotion_label()

    def _chip_enter(self, emo):
        """标签 hover：未选中时柔和变 COL_HOVER（选中态保持原选中色）。"""
        if emo not in self.selected_emotions:
            self.chip_btns[emo].config(bg=COL_HOVER)

    def _chip_leave(self, emo):
        """标签离开：未选中时恢复白底 COL_CARD。"""
        if emo not in self.selected_emotions:
            self.chip_btns[emo].config(bg=COL_CARD)

    def _add_chip_enter(self):
        """「＋ 添加情绪词」hover：柔和变 COL_HOVER（文字保持薄荷绿）。"""
        if getattr(self, "add_btn", None) is not None:
            self.add_btn.config(bg=COL_HOVER)

    def _add_chip_leave(self):
        """「＋ 添加情绪词」离开：恢复白底。"""
        if getattr(self, "add_btn", None) is not None:
            self.add_btn.config(bg=COL_CARD)

    def _open_add_emotion_dialog(self):
        """「＋ 添加情绪词」弹窗：白底圆角、居中、柔和；情绪词必填 + 解释可选。"""
        win = tk.Toplevel(self.home)
        win.title("添加情绪词")
        win.configure(bg=COL_BG)
        win.resizable(False, False)
        win.transient(self.home)
        win.grab_set()
        card = rounded_card(win)
        card.pack(fill="both", expand=True, padx=14, pady=14)
        tk.Label(card, text="给词库加一个情绪词",
                 font=self.f_body_b, bg=COL_CARD, fg=COL_PRIMARY_DK).pack(padx=24, pady=(16, 2))
        tk.Label(card, text="以后它也会出现在标签里，可以多选",
                 font=self.f_small, bg=COL_CARD, fg=COL_SUB).pack(padx=24, pady=(0, 10))
        tk.Label(card, text="情绪词（必填）：", font=self.f_small,
                 bg=COL_CARD, fg=COL_SUB).pack(padx=24, anchor="w")
        word_entry = tk.Entry(card, font=(FONT_FAMILY, 10), relief="flat",
                              bg=COL_INPUT_BG, highlightbackground=COL_LINE,
                              highlightthickness=1, width=20)
        word_entry.pack(padx=24, pady=(2, 8), fill="x", ipady=5)
        tk.Label(card, text="这个词对你意味着什么（可选）：", font=self.f_small,
                 bg=COL_CARD, fg=COL_SUB).pack(padx=24, anchor="w")
        gloss_entry = tk.Entry(card, font=(FONT_FAMILY, 10), relief="flat",
                               bg=COL_INPUT_BG, highlightbackground=COL_LINE,
                               highlightthickness=1, width=20)
        gloss_entry.pack(padx=24, pady=(2, 12), fill="x", ipady=5)

        def on_add():
            if self._add_custom_emotion(word_entry.get(), gloss_entry.get()):
                win.destroy()

        btns = tk.Frame(card, bg=COL_CARD)
        btns.pack(fill="x", padx=24, pady=(0, 16))
        tk.Button(btns, text="先不了", font=self.f_small, relief="flat", bd=0,
                  bg=COL_CARD, fg=COL_SUB, cursor="hand2",
                  activebackground=COL_CARD,
                  command=win.destroy).pack(side="right", padx=(12, 0))
        tk.Button(btns, text="加入词库", font=(FONT_FAMILY, 10, "bold"), relief="flat",
                  bg=COL_PRIMARY, fg="white", padx=16, pady=6, cursor="hand2",
                  activebackground=COL_PRIMARY_DK,
                  command=on_add).pack(side="right")
        win.bind("<Return>", lambda ev: on_add())
        win.bind("<Escape>", lambda ev: win.destroy())
        word_entry.focus_set()
        # 相对主窗口居中（弹窗尺寸就绪后定位）
        win.update_idletasks()
        ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
        x = self.home.winfo_rootx() + (self.home.winfo_width() - ww) // 2
        y = self.home.winfo_rooty() + (self.home.winfo_height() - wh) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _add_custom_emotion(self, word, gloss=""):
        """加入自定义情绪词（弹窗确认逻辑）：空词/已存在词温柔提示不添加；成功后
        写入 data["custom_emotions"]（{word, gloss}）→ save_data → 重建标签。返回是否成功。"""
        w = word.strip()
        if not w:
            soft_showinfo(self.home, "还差一步", "先写下情绪词本身，我才能记住它。")
            return False
        if w in all_emotions(self.data):
            soft_showinfo(self.home, "它已经在词库里啦",
                          f"「{w}」早就在了，直接点标签就能用它。")
            return False
        self.data.setdefault("custom_emotions", []).append(
            {"word": w, "gloss": gloss.strip()})
        save_data(self.data)
        self._reflow_chips()
        return True

    def _pick_emotion(self, emo):
        """点击情绪词：可多选，再点一次取消。"""
        if emo in self.selected_emotions:
            self.selected_emotions.remove(emo)
        else:
            self.selected_emotions.append(emo)
        self._update_emotion_label()

    def _update_emotion_label(self):
        """刷新情绪词的选中高亮与"你叫它…"提示文字。"""
        for e, b in self.chip_btns.items():
            b.config(bg=COL_SOFT if e in self.selected_emotions else COL_CARD,
                     fg=COL_PRIMARY_DK if e in self.selected_emotions else COL_TEXT)
        parts = [f"「{e}」" for e in self.selected_emotions]
        custom = self.emo_entry.get().strip()
        if custom:
            parts.append(f"「{custom}」")
        if not parts:
            self.emo_selected_label.config(text="")
            return
        if len(parts) == 1:
            self.emo_selected_label.config(
                text=f"你叫它：{parts[0]}——好，你看见它了。")
        else:
            self.emo_selected_label.config(
                text=f"你叫它们：{''.join(parts)}——好，你看见它们了。")

    def _record_emotion(self):
        """记录一次情绪：写入 records（按次），清空表单并显示确认。"""
        emotions = list(self.selected_emotions)
        custom = self.emo_entry.get().strip()
        if custom:
            emotions.append(custom)
        if not emotions:
            soft_showinfo(
                self.home, "还差一步",
                "先给情绪起个名字吧——说出口，它才开始变小。\n\n"
                "可以点一个或多个情绪词，也可以自己输入一个名字。")
            return
        note = self.note_entry.get("1.0", "end-1c").strip()
        if note == "例如：复习不下去，心里堵得慌":
            note = ""
        # 经 data_store 契约构造记录（ts/date/time/emotions/action/scene/intensity）
        rec = make_record(emotions, note,
                          self.scene_var.get(), self.intensity_var.get())
        self.data.setdefault("records", []).append(rec)
        self._last_rec = rec   # H4：供撤销上一条
        d = rec["date"]
        if not self.data.get("start_date"):
            self.data["start_date"] = d
        s = calc_streak(self.data["records"])
        if s > self.data.get("best_streak", 0):
            self.data["best_streak"] = s
        save_data(self.data)

        # H3：保留已选情绪/场景/强度（可再记一条），只清备注与自定义输入
        self.emo_entry.delete(0, "end")
        self.note_entry.delete("1.0", "end")
        self.note_entry.insert("1.0", "例如：复习不下去，心里堵得慌")
        if hasattr(self, "undo_btn"):
            self.undo_btn.pack(side="left", padx=(6, 0))
            self.clear_btn.pack(side="left", padx=(6, 0))
        self.record_done_label.config(
            text="我听见了，已记录。可以再记一条，或点「清空选择」重新开始。")
        m = dt.date.today().strftime("%Y-%m")
        month_days = len({r.get("date", "") for r in self.data.get("records", [])
                          if r.get("date", "").startswith(m)})
        self.record_summary_label.config(
            text=f"今天已记录 {len(records_today(self.data))} 次・本月 {month_days} 天")
        self._sync_greeting_count()
        self._update_head_count()

    def _undo_last_record(self):
        """H4：撤销上一条记录（pop 最后一条 + 恢复表单），仅当最后一条仍是刚记的。"""
        if not getattr(self, "_last_rec", None):
            return
        recs = self.data.get("records", [])
        if not recs or recs[-1] is not self._last_rec:
            return
        recs.pop()
        save_data(self.data)
        self.selected_emotions = list(self._last_rec.get("emotions", []))
        self.scene_var.set(self._last_rec.get("scene", ""))
        self.intensity_var.set(self._last_rec.get("intensity", 3))
        action = self._last_rec.get("action", "")
        self.note_entry.delete("1.0", "end")
        if action:
            self.note_entry.insert("1.0", action)
        else:
            self.note_entry.insert("1.0", "例如：复习不下去，心里堵得慌")
        self._update_emotion_label()
        self._last_rec = None
        self.record_done_label.config(text="已撤销上一条，可以重新调整后再记录。")
        self.record_summary_label.config(text="")
        self._sync_greeting_count()
        self._update_head_count()
        if hasattr(self, "undo_btn"):
            self.undo_btn.pack_forget()
            self.clear_btn.pack_forget()

    def _clear_form(self):
        """H3：清空当前选择（重新开始），并隐藏快捷操作行。"""
        self.selected_emotions = []
        for b in self.chip_btns.values():
            b.config(bg=COL_CARD, fg=COL_TEXT)
        self.emo_entry.delete(0, "end")
        self.emo_selected_label.config(text="")
        self.note_entry.delete("1.0", "end")
        self.note_entry.insert("1.0", "例如：复习不下去，心里堵得慌")
        self.scene_var.set("")
        self.intensity_var.set(3)
        self._refresh_scene_chips()
        self._refresh_inten_chips()
        self.record_done_label.config(text="")
        self.record_summary_label.config(text="")
        self._last_rec = None
        if hasattr(self, "undo_btn"):
            self.undo_btn.pack_forget()
            self.clear_btn.pack_forget()

    def refresh_home(self):
        """切回首页：有草稿（已选情绪/输入）时保留表单只轻刷新；无草稿且
        数据/日期变化时才重建（H1：填一半切页不再丢草稿）。"""
        if not getattr(self, "home_inner", None) or not self.home_inner.winfo_children():
            self._rebuild_home()
            return
        note = ""
        if hasattr(self, "note_entry"):
            note = self.note_entry.get("1.0", "end-1c").strip()
        draft = (bool(getattr(self, "selected_emotions", []))
                 or (note and note != "例如：复习不下去，心里堵得慌"))
        if draft:
            self._light_refresh_home()
            return
        recs = self.data.get("records", [])
        fp = (dt.date.today().isoformat(), len(recs),
              recs[-1].get("ts", "") if recs else "")
        if getattr(self, "_home_fp", None) == fp:
            return
        self._home_fp = fp
        self._rebuild_home()

    def _light_refresh_home(self):
        """草稿保留时的轻刷新：更新计数与日期文案，不动表单控件。"""
        self._sync_greeting_count()
        self._update_head_count()

    def _sync_greeting_count(self):
        """同步问候卡日期行的计数文案（记录/撤销/轻刷新后即时更新，不依赖重建）。"""
        if hasattr(self, "greeting_date_label"):
            recs_all = self.data.get("records", [])
            self.greeting_date_label.config(
                text=f"{dt.date.today().strftime('%m月%d日 %A')} · 今天已记录 "
                     f"{len(records_today(self.data))} 次 · 累计 {len(recs_all)} 次")
