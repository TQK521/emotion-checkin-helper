# -*- coding: utf-8 -*-
"""export_webapp_data.py —— 一次性数据转换：把 Python 静态数据导出为 webapp 静态 JSON。

运行：py -3.13 scripts/export_webapp_data.py
数据口径（权威）：
- chapters_data：CHAPTERS / EMOTIONS / EMOTION_GLOSSARY / WARM_INTRO / GROUP_ORDER / CHAPTER_COUNT
- toolkit_data：TOOL_STATES / STATE_RECS / TOOL_GROUPS / TOOL_METHODS
- 元组（full、TOOL_STATES、TOOL_GROUPS）经 json.dump 自动转为数组，保持顺序。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chapters_data as ch  # noqa: E402
import toolkit_data as tk  # noqa: E402

OUT = ROOT / "webapp" / "src" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def dump(name, payload):
    with open(OUT / name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# 手册每日一课（含 full 长文元组 → 数组）
dump("chapters.json", {
    "chapters": ch.CHAPTERS,
    "group_order": ch.GROUP_ORDER,
    "chapter_count": ch.CHAPTER_COUNT,
    "warm_intro": ch.WARM_INTRO,
})

# 情绪词与词库
dump("emotions.json", {
    "emotions": ch.EMOTIONS,
    "glossary": ch.EMOTION_GLOSSARY,
})

# 工具箱（状态分流 + 方法库）
dump("toolkit.json", {
    "states": tk.TOOL_STATES,
    "state_recs": tk.STATE_RECS,
    "groups": tk.TOOL_GROUPS,
    "methods": tk.TOOL_METHODS,
})

# 条数自检（实际口径，不预设）
print("chapters=", len(ch.CHAPTERS))
print("group_order=", len(ch.GROUP_ORDER))
print("emotions=", len(ch.EMOTIONS))
print("glossary=", len(ch.EMOTION_GLOSSARY))
print("tool_states=", len(tk.TOOL_STATES))
print("tool_groups=", len(tk.TOOL_GROUPS))
print("tool_methods=", len(tk.TOOL_METHODS))
