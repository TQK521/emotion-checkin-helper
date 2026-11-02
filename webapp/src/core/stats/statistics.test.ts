/**
 * statistics.test.ts —— 统计纯函数段门（口径对齐 Python，断言可失败）
 */
import { describe, expect, it } from "vitest";
import type { CheckinData } from "@/core/domain";
import {
  allEmotions,
  calcStreak,
  calendarDates,
  chapterOfToday,
  fmtEmotions,
  greeting,
  monthDays,
  recordsOnDate,
  sceneCounts,
  todayCount,
  topEmotions,
  weekRecords,
} from "./statistics";

/** 构造一条记录 */
function rec(date: string, emotions: string[] = [], scene = ""): CheckinData["records"][number] {
  return { ts: `${date} 08:00:00`, date, time: "08:00", emotions, action: "", scene, intensity: 3 };
}

function data(records: ReturnType<typeof rec>[], start_date: string | null = null, best_streak = 0): CheckinData {
  return { start_date, records, best_streak, journal: [], custom_emotions: [] };
}

describe("calcStreak 连续天数", () => {
  it("空记录为 0", () => {
    expect(calcStreak(data([]), "2026-11-01")).toBe(0);
  });

  it("仅今天有记录为 1", () => {
    expect(calcStreak(data([rec("2026-11-01")]), "2026-11-01")).toBe(1);
  });

  it("连续三天为 3", () => {
    const r = [rec("2026-10-30"), rec("2026-10-31"), rec("2026-11-01")];
    expect(calcStreak(data(r), "2026-11-01")).toBe(3);
  });

  it("中间断档只数连续段（今天起往前）", () => {
    const r = [rec("2026-10-29"), rec("2026-10-31"), rec("2026-11-01")];
    expect(calcStreak(data(r), "2026-11-01")).toBe(2);
  });

  it("跨月连续（10-31 与 11-01）", () => {
    const r = [rec("2026-10-31"), rec("2026-11-01")];
    expect(calcStreak(data(r), "2026-11-01")).toBe(2);
  });

  it("同一天多条只算一天", () => {
    const r = [rec("2026-11-01", ["开心"]), rec("2026-11-01", ["平静"])];
    expect(calcStreak(data(r), "2026-11-01")).toBe(1);
  });
});

describe("今日/累计/本月统计", () => {
  const d = data([
    rec("2026-11-01", ["开心"], "学习"),
    rec("2026-11-01", ["平静"]),
    rec("2026-10-31"),
    rec("2026-10-15"),
  ]);

  it("todayCount 只数今天", () => {
    expect(todayCount(d, "2026-11-01")).toBe(2);
    expect(todayCount(d, "2026-11-02")).toBe(0);
  });

  it("recordsOnDate 过滤", () => {
    expect(recordsOnDate(d, "2026-11-01")).toHaveLength(2);
  });

  it("monthDays 本月去重天数", () => {
    expect(monthDays(d, "2026-11")).toBe(1);
    expect(monthDays(d, "2026-10")).toBe(2);
  });

  it("累计 = records.length", () => {
    expect(d.records.length).toBe(4);
  });
});

describe("本周与 top 情绪", () => {
  it("weekRecords 从本周一至今", () => {
    // 2026-11-01 是周日，本周一为 2026-10-26
    const d = data([
      rec("2026-10-25", ["开心"]), // 上周日，排除
      rec("2026-10-26", ["平静"]),
      rec("2026-11-01", ["开心"]),
    ]);
    const wk = weekRecords(d, "2026-11-01");
    expect(wk).toHaveLength(2);
    expect(wk[0].date).toBe("2026-10-26");
  });

  it("topEmotions 频次 top5 且按频次降序", () => {
    const d = data([
      rec("2026-10-26", ["开心", "平静"]),
      rec("2026-10-27", ["开心"]),
      rec("2026-10-28", ["焦虑", "焦虑"]),
      rec("2026-10-29", ["平静"]),
      rec("2026-10-30", ["疲惫"]),
      rec("2026-10-31", ["烦躁"]),
    ]);
    const top = topEmotions(d, 5, "2026-11-01");
    expect(top[0]).toEqual(["开心", 2]);
    expect(top).toHaveLength(5);
    // 降序断言
    for (let i = 1; i < top.length; i++) expect(top[i][1]).toBeLessThanOrEqual(top[i - 1][1]);
  });

  it("本周无记录返回空数组", () => {
    expect(topEmotions(data([rec("2026-10-01")]), 5, "2026-11-01")).toEqual([]);
  });
});

