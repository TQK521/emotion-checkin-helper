# -*- coding: utf-8 -*-
"""_exp_v1610_smoke.py —— v1.6.10 四项解耦改动·手册专项 + 四页冒烟（隔离数据）

段 P1 手册页功能专项（ManualMixin 迁移后行为 + MRO 协作链端到端）
段 P2 四页冒烟·用户操作流（切页 → 打卡写入 → 记录可见 → 切回刷新）
段 P3 数据哈希核验（真实 checkin_data.json 未被程序触碰）
运行：py _exp_v1610_smoke.py
"""
import hashlib
import os
import sys
import time

ROOT = r"C:\Users\29236\Desktop\桌面小程序开发"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "docs", "jingyan-zichan", "11-yanshou-kufu"))

from accept_lib import (check, phase, boot_once, make_isolated_data,
                        runlog, report, walk_labels, walk_all, shot)

REAL = os.path.join(ROOT, "checkin_data.json")
H_EXPECT = "edd323d3ec0b91ed"   # v1.6.9 重跑前实测（改动全程未触碰数据）


def real_hash():
    with open(REAL, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


# ==================== 段 P1 · 手册页功能专项（隔离数据） ====================
with phase("P1-手册专项"):
    today = time.strftime("%Y-%m-%d")
    now = time.strftime("%H:%M")
    rec0 = {"ts": f"{today}T{now}:00", "date": today, "time": now,
            "emotions": ["焦虑"], "action": "初始化记录",
            "scene": "备考", "intensity": 3}
    make_isolated_data(records=[rec0], start_date=today)
    app, W = boot_once(tag="smoke")

    # ---- 切到手册页，三视图逐一切换 ----
    app.show_page("manual")
    app.update()
    check("手册-页面可达", app.pages["manual"].winfo_viewable())
    check("手册-3个Tab按钮",
          set(app._manual_tab_btns) == {"today", "catalog", "glossary"})

    # ---- 今日一课 ----
    check("今日一课-已选课", isinstance(app._today_ch, dict)
          and "name" in app._today_ch, app._today_ch.get("name", ""))
    texts = [l.cget("text") for l in walk_labels(app._manual_content)]
    check("今日一课-含今日推荐", any("今日推荐" in t for t in texts),
          " | ".join(texts[:3]))
    shot(app, "_exp_shot_v1610_manual_today.png")

    # ---- 目录 ----
    app._show_manual_tab("catalog")
    app.update()
    cat_texts = [l.cget("text") for l in walk_labels(app._manual_content)]
    group_heads = [t for t in cat_texts if "课）" in t and ("▼" in t or "▲" in t)]
    check("目录-7个分组头", len(group_heads) == 7, str(len(group_heads)))

    # ---- 词库 + 搜索过滤 ----
    app._show_manual_tab("glossary")
    app.update()
    n_all = len(app._glossary_inner.winfo_children())
    check("词库-词条已渲染", n_all > 0, f"n={n_all}")
    app._glossary_var.set("焦虑")
    app.update()
    n_kw = len(app._glossary_inner.winfo_children())
    check("词库-搜索过滤生效", 0 < n_kw < n_all, f"{n_all}->{n_kw}")
    app._glossary_var.set("")
    app.update()

    # ---- MRO 协作链端到端：添加自定义情绪词（ManualMixin 前置 super 链） ----
    app._glossary_var.set("")
    app.update()
    ok = app._add_custom_emotion("验收测试词")
    check("协作-添加返回True", ok is True)
    check("协作-写入custom_emotions",
          app.data["custom_emotions"][-1]["word"] == "验收测试词")
    gl_texts = [l.cget("text") for l in walk_labels(app._glossary_inner)]
    check("协作-词库区含新词", any("验收测试词" == t for t in gl_texts),
          "词库区未刷新" if not any("验收测试词" == t for t in gl_texts) else "已刷新")
    shot(app, "_exp_shot_v1610_manual_glossary.png")

    # ---- 详情页 + 返回（返回按钮是 tk.Button，需 walk_all 而非 walk_labels） ----
    ch = app._today_ch
    app._open_detail(ch)
    app.update()
    d_btns = [w for w in walk_all(app._manual_content)
              if w.winfo_class() == "Button" and "← 返回" in str(w.cget("text"))]
    check("详情-含返回按钮", len(d_btns) == 1, f"buttons={len(d_btns)}")

    # ---- 换一课 ----
    app._show_manual_tab("today")
    app.update()
    old = app._today_ch
    app._swap_today_lesson()
    app.update()
    check("换一课-不同课", app._today_ch is not old)

# ==================== 段 P2 · 四页冒烟·用户操作流（同一 App） ====================
with phase("P2-四页冒烟"):
    n0 = len(app.data["records"])

    # home：可达 + 场景 chips
    app.show_page("home")
    app.update()
    check("home-页面可达", app.pages["home"].winfo_viewable())
    check("home-场景chips", len(getattr(app, "_scene_chips", [])) == 11)

    # 打卡写入（GUI 路径：勾选情绪 → 记录）
    app.selected_emotions = ["焦虑"]
    app.emo_entry.delete(0, "end")
    app.note_entry.delete("1.0", "end")
    app.note_entry.insert("1.0", "冒烟测试记录")
    app._record_emotion()
    app.update()
    n1 = len(app.data["records"])
    check("写入-记录+1", n1 == n0 + 1, f"{n0}->{n1}")
    check("写入-撤销入口可见", app.undo_btn.winfo_ismapped())
    shot(app, "_exp_shot_v1610_home.png")

    # record：可达 + 统计卡 + 日历 + 新记录可见
    app.show_page("record")
    for _ in range(3):
        app.update()
        time.sleep(0.1)
        app.update()
    check("record-页面可达", app.pages["record"].winfo_viewable())
    check("record-周复盘卡渲染",
          app.week_review_frame.winfo_ismapped()
          and len(app.week_review_frame.winfo_children()) > 0)
    check("record-日历网格渲染", app.cal_grid.winfo_ismapped())
    # 历史列表默认折叠：按用户操作流点击「查看历史记录」展开后断言新记录可见
    if not getattr(app, "_hist_visible", False):
        app.hist_btn.invoke()
    for _ in range(2):
        app.update()
        time.sleep(0.1)
        app.update()
    hist_texts = [l.cget("text") for l in walk_labels(app.rec_list)]
    day_title = f"{time.strftime('%m').lstrip('0')}月{time.strftime('%d').lstrip('0')}日"
    check("record-新记录可见", any(day_title in t for t in hist_texts),
          "日志区未含今日" if not any(day_title in t for t in hist_texts)
          else "今日记录在日志")
    shot(app, "_exp_shot_v1610_record.png")

    # tool：可达 + 工具箱渲染
    app.show_page("tool")
    app.update()
    check("tool-页面可达", app.pages["tool"].winfo_viewable())
    check("tool-工具箱渲染", app._toolkit_body.winfo_ismapped())

    # manual：切回可达（此前已验功能）
    app.show_page("manual")
    app.update()
    check("manual-再切可达", app.pages["manual"].winfo_viewable())

    # 回 home：计数刷新（head_count_label 含新总数）
    app.show_page("home")
    app.update()
    head_txt = app.head_count_label.cget("text")
    check("home-计数含新记录数", str(n1) in head_txt, head_txt)

    app.destroy()

# ==================== 段 P3 · 数据哈希核验 ====================
with phase("P3-哈希核验"):
    h = real_hash()
    check("真实数据哈希未变", h == H_EXPECT, f"{h} vs {H_EXPECT}")

try:  # accept_lib.runlog 硬编码旧路径会崩；记录失败不影响结论
    runlog(__file__, note="full")
except Exception as _e:
    print("RUNLOG-SKIP:", _e)
sys.exit(0 if report("V1610-SMOKE") == 0 else 1)
