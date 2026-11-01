/**
 * importer.ts —— 旧数据导入/迁移（对应 Python migrate_old_data + journal_fields）
 * 兼容：旧 checkins 字典 → records；旧 journal text → 三字段；缺字段兜底。
 */
import type { CheckinData, CheckinRecord, JournalEntry, CustomEmotion } from "@/core/domain";

/** 旧版单日记录（每天一次；可能只有 emotion 单字段） */
export interface LegacyCheckin {
  emotions?: unknown;
  emotion?: unknown;
  action?: string;
}

export interface LegacyData {
  checkins?: Record<string, LegacyCheckin>;
  start_date?: string | null;
  best_streak?: number;
  journal?: JournalEntry[];
  custom_emotions?: CustomEmotion[];
}

/** 兼容读取旧记录的情绪列表 */
function readEmotions(rec: LegacyCheckin): string[] {
  if (Array.isArray(rec.emotions)) return rec.emotions.filter((e): e is string => typeof e === "string");
  const one = rec.emotion;
  return typeof one === "string" && one ? [one] : [];
}

/**
 * 把任意旧数据规范化为当前契约。
 * 幂等：已是 records 格式的（含部分字段缺失）只做 setdefault 兜底，不重复迁移。
 */
export function migrateOldData(raw: unknown): CheckinData {
  if (typeof raw !== "object" || raw === null) return createEmpty();
  const data = raw as Record<string, unknown> & LegacyData;

  // 旧版"每天一次"：checkins 字典 → records 列表
  if (!Array.isArray(data.records) && typeof data.checkins === "object" && data.checkins !== null) {
    const records: CheckinRecord[] = [];
    for (const [d, rec] of Object.entries(data.checkins).sort(([a], [b]) => (a < b ? -1 : 1))) {
      records.push({
        ts: `${d}T00:00:00`,
        date: d,
        time: "",
        emotions: readEmotions(rec),
        action: typeof rec.action === "string" ? rec.action : "",
      });
    }
    data.records = records;
    delete data.checkins;
  }

  return {
    start_date: typeof data.start_date === "string" ? data.start_date : null,
    records: Array.isArray(data.records) ? data.records : [],
    best_streak: typeof data.best_streak === "number" ? data.best_streak : 0,
    journal: Array.isArray(data.journal) ? data.journal : [],
    custom_emotions: Array.isArray(data.custom_emotions) ? data.custom_emotions : [],
  };
}

/** 旧 journal 占位提示语（命中整段即置空，对齐 Python journal_fields） */
export const JOURNAL_PLACEHOLDERS = [
  "（今天让你有情绪的一件事）",
  "（给这个感受起个名字）",
  "（下一步的小行动，可选）",
] as const;

/** 兼容新旧 journal 条目，返回恒定 (event, feeling, action) 三元组 */
export function journalFields(entry: JournalEntry): [string, string, string] {
  if (typeof entry.text !== "string") {
    return [entry.event ?? "", entry.feeling ?? "", entry.action ?? ""];
  }
  const parts = entry.text
    .split("\n")
    .slice(0, 3)
    .map((ln) => {
      const t = ln.trim();
      return (JOURNAL_PLACEHOLDERS as readonly string[]).includes(t) ? "" : t;
    });
  while (parts.length < 3) parts.push("");
  return [parts[0], parts[1], parts[2]];
}

function createEmpty(): CheckinData {
  return { start_date: null, records: [], best_streak: 0, journal: [], custom_emotions: [] };
}
