/**
 * tool-data.ts —— 工具箱域纯逻辑层（对齐 toolkit_data.py / pages_tool.py）
 * 数据加载、推荐排序、呼吸模式参数、日记旧格式兼容均在此，组件只负责渲染。
 */
import toolkitJson from "@/assets/data/toolkit.json";
import emotionsJson from "@/assets/data/emotions.json";
import type {
  BreathAction,
  CustomEmotion,
  JournalEntry,
  ToolMethod,
  ToolkitFile,
} from "@/core/domain";

/** 冻结数据（JSON 数组字面量非元组，统一在此收窄为契约类型） */
export const toolkit: ToolkitFile = toolkitJson as unknown as ToolkitFile;

/** 内置情绪词（56，对齐 emotions.json / Python EMOTIONS） */
export const builtinEmotions: string[] = (emotionsJson as { emotions: string[] }).emotions;

/** 按 key 取方法 */
export function methodByKey(key: string): ToolMethod | undefined {
  return toolkit.methods.find((m) => m.key === key);
}

/** 按分组 key 取方法（保持 JSON 内顺序） */
export function methodsByGroup(g: string): ToolMethod[] {
  return toolkit.methods.filter((m) => m.group === g);
}

/**
 * 时长字符串 → 分钟数（用于"最短在前"排序）。
 * 口径：取首个数字；"X-Y" 区间取短端；"<1" 得 1；解析不到记无穷大。
 */
export function parseMinutes(time: string): number {
  const range = /(\d+)\s*[-~]\s*(\d+)/.exec(time);
  if (range) return Number(range[1]);
  const single = /(\d+)/.exec(time);
  if (single) return Number(single[1]);
  return Number.POSITIVE_INFINITY;
}

/** 状态分流推荐：state_recs 对应方法 → 按 time 升序（最短在前）取全部（约定 3 条） */
export function recommendedMethods(stateKey: string): ToolMethod[] {
  const keys = toolkit.state_recs[stateKey] ?? [];
  return keys
    .map(methodByKey)
    .filter((m): m is ToolMethod => !!m)
    .sort((a, b) => parseMinutes(a.time) - parseMinutes(b.time));
}

/** 全部可选情绪词 = 内置 56 + 自定义（去重，对齐 all_emotions） */
export function allEmotionWords(custom: CustomEmotion[] | undefined): string[] {
  const words = [...builtinEmotions];
  for (const e of custom ?? []) {
    if (e.word && !words.includes(e.word)) words.push(e.word);
  }
  return words;
}

/**
 * 兼容新旧 journal 条目，返回恒定 (event, feeling, action) 三元组（对齐 journal_fields）。
 * 新条目直接取字段；旧条目仅含 text（三句 "\n" 连接），按行拆 3 段并剔除旧占位提示语。
 */
export function journalFields(entry: JournalEntry): [string, string, string] {
  if (entry.text === undefined) {
    return [entry.event ?? "", entry.feeling ?? "", entry.action ?? ""];
  }
  const placeholders = new Set([
    "（今天让你有情绪的一件事）",
    "（给这个感受起个名字）",
    "（下一步的小行动，可选）",
  ]);
  const lines = (entry.text ?? "").split("\n");
  const parts: string[] = [];
  for (const ln of lines.slice(0, 3)) {
    const s = ln.trim();
    parts.push(placeholders.has(s) ? "" : s);
  }
  while (parts.length < 3) parts.push("");
  return [parts[0], parts[1], parts[2]];
}

// ---------------------------------------------------------------------------
// 呼吸引导模式（参数以 pages_tool.py BreathingDialog 各 mode 为准，冻结）
// ---------------------------------------------------------------------------

export type BreathMode = "478" | "box" | "sigh" | "belly";

export interface BreathPhase {
  /** 阶段名（吸气/屏息/呼气/快吸/补吸/长呼） */
  name: string;
  /** 时长（秒） */
  dur: number;
}

export interface BreathModeSpec {
  title: string;
  desc: string;
  phases: BreathPhase[];
  rounds: number;
}

export const BREATH_MODES: Record<BreathMode, BreathModeSpec> = {
  "478": {
    title: "4-7-8 呼吸法",
    desc: "吸气 4 秒 · 屏住 7 秒 · 呼气 8 秒 · 循环 3 轮",
    phases: [
      { name: "吸气", dur: 4 },
      { name: "屏息", dur: 7 },
      { name: "呼气", dur: 8 },
    ],
    rounds: 3,
  },
  box: {
    title: "盒式呼吸",
    desc: "吸气 4 秒 · 屏住 4 秒 · 呼气 4 秒 · 屏住 4 秒 · 循环 4 轮",
    phases: [
      { name: "吸气", dur: 4 },
      { name: "屏息", dur: 4 },
      { name: "呼气", dur: 4 },
      { name: "屏息", dur: 4 },
    ],
    rounds: 4,
  },
  sigh: {
    title: "生理性叹息",
    desc: "连吸两口气 · 再缓慢深长呼气 · 循环 3 轮",
    phases: [
      { name: "快吸", dur: 2 },
      { name: "补吸", dur: 2 },
      { name: "长呼", dur: 6 },
    ],
    rounds: 3,
  },
  belly: {
    title: "腹式呼吸",
    desc: "吸气 4 秒 · 屏住 2 秒 · 呼气 6 秒 · 循环 5 轮",
    phases: [
      { name: "吸气", dur: 4 },
      { name: "屏息", dur: 2 },
      { name: "呼气", dur: 6 },
    ],
    rounds: 5,
  },
};

/** toolkit.json action 字段 → 呼吸模式（腹式无 action，由呼吸训练卡直接发起） */
export function breathModeFromAction(action: BreathAction): BreathMode | null {
  switch (action) {
    case "breath_478":
      return "478";
    case "breath_box":
      return "box";
    case "breath_sigh":
      return "sigh";
    default:
      return null;
  }
}

/** 展开 (轮次, 阶段) 序列（对齐 BreathingDialog.plan） */
export function buildBreathPlan(spec: BreathModeSpec): { round: number; phase: BreathPhase }[] {
  const plan: { round: number; phase: BreathPhase }[] = [];
  for (let r = 1; r <= spec.rounds; r++) {
    for (const phase of spec.phases) plan.push({ round: r, phase });
  }
  return plan;
}
