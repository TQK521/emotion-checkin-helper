# -*- coding: utf-8 -*-
"""theme.py —— 界面视觉模块（视觉组员负责）

职责范围（只准改本文件内的视觉常量与组件样式）：
- 颜色常量、字体常量：全项目所有页面共用。
- 圆角卡片组件 rounded_card：全项目复用的视觉容器。
- 不包含任何业务逻辑与数据逻辑。

使用约定：
- 其他模块用 `from theme import *` 引入全部常量与组件。
- 改颜色常量属于"共享接口改动"，改前必须向总调度声明影响面。

【任务卡 ② 验收后状态】视觉令牌已切换为护眼主题 v1：
柔和米白底 / 白卡 / 低饱和浅薄荷绿 / 深灰正文 / 浅灰小字 /
16px 圆角卡片 / 极淡描边替代投影 / 弱化分割线。
本卡为唯一改动者，其他组员等本卡验收后再动相关常量。
"""

import tkinter as tk

# ---------------- 配色（护眼主题 v1） ----------------
COL_BG         = "#FAFAF8"   # 页面底色：柔和米白
COL_CARD       = "#FFFFFF"   # 卡片白（不变）
COL_PRIMARY    = "#88C9B0"   # 主色：低饱和浅薄荷绿
COL_PRIMARY_DK = "#5DA386"   # 加深薄荷绿（用于文字强调）
COL_ACCENT     = "#D9A38A"   # 强调：降饱和暖色
COL_TEXT       = "#444444"   # 正文（深灰）
COL_SUB        = "#777777"   # 次要文字（浅灰）
COL_LINE       = "#EDEDEA"   # 卡片描边（更淡，弱化分割线）
COL_CHIP       = "#F2F1EC"   # 极浅灰标签底
COL_SOFT       = "#E8F3EE"   # 极浅薄荷绿提示底

# ---------------- 新增令牌（设计令牌） ----------------
COL_HOVER        = "#D8EFE4"   # 标签 hover 柔和薄荷绿
COL_INPUT_BG     = "#F5F5F2"   # 输入框浅灰底
CARD_RADIUS      = 16          # 圆角半径（像素）
CARD_SHADOW_LINE = "#F0EFEC"   # 卡片极淡描边（替代投影近似）
SPACING_CARD     = 16          # 卡片内间距基准
SPACING_BLOCK    = 20          # 卡片外/区块间距基准

# ---------------- 手册图书馆模式 v1.6.0 波1：新增视觉令牌 ----------------
COL_TAB_ON      = "#4F9274"   # 手册页 Tab 选中文字色（加深薄荷绿，与 COL_PRIMARY_DK 同系，选中态清晰）
COL_TAB_OFF     = "#8C8C8C"   # Tab 未选中文字色（浅灰，与 COL_SUB 同系，弱化未选中态）
COL_GROUP_HEAD  = "#F1F0EB"   # 课程分组头底色（极浅灰标签底，与 COL_CHIP 同系，低调不抢内容）
COL_TIP_BLOCK   = "#E2F0E9"   # 「今日一招」高亮块背景（极浅薄荷绿，与 COL_SOFT 同系，醒目护眼）
COL_CARD_HOVER  = "#CDE8DA"   # 卡片 hover 底色（柔和薄荷绿，与 COL_HOVER 同系）

# ---------------- 内容区宽度（用户指定） ----------------
CONTENT_MAX      = 2400        # 内容区最大宽度（px，v1.6.4 1920→2400：2560 逻辑屏留白 320px→80px=÷4，仍保留上限保护可读性）
CONTENT_MARGIN   = 0           # 内容区左右边距（px）
CONTENT_MIN      = 440         # 内容区最小宽度（小窗口保护，px）

# ---------------- 打卡契约：场景与强度（公共契约冻结 v1.4；v1.6.9 场景扩 11 词） ----------------
SCENES = ["备考", "自习", "作业论文", "学生工作", "人际", "家庭关系",
          "睡眠状况", "身体", "娱乐休闲", "突发状况", "其他"]  # 语义排序：学业→关系→身心→休闲→兜底
INTENSITY_SEL = COL_PRIMARY                         # 保留：旧契约引用（v1.6.9 圆钮改用新色）
COL_INTEN_ON   = "#FFE14D"                          # 强度圆钮选中：荧光黄（v1.6.9）
COL_INTEN_GLOW = "#FFF3B0"                          # 强度圆钮选中外发光环：浅黄（v1.6.9）
INTEN_R        = 16                                 # 强度圆钮半径（px）


def circle_pick_btn(parent, text, selected=False, command=None):
    """圆形单选按钮（Canvas 自绘，v1.6.9，全项目可复用）。

    视觉：未选=浅灰底(COL_CHIP)+深字；选中=荧光黄(COL_INTEN_ON) +
    浅黄外发光环(COL_INTEN_GLOW)+高对比深字。
    交互：点击触发 command(text)（单选逻辑由调用方实现）。
    机制经 _exp_circle_btn.py 实验验证（36×36、点击切换正常）。
    返回 Canvas；用 redraw_circle(c, text, selected) 更新选中态。
    """
    c = tk.Canvas(parent, width=2 * INTEN_R + 4, height=2 * INTEN_R + 4,
                  bg=parent.cget("bg"), highlightthickness=0)
    redraw_circle(c, text, selected)
    if command:
        c.bind("<Button-1>", lambda ev: command(text))
    return c


