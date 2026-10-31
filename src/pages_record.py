# -*- coding: utf-8 -*-
"""pages_record.py —— 记录展示模块（记录组员负责）

职责范围（只准改本文件内的记录页展示）：
- 统计卡（累计次数 / 今日次数 / 本月记录天数）。
- 日历（高亮方式、翻月、日期详情）。
- 本周情绪 / 本周复盘。
- 历史记录列表（可滚动、删除）。
- 统计口径一律调用 data_store 的函数，不自行计算定义。
- 不包含打卡写入逻辑（在 pages_home.py）。

说明：本模块以 RecordMixin 形式提供方法，由 main.py 的 App 类继承组合。
"""

import calendar
import datetime as dt
import tkinter as tk
from collections import Counter

from theme import *                      # 颜色/字体常量
from data_store import (records_today, fmt_emotions, save_data, backup_data)
from ui_dialogs import soft_askyesno, soft_showinfo   # H9：柔和弹窗轮子


class RecordMixin:
    """打卡记录页的页面方法集合。"""

    def _build_record(self):
        """构建记录页：居中容器(place) + Canvas 整页滚动，内容超高必可达（历史记录不再被裁）。"""
        page = self.pages["record"]
        # 居中容器：固定宽居中（首页已验证模式），窄窗动态收窄
        self.rec_center = tk.Frame(page, bg=COL_BG)
        self.rec_center.place(relx=0.5, anchor="n", relheight=1, width=1600)
        # v1.6.2：追踪所有需随窗口宽重排的 wrap 标签（元素=(控件, 左右留白合计)）
        self._wrap_labels = []
        self._rec_cw = 1600
        self._rec_resize_after = None
        page.bind("<Configure>", self._on_record_page_cfg)
        # 整页滚动容器：Canvas + 竖向 Scrollbar + inner（内容直接 pack 到 inner）
        self.rec_canvas = tk.Canvas(self.rec_center, bg=COL_BG, highlightthickness=0)
        self.rec_sb = tk.Scrollbar(self.rec_center, orient="vertical",
                                   command=self.rec_canvas.yview,
                                   width=8, bg=COL_LINE, troughcolor=COL_BG,
                                   activebackground=COL_PRIMARY)
        self.rec_canvas.configure(yscrollcommand=self._on_yscroll)
        self.rec_canvas.pack(side="left", fill="both", expand=True)
        self.rec_sb.pack(side="right", fill="y")
        self.rec_inner = tk.Frame(self.rec_canvas, bg=COL_BG, width=1600)
        self.rec_win = self.rec_canvas.create_window(
            (0, 0), window=self.rec_inner, anchor="nw")
        self.rec_inner.bind("<Configure>", self._on_record_inner_cfg)
        self.rec_canvas.bind("<Configure>", self._on_record_canvas_cfg)

        # 顶部：页标题 + 常驻「查看历史记录」入口（初始视口内必见，点击展开/收起历史区）
        head = tk.Frame(self.rec_inner, bg=COL_BG)
        head.pack(fill="x", padx=12, pady=(16, 6))
        tk.Label(head, text="打卡记录", font=self.f_title, bg=COL_BG,
                 fg=COL_TEXT).pack(side="left")
        # G1：备份数据入口（浅灰小字，紧挨历史按钮左侧）
        self.backup_btn = tk.Button(head, text="备份数据", command=self._backup_data,
                                    font=(FONT_FAMILY, 9), relief="flat", bd=0,
                                    cursor="hand2", bg=COL_BG, fg=COL_SUB,
                                    activebackground=COL_BG,
                                    activeforeground=COL_PRIMARY_DK)
        self.backup_btn.pack(side="right", padx=(0, 10))
        self.hist_btn = tk.Button(head, text="📖 查看历史记录", command=self._toggle_history,
                                  font=(FONT_FAMILY, 10, "bold"), relief="flat", bd=0,
                                  cursor="hand2", bg=COL_BG, fg=COL_PRIMARY,
                                  activebackground=COL_BG,
                                  activeforeground=COL_PRIMARY_DK)
        self.hist_btn.pack(side="right")

        # 顶部三项统计：横向并排三张小圆角卡片
        stats = tk.Frame(self.rec_inner, bg=COL_BG)
        stats.pack(fill="x", padx=12, pady=(0, 10))
        self.stat_labels = {}
        names = [("total", "累计次数"), ("today", "今日次数"), ("month_days", "本月记录")]
        for i, (k, name) in enumerate(names):
            box = rounded_card(stats, bg=COL_CARD)
            box.grid(row=0, column=i, sticky="nsew", padx=6)
            stats.grid_columnconfigure(i, weight=1)
            tk.Label(box, text=name, font=self.f_small, bg=COL_CARD,
                     fg=COL_SUB).pack(pady=(16, 0))
            self.stat_labels[k] = tk.Label(box, text="0", font=self.f_big,
                                           bg=COL_CARD, fg=COL_PRIMARY_DK)
            self.stat_labels[k].pack(pady=(0, 16))

        # 日历卡（圆角 + 极淡描边）
        cal_card = rounded_card(self.rec_inner, bg=COL_CARD)
        cal_card.pack(fill="x", padx=12, pady=4)
        self.cal_year = dt.date.today().year
        self.cal_month = dt.date.today().month
        cal_head = tk.Frame(cal_card, bg=COL_CARD)
        cal_head.pack(fill="x", padx=10, pady=(8, 2))
        # H12：一键回到今天（翻远月后不必再靠切页重置）
        tk.Button(cal_head, text="今天", command=self._cal_today, relief="flat",
                  bg=COL_CARD, fg=COL_PRIMARY, font=(FONT_FAMILY, 10), bd=0,
                  cursor="hand2", activebackground=COL_CARD,
                  activeforeground=COL_PRIMARY_DK).pack(side="left", padx=(0, 4))
        tk.Button(cal_head, text="◀", command=self._cal_prev, relief="flat",
                  bg=COL_CARD, fg=COL_SUB, font=(FONT_FAMILY, 11), bd=0,
                  cursor="hand2").pack(side="left")
        self.cal_title = tk.Label(cal_head, text="", font=self.f_body_b,
                                  bg=COL_CARD, fg=COL_TEXT)
        self.cal_title.pack(side="left", expand=True)
        tk.Button(cal_head, text="▶", command=self._cal_next, relief="flat",
                  bg=COL_CARD, fg=COL_SUB, font=(FONT_FAMILY, 11), bd=0,
                  cursor="hand2").pack(side="right")

        self.cal_grid = tk.Frame(cal_card, bg=COL_CARD)
        self.cal_grid.pack(fill="x", padx=10, pady=(2, 8))
        for i, wd in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
            tk.Label(self.cal_grid, text=wd, font=self.f_small, bg=COL_CARD,
                     fg=COL_SUB, width=5).grid(row=0, column=i, padx=1, pady=2)
        for i in range(7):
            self.cal_grid.grid_columnconfigure(i, weight=1)
        self.cal_cells = {}

        self.day_detail = tk.Label(cal_card, text="", font=self.f_small,
                                   bg=COL_CARD, fg=COL_SUB,
                                   wraplength=self._rec_wrap(44),
                                   anchor="w", justify="left")
        self.day_detail.pack(fill="x", padx=10, pady=(0, 10))
        self._rec_track(self.day_detail, 44)

        # 本周情绪卡片（横条列表，最多 5 种高频情绪）
        week_card = rounded_card(self.rec_inner, bg=COL_CARD)
        week_card.pack(fill="x", padx=12, pady=4)
        tk.Label(week_card, text="本周情绪", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_TEXT).pack(anchor="w", padx=10, pady=(10, 4))
        self.week_emotions_frame = tk.Frame(week_card, bg=COL_CARD)
        self.week_emotions_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 本周复盘卡片（高频情绪 Top3 + 主要场景 + 肯定语）
        review_card = rounded_card(self.rec_inner, bg=COL_CARD)
        review_card.pack(fill="x", padx=12, pady=4)
        tk.Label(review_card, text="本周复盘", font=self.f_body_b, bg=COL_CARD,
                 fg=COL_TEXT).pack(anchor="w", padx=10, pady=(10, 4))
        self.week_review_frame = tk.Frame(review_card, bg=COL_CARD)
        self.week_review_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 历史记录区：默认隐藏（页面不超长），点「查看历史记录」才展开
        self._hist_visible = False
        self.hist_section = tk.Frame(self.rec_inner, bg=COL_BG)
        # 注意：此处不 pack——初始收起，页面只显示统计/日历/周情绪/周复盘
        hist_head = tk.Frame(self.hist_section, bg=COL_BG)
        hist_head.pack(fill="x", pady=(14, 2))
        tk.Label(hist_head, text="📖 历史记录", font=(FONT_FAMILY, 13, "bold"),
                 bg=COL_BG, fg=COL_PRIMARY_DK).pack(side="left")
        tk.Button(hist_head, text="收起", command=self._toggle_history,
                  font=(FONT_FAMILY, 9), relief="flat", bd=0, cursor="hand2",
                  bg=COL_BG, fg=COL_SUB, activebackground=COL_BG,
                  activeforeground=COL_PRIMARY_DK).pack(side="right")
        # H10：删除成功的柔和反馈小字（初始空文本，0 高度）
        self.hist_feedback = tk.Label(self.hist_section, text="", font=self.f_small,
                                      bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w")
        self.hist_feedback.pack(fill="x", pady=(0, 2))
        # 历史记录列表：直接 pack 进页面滚动流（整页滚动，不再嵌套内部滚动）
        self.rec_list = tk.Frame(self.hist_section, bg=COL_BG)
        self.rec_list.pack(fill="x", pady=(0, 12))
        # 滚轮全局化：进入 Canvas 区域即 bind_all，任何子控件（含分帧新建条目）都生效，
        # 离开 Canvas（滚动条/导航栏）自动解除——不依赖逐控件递归绑定
        self.rec_canvas.bind("<Enter>",
                             lambda e: self.rec_canvas.bind_all(
                                 "<MouseWheel>", self._on_record_wheel))
        self.rec_canvas.bind("<Leave>",
                             lambda e: self.rec_canvas.unbind_all("<MouseWheel>"))

    def _on_record_page_cfg(self, ev):
        """页面宽变化：居中容器跟随收窄/放宽（封顶 1920），并防抖原地更新 wrap 文本宽。

        v1.6.2：仅原地 configure wraplength（不重跑 refresh_record / 不重建日历历史），
        避免重置日历浏览月份与历史分页进度；文本按最新 self._rec_cw 重排。
        """
        self.rec_center.place_configure(width=content_width(ev.width))
        if self._rec_resize_after is not None:
            try:
                self.after_cancel(self._rec_resize_after)
            except Exception:
                pass
        self._rec_resize_after = self.after(180, self._refresh_record_after_resize)

    def _refresh_record_after_resize(self):
        """窗口宽变化防抖回调：原地更新全部 wrap 标签 wraplength（不重建），保持滚动位置。"""
        self._rec_resize_after = None
        try:
            if not self.rec_center.winfo_exists():
                return
        except Exception:
            return
        cw = getattr(self, "_rec_cw", 1600)
        yv0 = self.rec_canvas.yview()
        alive = []
        for w, inset in getattr(self, "_wrap_labels", []):
            try:
                if w.winfo_exists():
                    w.config(wraplength=max(1, cw - inset))
                    alive.append((w, inset))
            except Exception:
                pass
        self._wrap_labels = alive
        self.rec_canvas.update_idletasks()
        try:
            self.rec_canvas.yview_moveto(yv0[0])
        except Exception:
            pass

    def _rec_wrap(self, inset):
        """记录页文本可用宽 = 当前内容宽 - 左右留白合计（构建期未测得 _rec_cw 时兜底 1600）。"""
        return max(1, getattr(self, "_rec_cw", 1600) - inset)

    def _rec_track(self, w, inset):
        """登记一个 wrap 标签进 resize 追踪表（重建产生的旧控件由刷新回调自动清理）。"""
        if not hasattr(self, "_wrap_labels"):
            self._wrap_labels = []
        self._wrap_labels.append((w, inset))

    def _on_record_inner_cfg(self, ev):
        """内容尺寸变化时刷新整页滚动区域（0 起）。"""
        self.rec_canvas.configure(scrollregion=(0, 0, ev.width, ev.height))

    def _on_record_canvas_cfg(self, ev):
        """画布尺寸变化：内容宽度跟随画布、左缘 0；维护当前内容宽（供 wrap 文本重排）。"""
        self.rec_canvas.itemconfigure(self.rec_win, width=ev.width)
        self.rec_canvas.coords(self.rec_win, 0, 0)
        self._rec_cw = content_width(ev.width)

    def _on_record_wheel(self, ev):
        """记录页整页滚动支持鼠标滚轮。"""
        self.rec_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")

    def _bind_record_wheel(self, widget):
        """递归给 widget 及其所有子控件绑定滚轮。"""
        try:
            widget.bind("<MouseWheel>", self._on_record_wheel)
        except Exception:
            pass
        for w in widget.winfo_children():
            self._bind_record_wheel(w)

    def _toggle_history(self):
        """展开/收起历史记录区：收起时页面回到总览（短页）；展开时重建最新列表并直达。"""
        if not hasattr(self, "hist_section"):
            return
        if self._hist_visible:
            # 收起：历史区隐藏，页面回到总览，scrollregion 缩小自动回顶部
            self.hist_section.pack_forget()
            self._hist_visible = False
            self.hist_btn.config(text="📖 查看历史记录")
        else:
            # 展开：显示历史区，重建最新列表，滚动到历史区开头
            self._hist_visible = True
            self.hist_section.pack(fill="x", padx=12, pady=(0, 12))
            self.hist_btn.config(text="📁 收起历史记录")
            self._rebuild_history()
            self.after(60, self._scroll_to_history)

    def _scroll_to_history(self):
        """滚动到历史记录区开头（标题行可见）。"""
        try:
            self.rec_canvas.update_idletasks()
            bb = self.rec_canvas.bbox("all")
            if not bb:
                return
            total = bb[3]
            view = self.rec_canvas.winfo_height()
            target = self.hist_section.winfo_y()
            # yview_moveto 的 fraction 对应内容坐标 = frac*total（视口顶部）
            frac = min(max(target / max(total, 1), 0.0), 1.0)
            if total - view > 0:
                self.rec_canvas.yview_moveto(frac)
        except Exception:
            pass

    def _jump_history(self):
        """一键直达历史记录区域（幂等：隐藏则展开，已展开则直达）。"""
        if not getattr(self, "_hist_visible", False):
            self._toggle_history()
        else:
            self._scroll_to_history()

    def _cal_prev(self):
        """日历翻到上个月。"""
        self.cal_month -= 1
        if self.cal_month == 0:
            self.cal_month = 12
            self.cal_year -= 1
        self._draw_calendar()

    def _cal_next(self):
        """日历翻到下个月。"""
        self.cal_month += 1
        if self.cal_month == 13:
            self.cal_month = 1
            self.cal_year += 1
        self._draw_calendar()

    def _cal_today(self):
        """H12：日历一键回到今天（并展示今天详情）。"""
        self.cal_year = dt.date.today().year
        self.cal_month = dt.date.today().month
        self._draw_calendar()
        self._show_day(dt.date.today())

    def _backup_data(self):
        """G1：备份数据文件到用户指定路径（filedialog + data_store.backup_data）。"""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self.rec_canvas, defaultextension=".json",
            initialfile=f"checkin_data_备份_{dt.date.today().strftime('%Y%m%d')}.json",
            filetypes=[("JSON 数据文件", "*.json")])
        if not path:
            return
        ok = backup_data(path)
        if ok:
            soft_showinfo(self.rec_canvas, "备份成功",
                          f"你的打卡数据已备份到：\n{path}\n\n换电脑或误删时，可以随时拿回来。")
        else:
            soft_showinfo(self.rec_canvas, "备份未完成",
                          "备份没有成功。请换个位置再试一次（比如桌面或我的文档）。")

    def _show_delete_feedback(self):
        """H10：删除成功后的柔和反馈小字（2.5s 自动消失）。"""
        if hasattr(self, "hist_feedback"):
            self.hist_feedback.config(text="已删除，过去的就让它过去。")
            if getattr(self, "_fb_after", None) is not None:
                try:
                    self.after_cancel(self._fb_after)
                except Exception:
                    pass
            self._fb_after = self.after(
                2500, lambda: self.hist_feedback.config(text=""))

    def _draw_calendar(self):
        """重画日历：有打卡记录的日期数字下方画浅绿小圆点。"""
        for w in self.cal_grid.winfo_children():
            if int(w.grid_info()["row"]) > 0:
                w.destroy()
        self.cal_cells = {}
        self.cal_title.config(text=f"{self.cal_year} 年 {self.cal_month} 月")
        first = dt.date(self.cal_year, self.cal_month, 1)
        start_col = (first.weekday() + 1) % 7
        days_in_month = calendar.monthrange(self.cal_year, self.cal_month)[1]
        dates = {r.get("date") for r in self.data.get("records", [])}
        today = dt.date.today()
        for day in range(1, days_in_month + 1):
            d = dt.date(self.cal_year, self.cal_month, day)
            row = (start_col + day - 1) // 7 + 1
            col = (start_col + day - 1) % 7
            checked = d.isoformat() in dates
            is_today = (d == today)

            # 单 Label：日期 + 打卡圆点符号（两行），压缩控件树（35 天 → 35 控件）
            dot = "●" if checked else "·"
            fg = COL_PRIMARY_DK if (checked or is_today) else COL_TEXT
            cell = tk.Label(self.cal_grid, text=f"{day}\n{dot}", font=self.f_small,
                            bg=COL_CARD, fg=fg, cursor="hand2",
                            justify="center", anchor="center")
            cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            cell.bind("<Button-1>", lambda ev, dd=d: self._show_day(dd))
            self.cal_cells[d] = cell

    def _show_day(self, d):
        """点击日历日期：显示当天全部记录（按次，含时间与情绪）。"""
        day_recs = [r for r in self.data.get("records", [])
                    if r.get("date") == d.isoformat()]
        if day_recs:
            lines = [f"{d.strftime('%m月%d日')} 共 {len(day_recs)} 次"]
            for r in sorted(day_recs, key=lambda x: x.get("ts", "")):
                tm = r.get("time") or "—"
                ln = f"{tm} · {fmt_emotions(r)}"
                if r.get("action"):
                    ln += f" · {r['action']}"
                lines.append(ln)
            self.day_detail.config(text="\n".join(lines))
        else:
            if d > dt.date.today():
                text = f"{d.strftime('%m月%d日')} 还没到。"
            else:
                text = f"{d.strftime('%m月%d日')} 没有记录。没记录也没关系，下一次难受时来记就行。"
            self.day_detail.config(text=text)

    def _delete_record(self, idx):
        """删除第 idx 条记录（按 self.data["records"] 下标）。"""
        if not (0 <= idx < len(self.data.get("records", []))):
            return
        rec = self.data["records"][idx]
        emos = fmt_emotions(rec)
        msg = f"确认删除这条记录吗？\n\n{emos}\n\n删除后无法恢复，仅删除本条。"
        if not soft_askyesno(self.rec_canvas, "删除记录", msg):
            return
        self.data["records"].pop(idx)
        save_data(self.data)
        self.refresh_record()
        self._show_delete_feedback()

    def refresh_record(self):
        """切到记录页时刷新：统计立即更新；数据未变则跳过重建（秒切），数据变化时分帧重建。"""
        records = self.data.get("records", [])
        fp = (len(records),
              records[0].get("ts") if records else "",
              dt.date.today().isoformat())
        # 统计卡总是更新（轻量 config，不重建控件）
        self.stat_labels["total"].config(text=str(len(records)))
        self.stat_labels["today"].config(text=str(len(records_today(self.data))))
        month_prefix = dt.date.today().strftime("%Y-%m")
        month_days = len({r.get("date") for r in records
                          if r.get("date", "").startswith(month_prefix)})
        self.stat_labels["month_days"].config(text=str(month_days))
        # 数据未变：日历/周卡/历史控件已构建，跳过重建（切页秒开，布局耗时≈0）
        if getattr(self, "_rec_fp", None) == fp:
            return
        self._rec_fp = fp
        # 分帧重建：先日历/周卡/周复盘，再历史列表，避免一次性构建阻塞主循环
        self.after(0, self._rebuild_calendar_week)
        self.after(40, self._rebuild_history)

    def _rebuild_calendar_week(self):
        """日历 + 当天详情 + 本周情绪 + 本周复盘（独立一帧构建）。"""
        records = self.data.get("records", [])
        self.cal_year = dt.date.today().year
        self.cal_month = dt.date.today().month
        self._draw_calendar()
        self._show_day(dt.date.today())

        # ── 本周情绪汇总 ──
        today = dt.date.today()
        monday = today - dt.timedelta(days=today.weekday())
        week_records = [r for r in records
                        if r.get("date", "") >= monday.isoformat()]
        emo_counter = Counter()
        scene_counter = Counter()
        for r in week_records:
            for e in r.get("emotions", []):
                emo_counter[e] += 1
            sc = r.get("scene")
            if sc:
                scene_counter[sc] += 1

        for w in self.week_emotions_frame.winfo_children():
            w.destroy()
        top_emos = emo_counter.most_common(5)
        if not top_emos:
            tk.Label(self.week_emotions_frame, text="这周还没记录，没关系。",
                     font=self.f_small, bg=COL_CARD, fg=COL_SUB).pack(anchor="w", pady=4)
        else:
            max_count = top_emos[0][1]
            for emo, cnt in top_emos:
                row = tk.Frame(self.week_emotions_frame, bg=COL_CARD)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=emo, font=self.f_small, bg=COL_CARD,
                         fg=COL_TEXT, width=8, anchor="w").pack(side="left")
                bar_w = max(20, int((cnt / max_count) * 200))
                bar = tk.Frame(row, bg=COL_PRIMARY, height=12, width=bar_w)
                bar.pack_propagate(False)
                bar.pack(side="left", padx=(4, 8))
                tk.Label(row, text=str(cnt), font=self.f_small, bg=COL_CARD,
                         fg=COL_SUB).pack(side="right")

        # ── 本周复盘 ──
        for w in self.week_review_frame.winfo_children():
            w.destroy()
        if not top_emos:
            lbl = tk.Label(self.week_review_frame,
                           text="这周还没记录，没关系。下一次记录时，这里会慢慢长出你的复盘。",
                           font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                           wraplength=self._rec_wrap(44), anchor="w", justify="left")
            lbl.pack(anchor="w", pady=4)
            self._rec_track(lbl, 44)
        else:
            top3 = "、".join(e for e, _ in top_emos[:3])
            top_scene = scene_counter.most_common(1)[0][0] if scene_counter else "—"
            affirm = {
                "焦虑": "焦虑说明你在乎，允许自己慢慢来，一步一步走。",
                "疲惫": "疲惫是身体在提醒你休息，好好照顾自己。",
                "难过": "难过的时候允许自己哭一会儿，情绪没有对错。",
                "生气": "生气说明你有边界，这份感受值得被看见。",
                "孤独": "孤独不是你的错，你正在学习和自己相处。",
                "压力": "压力之下你还在坚持，这本身就很了不起。",
                "自我否定": "你已经做得很好了，别对自己太苛刻。",
                "委屈": "委屈是真实的，允许自己被理解。",
            }
            top_emo = top_emos[0][0]
            affirm_text = affirm.get(top_emo, "这周的每一次记录，都是你照顾自己的证明。")

            tk.Label(self.week_review_frame, text=f"高频情绪：{top3}",
                     font=self.f_small, bg=COL_CARD, fg=COL_TEXT,
                     anchor="w").pack(fill="x", pady=2)
            tk.Label(self.week_review_frame, text=f"主要场景：{top_scene}",
                     font=self.f_small, bg=COL_CARD, fg=COL_SUB,
                     anchor="w").pack(fill="x", pady=2)
            lbl = tk.Label(self.week_review_frame, text=affirm_text,
                           font=self.f_small, bg=COL_CARD, fg=COL_PRIMARY_DK,
                           anchor="w", wraplength=self._rec_wrap(44), justify="left")
            lbl.pack(fill="x", pady=(4, 0))
            self._rec_track(lbl, 44)

    def _rebuild_history(self):
        """历史记录列表重建（分页渲染：先 40 条，滚到底自动加载更多，控件树封顶防卡顿）。
        历史区隐藏时不重建（列表留到展开时刷新），省布局成本。"""
        if not getattr(self, "_hist_visible", False):
            return
        for w in self.rec_list.winfo_children():
            w.destroy()
        # 保留原始下标，便于删除
        records = self.data.get("records", [])
        self._hist_all = sorted(enumerate(records),
                                key=lambda pair: pair[1].get("ts", ""), reverse=True)
        self._hist_shown = 0
        self._hist_last_day = None
        self._hist_gen_running = False
        if not self._hist_all:
            tk.Label(self.rec_list, text="还没有记录。学习时感到难受，就来这里把它说出来。",
                     font=self.f_small, bg=COL_BG, fg=COL_SUB).pack(anchor="w")
            return
        self._hist_render_to(min(self._HIST_PAGE, len(self._hist_all)))

    # ── 历史记录分页渲染 ──
    _HIST_PAGE = 40       # 触底前先渲染的条数
    _HIST_BATCH = 15      # 每帧渲染条数（UI 不冻结）

    def _hist_render_to(self, target_idx, then=None):
        """从 _hist_shown 分帧渲染到 target_idx（每帧 _HIST_BATCH 条，after 间隔，UI 不冻结）。
        then：渲染全部完成后回调（用于直达后跳底）。"""
        if self._hist_gen_running:
            if then:
                self.after(60, then)
            return
        self._hist_gen_running = True

        def step():
            end = min(self._hist_shown + self._HIST_BATCH,
                      target_idx, len(self._hist_all))
            if end > self._hist_shown:
                self._hist_render_range(self._hist_shown, end)
                self._hist_shown = end
            if self._hist_shown < target_idx and self._hist_shown < len(self._hist_all):
                self.after(20, step)
            else:
                self._hist_gen_running = False
                if then:
                    self.after(20, then)
        step()

    def _hist_render_range(self, a, b):
        """渲染 all[a:b]（含按天分组，跨批保留 last_day）。"""
        for orig_idx, r in self._hist_all[a:b]:
            d_obj = dt.date.fromisoformat(r["date"])
            tm = r.get("time") or ""

            # 每天大日期只显示一次（当天第一条前）
            if r["date"] != self._hist_last_day:
                tk.Label(self.rec_list, text=f"{d_obj.month}月{d_obj.day}日",
                         font=(FONT_FAMILY, 12, "bold"), bg=COL_BG,
                         fg=COL_PRIMARY_DK, anchor="center"
                         ).pack(fill="x", pady=(10, 2))
                self._hist_last_day = r["date"]

            # 单条记录条目：浅底色 + 内容（时间+情绪+场景+强度）+ 删除按钮
            entry = tk.Frame(self.rec_list, bg=COL_CHIP)
            entry.pack(fill="x", pady=3)

            # 情绪 + 备注 + 场景 + 强度
            detail = fmt_emotions(r)
            if r.get("action"):
                detail += f" · {r['action']}"
            scene = r.get("scene") or "—"
            intensity = r.get("intensity")
            inten_str = f"强度{intensity}" if intensity else "—"
            detail += f" · {scene} · {inten_str}"
            line = f"{tm if tm else '—'}  {detail}"
            lbl = tk.Label(entry, text=line, font=self.f_small, bg=COL_CHIP,
                           fg=COL_TEXT, anchor="w", wraplength=self._rec_wrap(116))
            lbl.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=8)
            self._rec_track(lbl, 116)

            # 删除按钮：柔和浅灰文字，hover 变红
            del_btn = tk.Label(entry, text="删除", font=self.f_small,
                               bg=COL_CHIP, fg=COL_SUB, cursor="hand2",
                               padx=6, pady=8)
            del_btn.pack(side="right", padx=(0, 6))
            del_btn.bind("<Enter>", lambda e, b=del_btn: b.config(fg="#D96666"))
            del_btn.bind("<Leave>", lambda e, b=del_btn: b.config(fg=COL_SUB))
            del_btn.bind("<Button-1>", lambda e, idx=orig_idx: self._delete_record(idx))

    def _on_yscroll(self, *args):
        """滚动命令：更新滚动条 + 滚近底部排队加载更多（渲染不占用当前事件循环）。"""
        self.rec_sb.set(*args)
        try:
            _top, bottom = self.rec_canvas.yview()
            if (bottom > 0.93
                    and getattr(self, "_hist_shown", 0) < len(getattr(self, "_hist_all", []))
                    and not getattr(self, "_hist_gen_running", False)):
                self.after(50, lambda: self._hist_render_to(
                    min(self._hist_shown + self._HIST_PAGE, len(self._hist_all))))
        except Exception:
            pass
