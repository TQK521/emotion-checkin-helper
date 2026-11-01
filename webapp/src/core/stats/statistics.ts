/**
 * statistics.ts —— 统计纯函数（无副作用，可注入日期便于测试）
 * 口径对齐 Python data_store.py / pages_record.py / pages_home.py。
 */
import type { CheckinData, CheckinRecord } from "@/core/domain";
import { toDateStr, monthPrefixOf, mondayOf, dayDiff, todayStr } from "@/shared/lib/date";

function toIso(d: Date): string {
  return toDateStr(d);
}

/** 某日期的全部记录 */
export function recordsOnDate(data: CheckinData, dateStr: string): CheckinRecord[] {
  return data.records.filter((r) => r.date === dateStr);
}

/** 今天的记录数（对齐 records_today） */
export function todayCount(data: CheckinData, today?: string): number {
  const t = today ?? todayStr();
  return recordsOnDate(data, t).length;
}

/** 累计记录数（统计卡 total） */
export function totalCount(data: CheckinData): number {
  return data.records.length;
}

/** 本月有记录的天数（统计卡 month_days，date 前缀 YYYY-MM 去重） */
export function monthDays(data: CheckinData, prefix?: string): number {
  const p = prefix ?? monthPrefixOf(todayStr());
  return new Set(data.records.filter((r) => r.date.startsWith(p)).map((r) => r.date)).size;
}

/**
 * 连续打卡天数：有记录的天数里，从 end（默认今天）往前连续的天数。
 * 对齐 calc_streak：dates 集合 + 逐日向前。
 */
export function calcStreak(data: CheckinData, end?: string): number {
  const e = end ?? todayStr();
  const dates = new Set(data.records.map((r) => r.date));
  let s = 0;
  let d = new Date(`${e}T12:00:00`);
  const oneDay = 86_400_000;
  while (dates.has(toIso(d))) {
    s += 1;
    d = new Date(d.getTime() - oneDay);
  }
  return s;
}

/** 今日一课：从开始打卡那天起按章节数循环（对齐 chapter_of_today） */
export function chapterOfToday(data: CheckinData, chapterCount: number, today?: string): number {
  const t = today ?? todayStr();
  if (data.start_date) {
    const days = dayDiff(data.start_date, t);
    if (Number.isFinite(days) && chapterCount > 0) return ((days % chapterCount) + chapterCount) % chapterCount;
  }
  return 0;
}

/** 时段问候（对齐 greeting） */
export function greeting(hour?: number): string {
  const h = hour ?? new Date().getHours();
  if (h < 6) return "夜深了";
  if (h < 11) return "早上好";
  if (h < 14) return "中午好";
  if (h < 18) return "下午好";
  return "晚上好";
}

/** 记录情绪字段 → 可读文本（兼容新旧，对齐 fmt_emotions） */
export function fmtEmotions(rec: CheckinRecord): string {
  if (!Array.isArray(rec.emotions)) {
    const e = (rec as unknown as { emotion?: string }).emotion;
    return e ? e : "";
  }
  return rec.emotions.join("、");
}

/** 本周（周一至今）的记录（对齐 pages_record 的 week_records） */
export function weekRecords(data: CheckinData, today?: string): CheckinRecord[] {
  const t = today ?? todayStr();
  const monday = mondayOf(t);
  return data.records.filter((r) => r.date >= monday);
}

/** 按字段聚合计数（Counter） */
export function countBy(records: CheckinRecord[], key: "emotions" | "scene"): Map<string, number> {
  const counter = new Map<string, number>();
  for (const r of records) {
    if (key === "emotions") {
      for (const e of r.emotions ?? []) counter.set(e, (counter.get(e) ?? 0) + 1);
    } else {
      const sc = r.scene;
      if (sc) counter.set(sc, (counter.get(sc) ?? 0) + 1);
    }
  }
  return counter;
}

/** 本周情绪频次 topN（对齐 most_common） */
export function topEmotions(data: CheckinData, n = 5, today?: string): [string, number][] {
  const counter = countBy(weekRecords(data, today), "emotions");
  return [...counter.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
}

/** 本周场景频次（对齐 scene_counter） */
export function sceneCounts(data: CheckinData, today?: string): Map<string, number> {
  return countBy(weekRecords(data, today), "scene");
}

/** 某月有记录的日期集合（日历画点，对齐 pages_record 的 _draw_calendar） */
export function calendarDates(data: CheckinData, year: number, month: number): Set<string> {
  const prefix = `${year}-${String(month).padStart(2, "0")}`;
  return new Set(data.records.filter((r) => r.date.startsWith(prefix)).map((r) => r.date));
}

/** 全部可选情绪词 = 内置 + 自定义（对齐 all_emotions；内置词由调用方传入） */
export function allEmotions(data: CheckinData, builtin: readonly string[]): string[] {
  const words = [...builtin];
  for (const e of data.custom_emotions ?? []) {
    const w = typeof e === "string" ? e : e.word;
    if (w && !words.includes(w)) words.push(w);
  }
  return words;
}