def redraw_circle(c, text, selected):
    """重绘圆钮选中态（保持画布内元素一致，见 circle_pick_btn）。"""
    c.delete("all")
    r = INTEN_R
    if selected:
        c.create_oval(0, 0, 2 * r + 4, 2 * r + 4, fill=COL_INTEN_GLOW, outline="")
        c.create_oval(2, 2, 2 * r + 2, 2 * r + 2, fill=COL_INTEN_ON, outline="")
    else:
        c.create_oval(2, 2, 2 * r + 2, 2 * r + 2, fill=COL_CHIP, outline="")
    c.create_text(r + 2, r + 2, text=text, fill=COL_TEXT,
                  font=(FONT_FAMILY, 10, "bold"))

# ---------------- 字体 ----------------
FONT_FAMILY    = "Microsoft YaHei UI"   # 字体（本卡不变）


# ---------------- 内容区宽度辅助函数 ----------------
def content_width(avail):
    """按窗口可用宽计算内容区宽度（居中、自适应、有上限）。

    规则：上限 CONTENT_MAX、下限 CONTENT_MIN，
    左右边距 CONTENT_MARGIN（当前为 0，居中由调用方布局控制）。
    只做数值计算，不含任何业务逻辑。
    """
    return max(CONTENT_MIN, min(CONTENT_MAX, avail - 2 * CONTENT_MARGIN))


# ---------------- 圆角卡片组件（全项目复用） ----------------
def rounded_card(parent, radius=CARD_RADIUS, bg=COL_CARD, **kw) -> tk.Frame:
    """圆角卡片视觉容器：返回承载内容的 Frame，内容直接 pack 到它上面。

    结构：
        返回的 Frame（用户 pack 它，并把内容 pack 到它）
        └─ Canvas（place 铺满，绘制圆角矩形 + 极淡描边）

    视觉：
        - 圆角矩形用 create_polygon 平滑角实现（真圆角，非退化方案）。
        - 圆角外露区域透出 parent 背景色（默认取 parent 的 bg）。
        - 极淡描边用 CARD_SHADOW_LINE，替代投影近似。

    约束：
        - 仅负责视觉容器，不含任何业务逻辑与数据逻辑。

    参数：
        parent : 父容器（卡片放在它上面，圆角外露出它的背景色）
        radius : 圆角半径像素，默认 CARD_RADIUS=16
        bg     : 卡片底色，默认 COL_CARD
        **kw   : 透传给内部 Frame（如 width、height 等）
    """
    try:
        outer_bg = parent.cget("bg")
    except Exception:
        outer_bg = COL_BG

    inner = tk.Frame(parent, bg=bg, **kw)
    canvas = tk.Canvas(inner, bg=outer_bg, highlightthickness=0, bd=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def _draw(_ev=None):
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        r = max(0, min(radius, w // 2, h // 2))
        canvas.delete("all")
        pts = [
            r, 0,  w - r, 0,  w, 0,  w, r,
            w, h - r,  w, h,  w - r, h,  r, h,
            0, h,  0, h - r,  0, r,  0, 0,
        ]
        canvas.create_polygon(pts, smooth=True, fill=bg,
                              outline=CARD_SHADOW_LINE, width=1)

    canvas.bind("<Configure>", _draw)
    return inner


# ---------------- 导出白名单（耦合解耦：显式声明 import * 可用的名字） ----------------
# 仅导出视觉常量与组件函数，不导出内部 tk 引用等，避免命名空间污染。
__all__ = [
    # 配色
    "COL_BG", "COL_CARD", "COL_PRIMARY", "COL_PRIMARY_DK", "COL_ACCENT",
    "COL_TEXT", "COL_SUB", "COL_LINE", "COL_CHIP", "COL_SOFT",
    "COL_HOVER", "COL_INPUT_BG", "CARD_RADIUS", "CARD_SHADOW_LINE",
    "SPACING_CARD", "SPACING_BLOCK",
    # 手册图书馆模式令牌
    "COL_TAB_ON", "COL_TAB_OFF", "COL_GROUP_HEAD", "COL_TIP_BLOCK",
    "COL_CARD_HOVER",
    # 内容区宽度
    "CONTENT_MAX", "CONTENT_MARGIN", "CONTENT_MIN",
    # 打卡契约：场景与强度
    "SCENES", "INTENSITY_SEL", "COL_INTEN_ON", "COL_INTEN_GLOW", "INTEN_R",
    # 字体
    "FONT_FAMILY",
    # 组件与函数
    "circle_pick_btn", "redraw_circle", "content_width", "rounded_card",
]
