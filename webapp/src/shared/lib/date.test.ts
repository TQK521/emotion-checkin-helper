/**
 * date.test.ts —— 日期工具段门
 */
import { describe, expect, it } from "vitest";
import {
  dayDiff,
  mondayOf,
  monthDayWeekday,
  monthPrefixOf,
  parseDate,
  todayStr,
  weekdayName,
} from "./date";

describe("todayStr / parseDate", () => {
  it("格式化固定日期", () => {
    expect(todayStr(new Date(2026, 10, 1, 9, 30))).toBe("2026-11-01");
  });

  it("parseDate 非法输入返回 null", () => {
    expect(parseDate("2026-13-40")).toBeNull();
    expect(parseDate("2026-11-01T00:00:00")).toBeNull();
    expect(parseDate("abc")).toBeNull();
  });

  it("parseDate 合法日期可往返", () => {
    expect(todayStr(parseDate("2026-11-01")!)).toBe("2026-11-01");
  });
});

describe("weekdayName / monthDayWeekday", () => {
  it("2026-11-01 是星期日", () => {
    expect(weekdayName(new Date(2026, 10, 1))).toBe("星期日");
    expect(monthDayWeekday("2026-11-01")).toBe("11月1日 星期日");
  });

  it("2026-10-26 是星期一", () => {
    expect(weekdayName(new Date(2026, 9, 26))).toBe("星期一");
  });
});

describe("mondayOf / monthPrefixOf / dayDiff", () => {
  it("周日的本周一是 5 天前", () => {
    expect(mondayOf("2026-11-01")).toBe("2026-10-26");
  });

  it("周一本周一是当天", () => {
    expect(mondayOf("2026-10-26")).toBe("2026-10-26");
  });

  it("月前缀", () => {
    expect(monthPrefixOf("2026-11-01")).toBe("2026-11");
  });

  it("dayDiff 天数差", () => {
    expect(dayDiff("2026-10-01", "2026-11-01")).toBe(31);
    expect(dayDiff("2026-11-01", "2026-10-01")).toBe(-31);
  });
});
