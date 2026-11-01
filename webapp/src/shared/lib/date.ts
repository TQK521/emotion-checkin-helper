/**
 * date.ts —— 日期工具（对齐 Python datetime 本地时区语义）
 * 日期一律用 "YYYY-MM-DD" 字符串（ISO 字典序 = 时间序，可直接比较）。
 */

/** 补零两位 */
function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/** 本地日期 → "YYYY-MM-DD" */
export function toDateStr(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

/** 今天的日期 "YYYY-MM-DD" */
export function todayStr(now: Date = new Date()): string {
  return toDateStr(now);
}

/** 当前完整时间戳 "YYYY-MM-DD HH:mm:ss"（对齐 make_record 的 ts） */
export function nowTs(now: Date = new Date()): string {
  return `${toDateStr(now)} ${pad2(now.getHours())}:${pad2(now.getMinutes())}:${pad2(now.getSeconds())}`;
}

/** 当前 "HH:mm"（对齐 make_record 的 time） */
export function nowTime(now: Date = new Date()): string {
  return `${pad2(now.getHours())}:${pad2(now.getMinutes())}`;
}

/** 中文星期名（对齐 Python %A） */
export function weekdayName(now: Date = new Date()): string {
  const names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"];
  // getDay(): 0=周日 … 6=周六；Python weekday(): 0=周一 … 6=周日
  return names[(now.getDay() + 6) % 7];
}

/** 日期卡片标题，如 "10月31日 星期五"（对齐首页问候卡） */
export function monthDayWeekday(dateStr: string): string {
  const d = parseDate(dateStr);
  if (!d) return dateStr;
  return `${d.getMonth() + 1}月${d.getDate()}日 ${weekdayName(d)}`;
}

/** 解析 "YYYY-MM-DD" 为本地 Date；非法返回 null（JS Date 会越界进位，须校验回读） */
export function parseDate(dateStr: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  const dt = new Date(y, mo - 1, d);
  if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
  return dt;
}

/** 月前缀 "YYYY-MM"（对齐统计卡本月记录口径） */
export function monthPrefixOf(dateStr: string): string {
  return dateStr.length >= 7 ? dateStr.slice(0, 7) : dateStr;
}

/** 本周一（对齐 pages_record 的 monday = today - weekday） */
export function mondayOf(dateStr: string): string {
  const d = parseDate(dateStr);
  if (!d) return dateStr;
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return toDateStr(d);
}

/** 天数差 b - a（对齐 Python (end - start).days） */
export function dayDiff(a: string, b: string): number {
  const da = parseDate(a);
  const db = parseDate(b);
  if (!da || !db) return NaN;
  return Math.round((db.getTime() - da.getTime()) / 86_400_000);
}
