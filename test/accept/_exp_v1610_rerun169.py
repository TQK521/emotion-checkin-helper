# -*- coding: utf-8 -*-
"""_exp_v1610_rerun169.py —— v1.6.9 验收重跑副本（v1.6.10 四项解耦改动后回归）

两段式（算力刀刃 v1.2）：
    段1 纯逻辑/静态（契约/组件/绑定/提交签名，零 GUI）
    段2 GUI 冒烟·真实数据（场景单选+取消、强度圆钮，boot_once 单例）
    段3 隔离数据·新场景进统计（--fast 跳过；交付前必跑）
    段4 哈希零污染 + 今日备份恢复
运行：py _exp_v1610_rerun169.py [--fast]
"""
import hashlib
import inspect
import os
import sys
import time

ROOT = r"C:\Users\29236\Desktop\桌面小程序开发"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "docs", "jingyan-zichan", "11-yanshou-kufu"))

import theme
import data_store
from accept_lib import (check, phase, boot_once, make_isolated_data,
                        runlog, report, walk_labels)

FAST = "--fast" in sys.argv

REAL = os.path.join(ROOT, "checkin_data.json")
def real_hash():
    with open(REAL, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

# ==================== 段1 · 纯逻辑/静态（零 GUI） ====================
with phase("P1-纯逻辑静态"):
    EXPECT = ["备考", "自习", "作业论文", "学生工作", "人际", "家庭关系",
              "睡眠状况", "身体", "娱乐休闲", "突发状况", "其他"]
    check("SCENES-11词", theme.SCENES == EXPECT, str(len(theme.SCENES)))
    check("SCENES-其他兜底最后", theme.SCENES[-1] == "其他")
    check("theme-新色组件",
          hasattr(theme, "COL_INTEN_ON") and hasattr(theme, "COL_INTEN_GLOW")
          and hasattr(theme, "circle_pick_btn") and hasattr(theme, "redraw_circle"))
    src = open(os.path.join(ROOT, "src", "pages_home.py"),
               encoding="utf-8").read()
    check("home-绑定圆钮", "circle_pick_btn(inten_wrap" in src
          and "redraw_circle(canvas, txt" in src)
    check("home-场景取消逻辑", "_on_scene_click" in src and "_on_inten_click" in src)
    sig = inspect.signature(data_store.make_record)
    params = list(sig.parameters)
    check("make_record-契约未变",
          "scene" in params and "intensity" in params
          and sig.parameters["scene"].default == ""
          and sig.parameters["intensity"].default == 3)

# ==================== 段2 · GUI 冒烟·真实数据（boot_once 单例复用） ====================
h_before = real_hash()
with phase("P2-GUI真实数据"):
    app, W = boot_once(tag="real")
    scene_chips = getattr(app, "_scene_chips", [])
    vals = [c.opt for c in scene_chips]
    check("场景-11个chip", len(scene_chips) == 11 and vals == EXPECT, f"n={len(scene_chips)}")
    def click_scene(chip):
        chip.invoke(); app.update()
    b1 = scene_chips[0]
    b2 = scene_chips[1]
    click_scene(b1)
    check("场景-选中备考", app.scene_var.get() == "备考")
    click_scene(b2)
    sel_style_b1 = b1.cget("bg")
    check("场景-单选互斥", app.scene_var.get() == "自习"
          and sel_style_b1 == theme.COL_CHIP, sel_style_b1)
    click_scene(b2)
    check("场景-再次点击取消", app.scene_var.get() == "")

    inten = getattr(app, "_inten_chips", [])
    check("强度-5个圆钮", len(inten) == 5)
    c3, c5 = inten[2][0], inten[4][0]
    fills3 = [c3.itemcget(i, "fill") for i in c3.find_all() if c3.type(i) == "oval"]
    fills5 = [c5.itemcget(i, "fill") for i in c5.find_all() if c5.type(i) == "oval"]
    check("强度-默认3选中", app.intensity_var.get() == 3
          and theme.COL_INTEN_ON in fills3, str(fills3))
    check("强度-未选浅底", theme.COL_CHIP in fills5, str(fills5))
    c5.event_generate("<Button-1>", when="now")
    app.update()
    fills5b = [c5.itemcget(i, "fill") for i in c5.find_all() if c5.type(i) == "oval"]
    check("强度-点击5切换", app.intensity_var.get() == 5
          and theme.COL_INTEN_ON in fills5b, str(fills5b))
    wrap = inten[0][0].master
    lbls = [w.cget("text") for w in wrap.winfo_children() if w.winfo_class() == "Label"]
    check("强度-弱/强标注", "弱" in lbls and "强" in lbls, str(lbls))
    app.destroy()

# ==================== 段3 · 隔离数据·新场景进统计（--fast 跳过；交付前必跑） ====================
if not FAST:
    with phase("P3-隔离数据统计"):
        today = time.strftime("%Y-%m-%d")
        now = time.strftime("%H:%M")
        rec = {"ts": f"{today}T{now}:00", "date": today, "time": now,
               "emotions": ["焦虑"], "action": "作业赶deadline", "scene": "作业论文",
               "intensity": 5}
        tmp = make_isolated_data(records=[rec], start_date=today)
        from main import App
        app2 = App()
        try:
            app2.update()
            app2.show_page("record")
            for _ in range(3):
                app2.update(); time.sleep(0.2); app2.update()
            texts = [l.cget("text") for l in walk_labels(app2.week_review_frame)]
            joined = " | ".join(texts)
            check("复盘-新场景进统计", "主要场景：作业论文" in joined, joined[:80])
        finally:
            app2.destroy()
        data_store.DATA_FILE = REAL
        data_store.auto_backup()      # 恢复今日备份为真实内容
else:
    print("FAST-MODE: 跳过 P3 隔离数据段（交付前需完整模式跑一次）")

# ==================== 段4 · 哈希零污染 ====================
with phase("P4-哈希登记"):
    h_after = real_hash()
    check("real-hash-clean", h_before == h_after, f"{h_before} vs {h_after}")

try:  # accept_lib.runlog 硬编码旧路径(01-项目规范)，重构后目录不存在会崩；记录失败不影响断言结论
    runlog(__file__, note="%s" % ("fast" if FAST else "full"))
except Exception as _e:
    print("RUNLOG-SKIP:", _e)
sys.exit(0 if report("SCENE-INTEN") == 0 else 1)
