# -*- coding: utf-8 -*-
"""pages_manual.py —— 手册页模块（ManualMixin）

职责范围（只准改本文件内的手册页渲染逻辑）：
- 成长 Tab（manual 页）：今日一课 / 课程目录 / 情绪词库 三视图渲染。
- 今日一课按最近情绪推荐（EMOTION_LESSON_MAP）或随机轮换；目录分组折叠；
  词库搜索/展开/增词；详情上一篇/下一篇；滚动容器与滚轮全局化。
- 数据来源：chapters_data.py（手册内容+词库）、data_store.all_emotions（全部可选词）。

拆分说明（v1.6.10 耦合解耦）：本模块自 main.py 迁移而来，方法逻辑零改动，
仅位置变化。与 HomeMixin/RecordMixin/ToolMixin 的页面 Mixin 模式对齐，
main.py 只保留组装与启动。

⚠ MRO 顺序约束：本 Mixin 在 App 类定义中必须排在 HomeMixin 之前——
_add_custom_emotion 通过 super()._add_custom_emotion 调用 HomeMixin 实现
（写入 custom_emotions + save_data + 首页标签重建），成功后本 Mixin 再
重建手册词库区（协作链依赖此顺序，颠倒则词库区不刷新）。
"""

import tkinter as tk

from theme import *                      # 颜色/字体常量（含 content_width / rounded_card）
from chapters_data import EMOTION_GLOSSARY, GROUP_ORDER   # 内置词解释 + 分组顺序
from data_store import all_emotions      # 全部可选情绪词（内置 + 自定义）


# 情绪 → 章节索引推荐映射（H8：56 个内置情绪词全覆盖；无匹配保持当天轮换）
# 索引按 CHAPTERS 0 基（见 chapters_data.py：2=考试焦虑 5=厌学倦怠 8=社交焦虑
# 12=孤独 16=委屈 19=嫉妒 25=低自尊 26=冒名顶替 28=羞耻 29=内疚 31=反刍
# 35=麻木 37=想哭 38=愤怒 39=烦躁 40=无聊 43=惊恐 45=熬夜 46=进食 47=信息过载
# 48=消费 49=情绪劳动 50=戒断 51=三分钟热度 52=躯体化 53=深夜emo 54=倦怠
# 58=迷茫 59=FOMO 61=决策焦虑 63=哀伤 64=低谷重建 66=感恩 67=心流）
EMOTION_LESSON_MAP = {
    "焦虑": 2, "紧张": 2, "心慌": 43, "烦躁": 39,
    "拖延": 0, "疲惫": 54, "无聊": 40, "走神": 1,
    "自责": 29, "迷茫": 58, "害怕": 43, "委屈": 16,
    "没劲": 54, "想放弃": 64, "平静": 67, "期待": 67,
    "麻木": 35, "憋屈": 38, "内疚": 29, "羞耻": 28,
    "嫉妒": 19, "孤独": 12, "沮丧": 64, "无助": 64,
    "不安": 43, "空落落": 12, "自我怀疑": 26, "反刍": 31,
    "冒名顶替感": 26, "习得性无助": 64, "完美主义瘫痪": 4, "坐立不安": 39,
    "高敏感": 27, "患得患失": 13, "戒断感": 50, "想哭": 37,
    "愤怒": 38, "怀旧": 41, "敬畏": 42, "惊恐": 43,
    "易被带跑": 44, "舍不得睡": 45, "情绪性嘴馋": 46, "信息过载": 47,
    "冲动消费": 48, "假笑": 49, "躯体不适": 52, "深夜emo": 53,
    "倦怠": 54, "虚无感": 58, "错失感": 59, "选择困难": 61,
    "哀伤": 63, "感恩": 66, "三分钟热度": 51, "怕添麻烦": 23,
}


