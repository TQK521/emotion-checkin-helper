# -*- coding: utf-8 -*-
"""data_store.py —— 数据存储模块（数据组员负责）

职责范围（只准改本文件内的数据逻辑）：
- 数据文件读写（JSON）、数据格式结构、旧版本数据迁移。
- 统计口径：连续天数、今日次数、累计次数、每日一课轮换索引。
- 供所有页面调用的数据函数。
- 不包含任何界面代码。

路径契约（重要）：
- 数据文件固定在【项目根目录】的 checkin_data.json（本项目根目录 =
  本文件所在目录的上一级）。
- 程序一律用相对路径定位，整个项目文件夹可整体搬家；包内文件不得
  改名、移动、删除。
"""

import datetime as dt
import json
import os

from chapters_data import CHAPTER_COUNT, EMOTIONS   # 章节总数元数据 + 内置词底（不依赖整份 CHAPTERS）

# 项目根目录的定位规则（打包适配）：
# - 源码运行（开发/双击 bat）：本文件在 src/ 下，项目根 = 本文件上一级；
# - exe 运行（打包交付）：__file__ 指向临时解压目录，不能用来定位，
#   此时项目根 = exe 所在目录（数据文件在 exe 同目录生成，整包可搬家）。
# 两种形态下，checkin_data.json 都固定在"程序所在的项目根目录"。
import sys as _sys
if getattr(_sys, "frozen", False):
    PROJECT_ROOT = os.path.dirname(os.path.abspath(_sys.executable))
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_ROOT, "checkin_data.json")

__all__ = [
    "PROJECT_ROOT", "DATA_FILE",
    "load_data", "save_data", "backup_data", "migrate_old_data",
    "check_data_file", "quarantine_corrupt_file", "auto_backup",
    "make_record",
    "today_str", "now_ts", "records_today",
    "calc_streak", "chapter_of_today", "fmt_emotions", "greeting",
    "all_emotions",
    "journal_fields",
]


