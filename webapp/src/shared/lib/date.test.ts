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

describe("日期边界补丁（2026-11-02 分支覆盖）", () => {
  it("parseDate 越界进位回读校验：2026-02-30 非法返回 null", () => {
    expect(parseDate("2026-02-30")).toBeNull();
  });

  it("parseDate 闰年 2024-02-29 合法可往返", () => {
    expect(todayStr(parseDate("2024-02-29")!)).toBe("2024-02-29");
  });

  it("monthDayWeekday 非法输入原样返回", () => {
    expect(monthDayWeekday("abc")).toBe("abc");
  });

  it("mondayOf 非法输入原样返回", () => {
    expect(mondayOf("abc")).toBe("abc");
  });

  it("monthPrefixOf 短字符串原样返回", () => {
    expect(monthPrefixOf("2026")).toBe("2026");
  });

  it("dayDiff 非法输入返回 NaN", () => {
    expect(dayDiff("abc", "2026-11-01")).toBeNaN();
    expect(dayDiff("2026-11-01", "abc")).toBeNaN();
  });

  it("dayDiff 跨闰年：2024-02-28 → 2024-03-01 为 2 天", () => {
    expect(dayDiff("2024-02-28", "2024-03-01")).toBe(2);
  });

  it("mondayOf 跨年：2026-01-01（周四）本周一为 2025-12-29", () => {
    expect(mondayOf("2026-01-01")).toBe("2025-12-29");
  });
});