describe("日历聚合", () => {
  it("calendarDates 只含当月有记录的日期", () => {
    const d = data([
      rec("2026-11-01"),
      rec("2026-11-15"),
      rec("2026-10-31"),
    ]);
    const set = calendarDates(d, 2026, 11);
    expect(set.has("2026-11-01")).toBe(true);
    expect(set.has("2026-11-15")).toBe(true);
    expect(set.has("2026-10-31")).toBe(false);
    expect(set.size).toBe(2);
  });
});

describe("今日一课与问候", () => {
  it("chapterOfToday 从 start_date 起按 70 课循环", () => {
    const d = data([], "2026-10-01");
    // 10-01 起 0 天 → 0；11-01 起 31 天 → 31
    expect(chapterOfToday(d, 70, "2026-10-01")).toBe(0);
    expect(chapterOfToday(d, 70, "2026-11-01")).toBe(31);
    // 跨过 70 天循环：2026-12-09 距 10-01 为 69 天 → 69；2026-12-10 为 70 天 → 0
    expect(chapterOfToday(d, 70, "2026-12-09")).toBe(69);
    expect(chapterOfToday(d, 70, "2026-12-10")).toBe(0);
  });

  it("chapterOfToday 无 start_date 返回 0", () => {
    expect(chapterOfToday(data([]), 70, "2026-11-01")).toBe(0);
  });

  it("greeting 时段分界", () => {
    expect(greeting(3)).toBe("夜深了");
    expect(greeting(8)).toBe("早上好");
    expect(greeting(12)).toBe("中午好");
    expect(greeting(16)).toBe("下午好");
    expect(greeting(20)).toBe("晚上好");
  });
});

describe("fmtEmotions", () => {
  it("列表情绪用顿号连接", () => {
    expect(fmtEmotions(rec("2026-11-01", ["开心", "平静"]))).toBe("开心、平静");
  });

  it("空情绪返回空串", () => {
    expect(fmtEmotions(rec("2026-11-01"))).toBe("");
  });
});

describe("统计边界补丁（2026-11-02 分支覆盖）", () => {
  it("calcStreak：end 当天无记录返回 0（前一天有也不跨）", () => {
    const r = [rec("2026-10-31"), rec("2026-10-30")];
    expect(calcStreak(data(r), "2026-11-01")).toBe(0);
  });

  it("monthDays：无匹配月份返回 0", () => {
    expect(monthDays(data([rec("2026-10-01")]), "2026-11")).toBe(0);
  });

  it("recordsOnDate：无匹配日期返回空数组", () => {
    expect(recordsOnDate(data([rec("2026-11-01")]), "2026-11-02")).toEqual([]);
  });

  it("chapterOfToday：chapterCount<=0 返回 0", () => {
    expect(chapterOfToday(data([], "2026-10-01"), 0, "2026-11-01")).toBe(0);
  });

  it("chapterOfToday：start_date 在未来（days 为负）仍按模循环", () => {
    // start=2026-11-01, today=2026-10-01：-31 天 → ((-31 % 70) + 70) % 70 = 39
    expect(chapterOfToday(data([], "2026-11-01"), 70, "2026-10-01")).toBe(39);
  });

  it("fmtEmotions：旧字段 emotion（非数组）兼容", () => {
    const old = { ts: "2026-11-01 08:00:00", date: "2026-11-01", time: "08:00", emotions: undefined, action: "", scene: "", intensity: 3, emotion: "开心" } as unknown as CheckinData["records"][number];
    expect(fmtEmotions(old)).toBe("开心");
    const empty = { ...old, emotion: undefined };
    expect(fmtEmotions(empty)).toBe("");
  });

  it("allEmotions：内置 + 自定义对象形式 + 去重", () => {
    const d = data([]);
    const withCustom = { ...d, custom_emotions: [{ word: "惆怅" }, "平静", "惆怅"] } as CheckinData;
    expect(allEmotions(withCustom, ["开心", "平静"])).toEqual(["开心", "平静", "惆怅"]);
  });

  it("sceneCounts：空 scene 被跳过", () => {
    const d = data([rec("2026-10-26", ["开心"], "学习"), rec("2026-10-27")]);
    const counts = sceneCounts(d, "2026-11-01");
    expect(counts.get("学习")).toBe(1);
    expect(counts.has("")).toBe(false);
  });
});