def load_data():
    """读取打卡数据；文件不存在或损坏时返回全新空结构。"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return migrate_old_data(data)
        except Exception:
            pass
    return {"start_date": None, "records": [], "best_streak": 0}


def migrate_old_data(data):
    """把旧版「每天一次」的数据迁移成「按次记录」格式（历史记录不丢失）。"""
    if "records" not in data and isinstance(data.get("checkins"), dict):
        records = []
        for d, rec in sorted(data["checkins"].items()):
            emos = rec.get("emotions")
            if not isinstance(emos, list):
                emos = [rec["emotion"]] if rec.get("emotion") else []
            records.append({
                "ts": d + "T00:00:00",
                "date": d,
                "time": "",
                "emotions": emos,
                "action": rec.get("action", ""),
            })
        data["records"] = records
        data.pop("checkins", None)
    data.setdefault("records", [])
    data.setdefault("best_streak", 0)
    data.setdefault("custom_emotions", [])   # v1.4.3：用户自定义情绪词（{word, gloss}），旧数据缺省 []
    return data


def save_data(data):
    """把整个数据字典写回数据文件（原子写：先写临时文件再替换，崩溃不损坏原数据）。"""
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


def backup_data(dest_path):
    """把当前数据文件完整复制到指定路径（备份功能，G1）。返回是否成功。

    - 数据文件不存在时返回 False（程序还没产生数据，无可备份）。
    - 复制内容与 DATA_FILE 一致，供用户手动备份/迁移。
    """
    try:
        if not os.path.exists(DATA_FILE):
            return False
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


# ---------- 数据自检与自动备份（v1.6.7 数据安全） ----------

BACKUP_PREFIX = "checkin_data_备份_"


def check_data_file():
    """自检数据文件状态。返回 (status, detail)。

    status ∈ {"ok", "missing", "corrupt"}：
    - "ok"      : 文件存在且是合法 JSON 对象；
    - "missing" : 文件不存在（正常首次启动，空数据是预期）；
    - "corrupt" : 文件存在但解析失败或不是对象（数据已损坏，
                  必须保留现场并提示，禁止静默当空数据覆盖）。
    detail 为 corrupt 时的错误信息，其余为空串。
    """
    if not os.path.exists(DATA_FILE):
        return ("missing", "")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return ("corrupt", "顶层结构不是对象")
        return ("ok", "")
    except Exception as e:
        return ("corrupt", f"{type(e).__name__}: {e}")


def quarantine_corrupt_file():
    """损坏数据文件保留现场：改名 `checkin_data_损坏_<时间戳>.json`。

    - 用于自检发现 corrupt 后、加载空数据前的保护动作，
      防止后续保存把损坏原文件覆盖丢失；
    - 成功返回保留后的路径，无文件/失败返回 None。
    """
    try:
        if not os.path.exists(DATA_FILE):
            return None
        saved = os.path.join(os.path.dirname(DATA_FILE),
                             f"checkin_data_损坏_{now_ts().replace(':', '-')}.json")
        os.replace(DATA_FILE, saved)
        return saved
    except Exception:
        return None


def auto_backup(max_keep=7):
    """启动自动备份：数据正常时复制一份带日期的备份，保留最近 max_keep 份。

    - 仅备份合法数据（corrupt 不备份，现场保留交给 quarantine）；
    - 备份名 `checkin_data_备份_YYYY-MM-DD.json`，与数据文件同目录；
    - 同一天重复启动只覆盖当天一份（不堆积）；
    - 超过 max_keep 份按文件名倒序清理最旧备份。
    返回是否成功。
    """
    try:
        if check_data_file()[0] != "ok":
            return False
        backup_dir = os.path.dirname(DATA_FILE)
        backup_path = os.path.join(backup_dir,
                                   BACKUP_PREFIX + today_str() + ".json")
        if not backup_data(backup_path):
            return False
        backups = sorted(
            f for f in os.listdir(backup_dir)
            if f.startswith(BACKUP_PREFIX) and f.endswith(".json")
        )
        for old in backups[:-max_keep] if len(backups) > max_keep else []:
            try:
                os.remove(os.path.join(backup_dir, old))
            except Exception:
                pass
        return True
    except Exception:
        return False


def make_record(emotions, action="", scene="", intensity=3):
    """按当前数据契约构造一条打卡记录（记录 dict 的权威入口）。

    契约字段（公共契约冻结 v1.4）：ts / date / time / emotions / action /
    scene / intensity。
    - scene    : 场景字符串，默认 ""（旧 UI 未选场景）
    - intensity: 情绪强度 1-5，默认 3
    旧记录不含 scene / intensity 时，读取侧一律用
    rec.get("scene", "") / rec.get("intensity", 3) 兜底，
    不迁移、不覆盖旧数据。
    """
    now = dt.datetime.now()
    return {
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "emotions": list(emotions),
        "action": action,
        "scene": scene,
        "intensity": intensity,
    }


def today_str():
    """今天的日期字符串 YYYY-MM-DD。"""
    return dt.date.today().isoformat()


def now_ts():
    """当前完整时间戳 YYYY-MM-DD HH:MM:SS。"""
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def records_today(data):
    """返回今天的全部记录列表（按次记录模式，一天可能有多条）。"""
    t = today_str()
    return [r for r in data.get("records", []) if r.get("date") == t]


def calc_streak(records, end=None):
    """有打卡记录的天数里，从 end（默认今天）往前连续的天数。"""
    end = end or dt.date.today()
    dates = {r.get("date") for r in records}
    s = 0
    d = end
    while str(d) in dates:
        s += 1
        d -= dt.timedelta(days=1)
    return s


def chapter_of_today(data):
    """今天读第几课：从开始打卡那天起，按 10 课循环。"""
    if data.get("start_date"):
        try:
            start = dt.date.fromisoformat(data["start_date"])
            days = (dt.date.today() - start).days
            return days % CHAPTER_COUNT
        except Exception:
            pass
    return 0


def all_emotions(data):
    """全部可选情绪词 = 内置 EMOTIONS + 用户自定义词（v1.4.3 词库生长契约）。

    自定义词元素结构 {"word": str, "gloss": str}（gloss 可空）；
    返回去重后的词列表，供打卡标签、手册词库共用。
    """
    words = list(EMOTIONS)
    for e in data.get("custom_emotions", []):
        w = e.get("word") if isinstance(e, dict) else e
        if w and w not in words:
            words.append(w)
    return words


def fmt_emotions(rec):
    """把打卡记录里的情绪字段格式化成可读文本（兼容新旧数据格式）。"""
    emos = rec.get("emotions")
    if not isinstance(emos, list):
        emos = [rec["emotion"]] if rec.get("emotion") else []
    return "、".join(emos)


def journal_fields(entry):
    """兼容新旧 journal 条目，返回恒定的 (event, feeling, action) 三元组。

    新契约（v1.5）：条目 = {"date", "time", "event", "feeling", "action"}，
    action 可空字符串；
    旧条目：仅含 text（三句用 "\\n" 连接），按行拆分为 3 段并剔除旧占位
    提示语（命中则置空）。

    规则：
    - 新条目直接返回三字段，缺失字段兜底为空字符串；
    - 旧条目按 "\\n" 拆段，拆分段数不足则缺失段置空；
    - 无换行的自由文本（如 "哈哈哈"）→ event = 原文、feeling/action 空；
    - 占位提示语：旧 UI 未填写的提示原文，命中整段即置空。

    返回结构恒为 (event, feeling, action) 三元组，供展示与预览共用（⑦）。
    """
    if "text" not in entry:
        return (entry.get("event", ""), entry.get("feeling", ""),
                entry.get("action", ""))

    placeholders = {
        "（今天让你有情绪的一件事）",
        "（给这个感受起个名字）",
        "（下一步的小行动，可选）",
    }
    lines = (entry.get("text") or "").split("\n")
    parts = []
    for ln in lines[:3]:
        ln = ln.strip()
        parts.append("" if ln in placeholders else ln)
    while len(parts) < 3:
        parts.append("")
    return (parts[0], parts[1], parts[2])


def greeting():
    """按当前时段返回问候语。"""
    h = dt.datetime.now().hour
    if h < 6:
        return "夜深了"
    if h < 11:
        return "早上好"
    if h < 14:
        return "中午好"
    if h < 18:
        return "下午好"
    return "晚上好"
