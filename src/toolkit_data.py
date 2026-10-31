# -*- coding: utf-8 -*-
"""toolkit_data.py —— 工具页科学方法库数据模块（内容组员负责）

职责范围（只准改本文件内的数据）：
- 状态分流配置：TOOL_STATES（6 个情绪状态）+ STATE_RECS（状态 → 推荐方法 key）
- 方法库：TOOL_METHODS（30 条科学循证方法，7 组 A-G），每组含分组头与条数
- 字段结构（冻结，勿增删）：key/name/group/time/why/steps/evidence/action
  - action：breath_sigh / breath_478 / breath_box → 呼吸弹窗模式；None → 步骤卡引导
- 不包含任何界面逻辑（在 pages_tool.py）与业务存储（在 data_store.py）。

证据强度：★★★★★ 多中心 RCT/系统综述；★★★★ RCT/元分析；★★★ 权威指南/机制研究
"""

# ---------------- 状态分流配置（顶部 chips 顺序即展示顺序） ----------------
TOOL_STATES = [
    ("acute",     "急性难受"),
    ("tense",     "烦躁紧张"),
    ("low",       "低落没劲"),
    ("ruminate",  "胡思乱想"),
    ("selfcrit",  "自我批判"),
    ("nurture",   "想滋养自己"),
]

# 状态 → 推荐方法 key（3 条最快，按适用性排序）
STATE_RECS = {
    "acute":    ["physio_sigh", "grounding_54321", "box_breath"],
    "tense":    ["pmr_short", "ground_walk", "body_scan"],
    "low":      ["behavior_act", "aerobic", "outdoor"],
    "ruminate": ["name_it", "reappraisal", "defusion"],
    "selfcrit": ["act_accept", "self_compassion", "loving_kindness"],
    "nurture":  ["three_good", "gratitude", "savoring"],
}

# ---------------- 方法库（7 组，共 30 条） ----------------
TOOL_GROUPS = [
    ("A", "急性难受",  "60 秒～5 分钟，先拉回当下"),
    ("B", "烦躁紧绷",  "5～20 分钟，释放身体紧张"),
    ("C", "胡思乱想",  "5～15 分钟，处理想法"),
    ("D", "低落没劲",  "15～30 分钟，先动起来"),
    ("E", "自我批判",  "5～20 分钟，练习接纳与慈悲"),
    ("F", "滋养自己",  "5～10 分钟/天，培育积极情绪"),
    ("G", "生活底盘",  "长期预防性习惯"),
]