class ManualMixin:
    """手册页（成长 Tab）：今日一课 / 课程目录 / 情绪词库。"""

    # ---------- 今日一课：按今日情绪推荐 ----------
    def _lesson_reco_index(self):
        """按最近一次打卡情绪推荐章节索引；无记录/无匹配返回 None（保持当天轮换）。"""
        recs = self.data.get("records", [])
        if not recs:
            return None
        for emo in recs[-1].get("emotions", []):
            if emo in EMOTION_LESSON_MAP:
                return EMOTION_LESSON_MAP[emo]
        return None

    # ==================== 页面：完整手册（每章卡片） ====================
    def _build_manual(self):
        """构建手册页：固定 Tab 栏（画布外，H6 不随内容滚动）+ 可滚动内容区。"""
        from chapters_data import CHAPTERS

        page = self.pages["manual"]
        # 居中容器(place) + 固定 Tab 栏 + Canvas 滚动（内容宽跟随居中容器、封顶随 theme）
        self.manual_center = tk.Frame(page, bg=COL_BG)
        self.manual_center.place(relx=0.5, anchor="n", relheight=1, width=1600)
        page.bind("<Configure>", self._on_manual_page_cfg)

        # 顶部 Tab 栏（固定在画布上方，不随内容滚动；仿底部导航选中态）
        tabbar = tk.Frame(self.manual_center, bg=COL_BG)
        tabbar.pack(fill="x", padx=12, pady=(10, 2))
        self._manual_tab_btns = {}
        self._manual_tab_inds = {}
        for key, text in [("today", "今日一课"), ("catalog", "课程目录"),
                          ("glossary", "情绪词库")]:
            col = tk.Frame(tabbar, bg=COL_BG)
            col.pack(side="left", padx=(0, 22))
            b = tk.Button(col, text=text, font=(FONT_FAMILY, 11, "bold"),
                          relief="flat", bd=0, bg=COL_BG, fg=COL_TAB_OFF,
                          activebackground=COL_BG, activeforeground=COL_TAB_ON,
                          command=lambda k=key: self._show_manual_tab(k),
                          cursor="hand2")
            b.pack(anchor="w")
            ind = tk.Frame(col, bg=COL_BG, height=2)   # 选中态 2px 下划线
            ind.pack(fill="x", pady=(4, 0))
            self._manual_tab_btns[key] = b
            self._manual_tab_inds[key] = ind

        # 滚动容器（Tab 栏下方）
        self.manual_canvas = tk.Canvas(self.manual_center, bg=COL_BG,
                                       highlightthickness=0)
        self.manual_sb = tk.Scrollbar(self.manual_center, orient="vertical",
                                      command=self.manual_canvas.yview)
        self.manual_canvas.configure(yscrollcommand=self.manual_sb.set)
        self.manual_canvas.pack(side="left", fill="both", expand=True)
        self.manual_sb.pack(side="right", fill="y")
        self.manual_inner = tk.Frame(self.manual_canvas, bg=COL_BG, width=1600)
        self.manual_win = self.manual_canvas.create_window(
            (0, 0), window=self.manual_inner, anchor="nw")
        self.manual_inner.bind("<Configure>", self._on_manual_inner_cfg)
        self.manual_canvas.bind("<Configure>", self._on_manual_canvas_cfg)

        # 当前内容宽（动态，随画布宽度变化；_on_manual_canvas_cfg 维护）
        self._manual_cw = content_width(1600)

        # Tab 内容容器（所有 Tab 内容渲染进它，切换时重建）
        self._manual_content = tk.Frame(self.manual_inner, bg=COL_BG)

        # 滚轮全局化（核心约束八）：进入手册页区域才 bind_all，离开 unbind_all；
        # 禁止构建期一次性递归绑定。
        self.manual_center.bind("<Enter>", lambda e: self.manual_center.bind_all(
            "<MouseWheel>", self._on_manual_wheel))
        self.manual_center.bind("<Leave>", lambda e: self.manual_center.unbind_all(
            "<MouseWheel>"))

        # 默认显示今日一课
        self._show_manual_tab("today")

    def _show_manual_tab(self, tab):
        """切换手册页 Tab：更新选中态、重建内容容器并分派渲染、回顶。"""
        self._manual_tab = tab
        # 更新 Tab 按钮选中态
        for key, b in self._manual_tab_btns.items():
            on = (key == tab)
            b.config(fg=COL_TAB_ON if on else COL_TAB_OFF)
            self._manual_tab_inds[key].config(bg=COL_TAB_ON if on else COL_BG)
        # 重建内容容器
        if getattr(self, "_manual_content", None) is not None:
            self._manual_content.destroy()
        self._manual_content = tk.Frame(self.manual_inner, bg=COL_BG)
        self._manual_content.pack(fill="x", padx=12, pady=(0, 8))
        # 分派渲染（catalog/glossary 由 ⑧-B/⑧-C 实现）
        if tab == "today":
            self._build_today_card()
        elif tab == "catalog":
            self._build_catalog()
        elif tab == "glossary":
            self._build_glossary()
        # 重建后回顶（scrollregion 由 inner <Configure> 自动刷新）
        self.manual_canvas.yview_moveto(0)

    def _build_today_card(self):
        """今日一课大卡：按情绪推荐；无推荐则随机一课。"""
        from chapters_data import CHAPTERS
        idx = self._lesson_reco_index()
        if idx is not None:
            ch = CHAPTERS[idx]
        else:
            ch = self._pick_random_lesson()
        self._today_ch = ch
        self._render_today_card(ch)

    def _pick_random_lesson(self, exclude=None):
        """随机选一课；exclude 为需排除的当前课（换一课时使用）。"""
        from chapters_data import CHAPTERS
        import random
        cand = [c for c in CHAPTERS if c is not exclude]
        return random.choice(cand)

    def _render_today_card(self, ch):
        """渲染今日一课大卡：组标签 + 课名 + essence + 今日一招高亮块 + 按钮行。"""
        cw = self._manual_cw
        # v1.6.3 收窄：_manual_content padx12*2 + inner padx12*2 = 48，控件宽=cw-48
        wrap = max(0, cw - 48)              # 动态换行宽度，禁止写死
        tip_wrap = max(0, wrap - 24)        # 高亮块内再缩 24（左右各 12 留白）
        card = rounded_card(self._manual_content)
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=COL_CARD)
        inner.pack(fill="x", padx=12, pady=(16, 16))

        # a. 组标签
        tk.Label(inner, text=f"今日推荐 · {ch['group']}",
                 font=self.f_small, bg=COL_CARD, fg=COL_PRIMARY_DK
                 ).pack(anchor="w")
        # b. 课名（大字）
        tk.Label(inner, text=ch["name"], font=self.f_big, bg=COL_CARD, fg=COL_TEXT,
                 anchor="w", justify="left", wraplength=wrap
                 ).pack(fill="x", pady=(6, 4))
        # c. essence（两行内）
        tk.Label(inner, text=ch["essence"], font=self.f_body, bg=COL_CARD,
                 fg=COL_TEXT, anchor="w", justify="left", wraplength=wrap
                 ).pack(fill="x", pady=(0, 12))
        # d. 今日一招高亮块
        tipbox = tk.Frame(inner, bg=COL_TIP_BLOCK)
        tipbox.pack(fill="x", pady=(0, 12))
        tk.Label(tipbox, text=ch["tip_title"], font=self.f_body_b,
                 bg=COL_TIP_BLOCK, fg=COL_PRIMARY_DK, anchor="w", justify="left",
                 wraplength=tip_wrap).pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(tipbox, text=ch["tip"], font=self.f_body, bg=COL_TIP_BLOCK,
                 fg=COL_TEXT, anchor="w", justify="left", wraplength=tip_wrap
                 ).pack(fill="x", padx=12, pady=(0, 10))
        # e. 按钮行：读全文（⑧-B 实现 _open_detail）/ 换一课
        btns = tk.Frame(inner, bg=COL_CARD)
        btns.pack(anchor="w", pady=(4, 0))
        tk.Button(btns, text="读全文", font=self.f_small,
                  bg=COL_SOFT, fg=COL_PRIMARY_DK, relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2",
                  activebackground=COL_HOVER, activeforeground=COL_PRIMARY_DK,
                  command=lambda c=ch: self._open_detail(c)
                  ).pack(side="left", padx=(0, 10))
        tk.Button(btns, text="换一课", font=self.f_small,
                  bg=COL_BG, fg=COL_SUB, relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2",
                  activebackground=COL_BG, activeforeground=COL_PRIMARY_DK,
                  command=self._swap_today_lesson).pack(side="left")

    def _swap_today_lesson(self):
        """换一课：随机选 ≠ 当前课，重建今日卡内容。"""
        ch = self._pick_random_lesson(exclude=self._today_ch)
        self._today_ch = ch
        # 重建内容容器并渲染（保持 today tab）
        if getattr(self, "_manual_content", None) is not None:
            self._manual_content.destroy()
        self._manual_content = tk.Frame(self.manual_inner, bg=COL_BG)
        self._manual_content.pack(fill="x", padx=12, pady=(0, 8))
        self._render_today_card(ch)

    def _build_catalog(self):
        """课程目录：按 GROUP_ORDER 分组渲染，可折叠分组头，点击课行进入详情。

        v1.6.2 波2：cw>1600 时展开组内课行改双列 grid 布局（列宽按 (cw-24-gap)//2）；
        cw≤1600 保持单列行为不变。分组头始终通栏。
        """
        from chapters_data import CHAPTERS
        # 折叠状态持久化：默认第一组（学习）展开，其余收起
        if not hasattr(self, "_catalog_collapsed"):
            self._catalog_collapsed = set()
            for g in GROUP_ORDER[1:]:
                self._catalog_collapsed.add(g)
        for w in self._manual_content.winfo_children():
            w.destroy()
        cw = self._manual_cw
        # v1.6.3 收窄：_manual_content padx12*2 + row padx12*2 = 48，控件宽=cw-48
        wrap = max(0, cw - 48)
        # 大屏多列判定（v1.6.2）
        wide = cw > 1600
        gap = 12
        if wide:
            col_w = max(180, (cw - 24 - gap) // 2)
            cell_wrap = max(100, col_w - 8)
        for gname in GROUP_ORDER:
            chs = [c for c in CHAPTERS if c.get("group") == gname]
            collapsed = gname in self._catalog_collapsed
            mark = "▼" if not collapsed else "▲"
            head = tk.Label(self._manual_content,
                            text=f"{gname}（{len(chs)} 课）  {mark}",
                            font=self.f_body_b, bg=COL_GROUP_HEAD, fg=COL_TEXT,
                            anchor="w", padx=12, pady=6, cursor="hand2")
            head.pack(fill="x", pady=(8, 0))
            head.bind("<Button-1>", lambda e, g=gname: self._toggle_catalog_group(g))
            if collapsed:
                continue
            if not wide:
                # 单列（原逻辑，cw≤1600 保持不变）
                for ch in chs:
                    row = tk.Frame(self._manual_content, bg=COL_BG)
                    row.pack(fill="x", padx=12, pady=(2, 0))
                    name_l = tk.Label(row, text=ch["name"], font=self.f_body_b,
                                      bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w",
                                      cursor="hand2", justify="left", wraplength=wrap)
                    name_l.pack(fill="x")
                    intro_l = tk.Label(row, text=ch.get("intro", ""), font=self.f_small,
                                       bg=COL_BG, fg=COL_SUB, anchor="w",
                                       cursor="hand2", justify="left", wraplength=wrap)
                    intro_l.pack(fill="x", pady=(0, 4))
                    for w in (row, name_l, intro_l):
                        w.bind("<Button-1>", lambda e, c=ch: self._open_detail(c))
            else:
                # 双列 grid（cw>1600）：每格 = 课名 + intro，点击进详情
                grid = tk.Frame(self._manual_content, bg=COL_BG)
                grid.pack(fill="x", pady=(2, 0))
                grid.grid_columnconfigure(0, weight=1, uniform="catcol")
                grid.grid_columnconfigure(1, weight=1, uniform="catcol")
                for idx, ch in enumerate(chs):
                    col = idx % 2
                    row = idx // 2
                    cell = tk.Frame(grid, bg=COL_BG)
                    cell.grid(row=row, column=col, sticky="nsew",
                              padx=(0, gap if col == 0 else 0), pady=(0, 4))
                    name_l = tk.Label(cell, text=ch["name"], font=self.f_body_b,
                                      bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w",
                                      cursor="hand2", justify="left", wraplength=cell_wrap)
                    name_l.pack(fill="x")
                    intro_l = tk.Label(cell, text=ch.get("intro", ""), font=self.f_small,
                                       bg=COL_BG, fg=COL_SUB, anchor="w",
                                       cursor="hand2", justify="left", wraplength=cell_wrap)
                    intro_l.pack(fill="x", pady=(0, 4))
                    for w in (cell, name_l, intro_l):
                        w.bind("<Button-1>", lambda e, c=ch: self._open_detail(c))
        self.manual_canvas.configure(scrollregion=self.manual_canvas.bbox("all"))

    def _toggle_catalog_group(self, gname):
        """切换分组折叠状态并重建目录。"""
        if gname in self._catalog_collapsed:
            self._catalog_collapsed.discard(gname)
        else:
            self._catalog_collapsed.add(gname)
        self._build_catalog()

    def _open_detail(self, ch):
        """打开一课详情卡：只渲染当前这一课，禁止预建 70 课 full 控件。"""
        self._manual_prev_tab = self._manual_tab
        for w in self._manual_content.winfo_children():
            w.destroy()
        wrap = max(0, self._manual_cw - 48)
        # a. 课名大标题
        tk.Label(self._manual_content, text=ch["name"], font=self.f_title,
                 bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w", justify="left",
                 wraplength=wrap).pack(fill="x", padx=12, pady=(12, 8))
        # b. full 分段（h2/bullet/body）
        for kind, text in ch.get("full", []):
            if kind == "h2":
                tk.Label(self._manual_content, text=text, font=(FONT_FAMILY, 12, "bold"),
                         bg=COL_BG, fg=COL_PRIMARY, anchor="w", justify="left",
                         wraplength=wrap).pack(fill="x", padx=12, pady=(8, 4))
            elif kind == "bullet":
                tk.Label(self._manual_content, text="· " + text, font=self.f_body,
                         bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w", justify="left",
                         wraplength=wrap).pack(fill="x", padx=12, pady=(0, 4))
            else:
                tk.Label(self._manual_content, text=text, font=self.f_body,
                         bg=COL_BG, fg=COL_TEXT, anchor="w", justify="left",
                         wraplength=wrap).pack(fill="x", padx=12, pady=(0, 4))
        # c. 今日一招高亮块
        tip_title = ch.get("tip_title", "")
        tip = ch.get("tip", "")
        if tip_title or tip:
            tip_frame = tk.Frame(self._manual_content, bg=COL_TIP_BLOCK)
            tip_frame.pack(fill="x", padx=12, pady=(10, 6))
            if tip_title:
                tk.Label(tip_frame, text=tip_title, font=self.f_body_b,
                         bg=COL_TIP_BLOCK, fg=COL_PRIMARY_DK, anchor="w",
                         justify="left", wraplength=max(0, wrap - 24)
                         ).pack(fill="x", padx=12, pady=(8, 2))
            if tip:
                tk.Label(tip_frame, text=tip, font=self.f_body,
                         bg=COL_TIP_BLOCK, fg=COL_TEXT, anchor="w",
                         justify="left", wraplength=max(0, wrap - 24)
                         ).pack(fill="x", padx=12, pady=(0, 8))
        # d. warm 加粗
        warm = ch.get("warm", "")
        if warm:
            tk.Label(self._manual_content, text=warm, font=self.f_body_b,
                     bg=COL_BG, fg=COL_PRIMARY_DK, anchor="w", justify="left",
                     wraplength=wrap).pack(fill="x", padx=12, pady=(8, 4))
        # e2. 上一篇/下一篇（H7：按 CHAPTERS 全局顺序翻页，不必回目录再点）
        from chapters_data import CHAPTERS
        nav = tk.Frame(self._manual_content, bg=COL_BG)
        nav.pack(fill="x", padx=12, pady=(10, 0))
        try:
            idx = CHAPTERS.index(ch)
        except (ValueError, IndexError):
            idx = -1
        if idx > 0:
            tk.Button(nav, text="← 上一篇", font=self.f_small,
                      bg=COL_BG, fg=COL_SUB, relief="flat", bd=0,
                      padx=12, pady=4, cursor="hand2",
                      activebackground=COL_BG, activeforeground=COL_PRIMARY_DK,
                      command=lambda i=idx - 1: self._open_detail(CHAPTERS[i])
                      ).pack(side="left")
        if 0 <= idx < len(CHAPTERS) - 1:
            tk.Button(nav, text="下一篇 →", font=self.f_small,
                      bg=COL_BG, fg=COL_SUB, relief="flat", bd=0,
                      padx=12, pady=4, cursor="hand2",
                      activebackground=COL_BG, activeforeground=COL_PRIMARY_DK,
                      command=lambda i=idx + 1: self._open_detail(CHAPTERS[i])
                      ).pack(side="right")
        # e. 返回按钮
        tk.Button(self._manual_content, text="← 返回", font=self.f_small,
                  bg=COL_SOFT, fg=COL_PRIMARY_DK, relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  activebackground=COL_HOVER, activeforeground=COL_PRIMARY_DK,
                  command=lambda: self._show_manual_tab(self._manual_prev_tab)
                  ).pack(anchor="w", padx=12, pady=(8, 16))
        self.manual_canvas.configure(scrollregion=self.manual_canvas.bbox("all"))
        self.manual_canvas.yview_moveto(0)

    def _build_glossary(self):
        """词库 Tab 内容：搜索框 + 添加按钮 + 折叠词条区（渲染进 self._manual_content）。"""
        container = self._manual_content
        if not hasattr(self, "_glossary_var"):
            self._glossary_var = tk.StringVar(value="")
            self._glossary_var.trace_add(
                "write", lambda *a: self._rebuild_glossary())
        if not hasattr(self, "_glossary_expanded"):
            self._glossary_expanded = set()

        # 顶部栏：搜索框 + 添加按钮
        top = tk.Frame(container, bg=COL_BG)
        top.pack(fill="x", padx=12, pady=(12, 8))
        tk.Label(top, text="搜索", font=self.f_small,
                 bg=COL_BG, fg=COL_SUB).pack(side="left", padx=(0, 6))
        tk.Entry(top, textvariable=self._glossary_var, font=self.f_body,
                 relief="solid", bd=1, bg=COL_CARD, fg=COL_TEXT
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(top, text="＋ 添加情绪词", font=self.f_small,
                  bg=COL_SOFT, fg=COL_PRIMARY_DK, relief="flat", bd=0,
                  padx=10, pady=4, cursor="hand2",
                  activebackground=COL_HOVER, activeforeground=COL_PRIMARY_DK,
                  command=self._open_add_emotion_dialog
                  ).pack(side="right", padx=(8, 0))

        # 词条容器（_rebuild_glossary 填充）
        self._glossary_inner = tk.Frame(container, bg=COL_BG)
        self._glossary_inner.pack(fill="x", padx=12, pady=(0, 12))
        self._rebuild_glossary()

    def _toggle_glossary_word(self, word):
        """切换词条展开/收起状态，然后重建词条区。"""
        if word in self._glossary_expanded:
            self._glossary_expanded.discard(word)
        else:
            self._glossary_expanded.add(word)
        self._rebuild_glossary()

    def _rebuild_glossary(self):
        """重建词条区：折叠模式（默认只显词名，点击展开解释）+ 搜索过滤 + 保持展开态。"""
        if not getattr(self, "_glossary_inner", None):
            return
        for w in self._glossary_inner.winfo_children():
            w.destroy()

        kw = ""
        if hasattr(self, "_glossary_var"):
            kw = self._glossary_var.get().strip()
        fallback = "这个词是后来加入的，等你来定义它"
        custom = {e["word"]: (e.get("gloss") or "")
                  for e in self.data.get("custom_emotions", [])
                  if isinstance(e, dict) and e.get("word")}

        words = all_emotions(self.data)
        if kw:
            words = [w for w in words if kw in w]

        # 动态列宽：根据 self._manual_cw 计算列数（v1.6.2 波2：>1600 时三列）
        cw = getattr(self, "_manual_cw", 800) or 800
        gap = 12
        ncols = 3 if cw > 1600 else 2
        col_w = max(180, (cw - 48 - gap * (ncols - 1)) // ncols)   # _manual_content padx12*2 + _glossary_inner padx12*2 + 列间距
        gloss_w = max(100, col_w - 24)           # 卡内 padx12*2

        for idx, word in enumerate(words):
            col = idx % ncols
            row = idx // ncols
            self._glossary_inner.grid_columnconfigure(
                col, weight=1, uniform="gcol")
            gloss = EMOTION_GLOSSARY.get(word) or custom.get(word) or fallback
            expanded = word in self._glossary_expanded

            card = tk.Frame(self._glossary_inner, bg=COL_CARD)
            card.grid(row=row, column=col, sticky="nsew",
                      padx=(0, gap if col < ncols - 1 else 0), pady=(0, 8))
            # 词名行（点击 toggle）
            name_lbl = tk.Label(card, text=word, font=self.f_body_b,
                                bg=COL_CARD, fg=COL_PRIMARY_DK, anchor="w",
                                cursor="hand2")
            name_lbl.pack(fill="x", padx=12, pady=(8, 0 if expanded else 8))
            # 展开时显示解释
            if expanded:
                tk.Label(card, text=gloss, font=self.f_small,
                         bg=COL_CARD, fg=COL_SUB, anchor="w", justify="left",
                         wraplength=gloss_w).pack(fill="x", padx=12, pady=(0, 8))
            # 绑定点击事件到卡片及词名
            for widget in (card, name_lbl):
                widget.bind(
                    "<Button-1>",
                    lambda e, w=word: self._toggle_glossary_word(w))

        # 词条区高度变化后刷新滚动区域
        if hasattr(self, "manual_canvas") and self.manual_canvas.winfo_exists():
            self.manual_canvas.configure(
                scrollregion=self.manual_canvas.bbox("all"))

    def _add_custom_emotion(self, word, gloss=""):
        """扩展打卡页实现：保存成功后同步重建手册词库区（首页标签重建由父类负责）。

        ⚠ MRO 顺序约束：本 Mixin 在 App 类中排在 HomeMixin 之前，
        super()._add_custom_emotion 解析到 HomeMixin 实现（写入+save_data+首页重建）。
        """
        ok = super()._add_custom_emotion(word, gloss)
        if ok:
            self._rebuild_glossary()
        return ok

    def _on_manual_page_cfg(self, ev):
        """页面宽变化：居中容器跟随收窄/放宽（封顶 1600），并防抖重建当前 Tab。

        v1.6.1 修复：此前仅容器收窄，已渲染文本仍按旧宽换行 → 窗口非 1600 时
        长文本横向溢出被遮挡。窗口宽变化后延迟 180ms 重建当前 Tab，所有文本
        按最新 _manual_cw 重排（目录/词库/详情折叠态保留）。
        """
        self.manual_center.place_configure(width=content_width(ev.width))
        if getattr(self, "_manual_resize_after", None) is not None:
            try:
                self.after_cancel(self._manual_resize_after)
            except Exception:
                pass
        self._manual_resize_after = self.after(
            180, self._refresh_manual_after_resize)

    def _refresh_manual_after_resize(self):
        """窗口宽变化防抖回调：重建当前 Tab（用最新 _manual_cw），并保持滚动位置。"""
        if not (getattr(self, "_manual_tab", None)
                and getattr(self, "manual_center", None)
                and self.manual_center.winfo_exists()):
            return
        yv0 = self.manual_canvas.yview()
        self._show_manual_tab(self._manual_tab)
        self.manual_canvas.update_idletasks()
        self.manual_canvas.yview_moveto(yv0[0])

    def _on_manual_inner_cfg(self, ev):
        """内容尺寸变化时刷新滚动区域（0 起，避免 bbox 起点偏移导致内容贴右）。"""
        self.manual_canvas.configure(scrollregion=(0, 0, ev.width, ev.height))

    def _on_manual_canvas_cfg(self, ev):
        """画布（=居中容器）尺寸变化时：内容宽度跟随画布、左缘 0；维护当前内容宽。"""
        self.manual_canvas.itemconfigure(self.manual_win, width=ev.width)
        self.manual_canvas.coords(self.manual_win, 0, 0)
        self._manual_cw = content_width(ev.width)

    def _on_manual_wheel(self, ev):
        """手册页滚轮滚动（全局 bind_all；守卫：切页后隐藏容器不响应残留触发）。"""
        if not self.manual_center.winfo_viewable():
            return
        self.manual_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")
