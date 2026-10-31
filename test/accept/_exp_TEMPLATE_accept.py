# -*- coding: utf-8 -*-
"""_exp_TEMPLATE_accept.py —— 标准验收模板（两段式 · 算力刀刃 v1.2）

【复制本模板起新验收脚本，禁止从零手写骨架】（约束九.2 / 约束十.1）
运行模式：
    py _exp_xxx.py          # 完整模式：段1+段2+段3（隔离/压力段也跑）——交付前用
    py _exp_xxx.py --fast   # 开发模式：段1+段2，跳过段3 隔离/压力段——开发返工循环用
开发中返回循环跑 --fast（不启动隔离 App）；交付前必须完整模式跑一次。
段门：任何段内 check() FAIL → 打印 STOP-AT-PHASE 并退出，后续段不再启动（省算力）。
"""
import hashlib
import os
import sys
import time

ROOT = r"C:\Users\29236\Desktop\桌面小程序开发"
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "docs", "jingyan-zichan", "11-yanshou-kufu"))

from accept_lib import check, phase, boot_once, make_isolated_data, runlog, report

FAST = "--fast" in sys.argv          # 开发模式：跳过段3（隔离/压力）

REAL = os.path.join(ROOT, "checkin_data.json")
def real_hash():
    with open(REAL, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

# ==================== 段1 · 纯逻辑/静态（零 GUI，秒级） ====================
with phase("P1-纯逻辑静态"):
    check("示例-契约断言", True)

# ==================== 段2 · GUI 冒烟·真实数据（boot_once 单例复用） ====================
with phase("P2-GUI真实数据"):
    app, W = boot_once(tag="real")
    check("示例-组件存在", True)
    # ……多断言复用同一 App 实例，不再重复启动

# ==================== 段3 · 隔离数据/压力段（--fast 跳过；交付前必跑） ====================
if not FAST:
    with phase("P3-隔离数据"):
        tmp = make_isolated_data(records=[])
        from main import App
        app2 = App()
        try:
            app2.update()
            check("示例-隔离断言", True)
        finally:
            app2.destroy()
        import data_store
        data_store.DATA_FILE = REAL
        data_store.auto_backup()      # 恢复今日备份为真实内容
else:
    print("FAST-MODE: 跳过 P3 隔离/压力段（交付前需完整模式跑一次）")

# ==================== 段4 · 哈希零污染 + 登记（总是跑） ====================
with phase("P4-哈希登记"):
    h_before = real_hash()            # 若需基线请在段1 前取
    h_after = real_hash()
    check("real-hash-clean", h_before == h_after, f"{h_before} vs {h_after}")

sys.exit(0 if report() == 0 else 1)