TOOL_METHODS = [
    # ---------- A 急性难受（6） ----------
    {"key": "physio_sigh", "name": "生理性叹息", "group": "A", "time": "1 分钟",
     "why": "双重吸气+长呼气，刺激迷走神经，秒级降心率",
     "steps": ["先快速吸两口气", "第二口吸到最满", "缓慢深长地呼气", "重复 2-3 次"],
     "evidence": "★★★★ 斯坦福研究", "action": "breath_sigh"},
    {"key": "grounding_54321", "name": "5-4-3-2-1 接地法", "group": "A", "time": "2-3 分钟",
     "why": "让大脑处理真实感官输入，挤掉恐慌信号",
     "steps": ["看到 5 样东西", "摸到 4 样东西", "听到 3 种声音", "闻到 2 种气味", "尝到 1 种味道"],
     "evidence": "★★★★ RCT", "action": None},
    {"key": "breath_478", "name": "4-7-8 呼吸", "group": "A", "time": "2 分钟",
     "why": "延长呼气激活副交感神经，防过度换气",
     "steps": ["鼻吸气 4 秒", "屏住 7 秒", "嘴呼气 8 秒", "循环 4 次以上"],
     "evidence": "★★★★ 术后患者焦虑 −35%", "action": "breath_478"},
    {"key": "box_breath", "name": "盒式呼吸 4-4-4-4", "group": "A", "time": "1-2 分钟",
     "why": "等长呼吸稳定节律，办公/公共场合不显眼",
     "steps": ["吸气 4 秒", "屏住 4 秒", "呼气 4 秒", "屏住 4 秒", "重复几轮"],
     "evidence": "★★★★ 高应激人群", "action": "breath_box"},
    {"key": "cold_water", "name": "冷水/冰块法", "group": "A", "time": "<1 分钟",
     "why": "哺乳动物潜水反射强制降心率，打断惊恐回路",
     "steps": ["冷水泼脸或冲手腕", "或握一块冰", "感受凉意 30 秒"],
     "evidence": "★★★ 惊恐发作推荐", "action": None},
    {"key": "ground_feet", "name": "脚踩大地/锚定", "group": "A", "time": "30-60 秒",
     "why": "本体感觉输入切断解离感",
     "steps": ["双脚用力踩地", "感受脚底的支撑", "或握紧桌沿感受质感"],
     "evidence": "★★★★", "action": None},

    # ---------- B 烦躁紧绷（4） ----------
    {"key": "pmr_short", "name": "渐进放松·简版", "group": "B", "time": "3 分钟",
     "why": "紧张与放松不能共存，先紧后松产生对比",
     "steps": ["握拳 5 秒→松开 10 秒", "耸肩到耳朵→放下", "皱紧脸→松开", "重复 2-3 组"],
     "evidence": "★★★★ 元分析显著降焦虑", "action": None},
    {"key": "pmr_full", "name": "渐进放松·全版", "group": "B", "time": "10-15 分钟",
     "why": "系统走遍全身肌群，释放深层紧张",
     "steps": ["从脚趾开始绷紧 5 秒", "放松 10 秒", "依次到小腿、大腿、腹部、手、肩、脸", "每处都绷紧再放松"],
     "evidence": "★★★★ 烧伤患者焦虑 −43%", "action": None},
    {"key": "body_scan", "name": "身体扫描", "group": "B", "time": "10-20 分钟",
     "why": "MBSR 核心练习，释放身体积压的紧张",
     "steps": ["躺好或坐稳，闭眼", "从头顶开始感受", "慢慢移到脖子、肩膀、胸口", "最后到脚趾"],
     "evidence": "★★★★ MBSR 体系", "action": None},
    {"key": "ground_walk", "name": "落地散步/拉伸", "group": "B", "time": "5-15 分钟",
     "why": "运动打断反刍，改善情绪中枢调节",
     "steps": ["慢走 5 分钟", "感受脚步与地面", "或拉伸肩颈收尾"],
     "evidence": "★★★★", "action": None},

    # ---------- C 胡思乱想（6） ----------
    {"key": "name_it", "name": "情绪命名", "group": "C", "time": "1 分钟",
     "why": "说出来它就变小：语言标定激活前额叶，降低杏仁核活跃",
     "steps": ["不说“很难受”", "说出具体情绪名", "加上原因：“我愤怒，因为……”"],
     "evidence": "★★★★ 脑成像研究", "action": None},
    {"key": "reappraisal", "name": "认知重评", "group": "C", "time": "3 分钟",
     "why": "改变事件的意义而非压抑表达，降生理唤起",
     "steps": ["写下让你难受的事", "写下第一反应的想法", "写一个不同的解释", "例如：否方案→只是对事不对人"],
     "evidence": "★★★★★ Gross 系列研究", "action": None},
    {"key": "reframe_3q", "name": "认知重构三问", "group": "C", "time": "3 分钟",
     "why": "破除灾难化自动思维",
     "steps": ["问：有 100% 证据吗？", "问：最坏真发生怎么办？", "问：朋友遇到会怎么劝我？"],
     "evidence": "★★★★ 权威科普", "action": None},
    {"key": "self_distance", "name": "自我疏离", "group": "C", "time": "3 分钟",
     "why": "第三人称视角降低情绪强度",
     "steps": ["用“他/她”称呼自己", "像说别人一样讲自己的事", "语气换成朋友的语气"],
     "evidence": "★★★★ 机制研究", "action": None},
    {"key": "expressive_write", "name": "表达性书写", "group": "C", "time": "15 分钟",
     "why": "用语言重构经历，做认知整理而非宣泄",
     "steps": ["写下情绪事件", "写出真实感受", "写这件事对你意味着什么", "每周 3-4 次即可"],
     "evidence": "★★★★ 在线书写 RCT", "action": None},
    {"key": "defusion", "name": "认知解离", "group": "C", "time": "3 分钟",
     "why": "与想法拉开距离，不当真",
     "steps": ["在想法前加“我有一个想法：”", "或想象想法像树叶漂走", "看着它，不跟着它走"],
     "evidence": "★★★★ ACT 元分析", "action": None},

    # ---------- D 低落没劲（3） ----------
    {"key": "behavior_act", "name": "行为激活", "group": "D", "time": "15 分钟",
     "why": "行动先于动机：低谷时先动，感觉随后到",
     "steps": ["列 3 件小事：喝水/出门/整理", "挑 1 件立刻做", "只做 10 分钟"],
     "evidence": "★★★★★ CBT 核心", "action": None},
    {"key": "aerobic", "name": "有氧运动", "group": "D", "time": "20-30 分钟",
     "why": "单次中等强度运动即改善情绪，神经机制已证实",
     "steps": ["快走/慢跑/骑车", "做 20-30 分钟", "微微出汗即可"],
     "evidence": "★★★★★ 中科院心理所 2025 RCT", "action": None},
    {"key": "outdoor", "name": "户外自然接触", "group": "D", "time": "10-20 分钟",
     "why": "接触自然降低反刍与批判性思维活跃",
     "steps": ["去公园或绿化带", "别戴耳机", "走 10-20 分钟"],
     "evidence": "★★★★", "action": None},

    # ---------- E 自我批判（3） ----------
    {"key": "act_accept", "name": "ACT 接纳", "group": "E", "time": "5 分钟",
     "why": "允许情绪存在、不战斗，减少二次痛苦",
     "steps": ["觉察情绪在身体哪里", "找到它的位置", "对它说：我允许你在这"],
     "evidence": "★★★★★ 多国指南一线推荐", "action": None},
    {"key": "self_compassion", "name": "自我慈悲三问", "group": "E", "time": "5 分钟",
     "why": "像安慰朋友一样对待自己，对抗自我攻击",
     "steps": ["问：此刻我难受吗？", "想：人人都会有难受", "对自己说句安慰的话"],
     "evidence": "★★★★ 自我慈悲 RCT", "action": None},
    {"key": "loving_kindness", "name": "慈心冥想", "group": "E", "time": "10-15 分钟",
     "why": "培养温暖联结感，对抗孤独与自我苛责",
     "steps": ["闭眼默念：愿我平安", "愿我快乐、愿我轻松", "把祝福扩展到家人朋友"],
     "evidence": "★★★★ 7 周练习提升积极情绪", "action": None},

    # ---------- F 滋养自己（6） ----------
    {"key": "three_good", "name": "三件好事", "group": "F", "time": "5 分钟/晚",
     "why": "训练注意偏向积极，写清原因才有效",
     "steps": ["睡前想今天 3 件好事", "写下来", "写下为什么发生"],
     "evidence": "★★★★★ Seligman RCT，6 个月有效", "action": None},
    {"key": "gratitude", "name": "感恩记录", "group": "F", "time": "5 分钟/天",
     "why": "提升幸福基线，7 天可见效",
     "steps": ["写下想感谢的事", "天气/人/机会都可以", "坚持 7 天"],
     "evidence": "★★★★★ 大快乐计划 RCT +48%", "action": None},
    {"key": "gratitude_letter", "name": "感恩信/拜访", "group": "F", "time": "30-60 分钟/月",
     "why": "最强积极干预之一，效果持续 1 个月+",
     "steps": ["给没谢过的人写信", "写 300 字具体细节", "当面读给对方听"],
     "evidence": "★★★★★ 积极心理学经典", "action": None},
    {"key": "savoring", "name": "品味 Savoring", "group": "F", "time": "5-10 分钟",
     "why": "把好体验放大延长，训练享受当下",
     "steps": ["遇到好事停 30 秒", "看细节、感受身体反应", "记住这个画面"],
     "evidence": "★★★★ Bryant & Veroff 研究", "action": None},
    {"key": "kindness", "name": "善举微行动", "group": "F", "time": "<5 分钟",
     "why": "利他提升幸福感与联结感",
     "steps": ["帮人开门/递东西", "发一句鼓励的话", "今天做 1 件就行"],
     "evidence": "★★★★ 大快乐计划", "action": None},
    {"key": "best_self", "name": "最佳自我可视化", "group": "F", "time": "10-15 分钟",
     "why": "增强希望感与目标承诺",
     "steps": ["想象 1 年后最好的自己", "写下细节：环境/状态/关系", "每天读一遍"],
     "evidence": "★★★★ BPS 干预", "action": None},

    # ---------- G 生活底盘（2） ----------
    {"key": "sleep_hygiene", "name": "睡眠卫生", "group": "G", "time": "每晚",
     "why": "深度睡眠是大脑排废窗口，情绪底盘",
     "steps": ["固定睡觉起床时间", "睡前 1 小时远离屏幕", "睡够 7-8 小时"],
     "evidence": "★★★★ 权威科普", "action": None},
    {"key": "weekly_exercise", "name": "规律运动周课", "group": "G", "time": "每周 150 分钟",
     "why": "长期改善抑郁焦虑，效果可比药物且防复发",
     "steps": ["每周 3-5 次", "每次 30 分钟中等强度", "快走/慢跑/游泳都行"],
     "evidence": "★★★★★ Schuch 元分析", "action": None},
]

# 分组索引（供页面按组渲染，保持 TOOL_GROUPS 顺序）
def methods_by_group(gkey):
    return [m for m in TOOL_METHODS if m["group"] == gkey]

def method_by_key(key):
    for m in TOOL_METHODS:
        if m["key"] == key:
            return m
    return None
