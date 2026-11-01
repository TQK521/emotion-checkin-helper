/**
 * importer.test.ts —— 旧数据导入/迁移段门（断言可失败）
 */
import { describe, expect, it } from "vitest";
import { migrateOldData, journalFields } from "./importer";

describe("migrateOldData 旧 checkins 迁移", () => {
  it("旧每天一次格式转 records（ts 用 T00:00:00、time 空）", () => {
    const migrated = migrateOldData({
      start_date: "2026-10-01",
      best_streak: 3,
      checkins: {
        "2026-10-01": { emotions: ["开心"], action: "散步" },
        "2026-10-02": { emotion: "平静" }, // 单字段兼容
        "2026-10-03": { emotions: "not-a-list", action: "" }, // 非法列表 → 空
      },
    });
    expect(migrated.records).toHaveLength(3);
    expect(migrated.records[0]).toEqual({
      ts: "2026-10-01T00:00:00",
      date: "2026-10-01",
      time: "",
      emotions: ["开心"],
      action: "散步",
    });
    expect(migrated.records[1].emotions).toEqual(["平静"]);
    expect(migrated.records[2].emotions).toEqual([]);
    expect(Object.keys(migrated)).not.toContain("checkins");
  });

  it("已是 records 格式只做 setdefault 兜底不重复迁移", () => {
    const migrated = migrateOldData({
      records: [{ ts: "2026-11-01 08:00:00", date: "2026-11-01", time: "08:00", emotions: ["开心"], action: "" }],
      best_streak: 1,
    });
    expect(migrated.records).toHaveLength(1);
    expect(migrated.best_streak).toBe(1);
    expect(migrated.start_date).toBeNull();
    expect(migrated.custom_emotions).toEqual([]);
  });

  it("完全空数据返回契约空结构", () => {
    const migrated = migrateOldData({});
    expect(migrated).toEqual({
      start_date: null,
      records: [],
      best_streak: 0,
      journal: [],
      custom_emotions: [],
    });
  });

  it("非对象输入返回空结构", () => {
    expect(migrateOldData(null)).toEqual({
      start_date: null,
      records: [],
      best_streak: 0,
      journal: [],
      custom_emotions: [],
    });
  });

  it("records 按日期升序", () => {
    const migrated = migrateOldData({
      checkins: {
        "2026-10-05": { emotion: "烦躁" },
        "2026-10-01": { emotion: "开心" },
      },
    });
    expect(migrated.records.map((r) => r.date)).toEqual(["2026-10-01", "2026-10-05"]);
  });
});

describe("journalFields 新旧兼容", () => {
  it("新结构直接取三字段，缺失兜底空串", () => {
    expect(journalFields({ event: "考试", feeling: "紧张", action: "深呼吸" })).toEqual([
      "考试",
      "紧张",
      "深呼吸",
    ]);
    expect(journalFields({ event: "考试" })).toEqual(["考试", "", ""]);
  });

  it("旧 text 按换行拆 3 段", () => {
    expect(journalFields({ text: "考试没考好\n有点挫败\n明天复习" })).toEqual([
      "考试没考好",
      "有点挫败",
      "明天复习",
    ]);
  });

  it("旧占位提示语命中整段置空", () => {
    expect(journalFields({ text: "（今天让你有情绪的一件事）\n（给这个感受起个名字）\n（下一步的小行动，可选）" })).toEqual(["", "", ""]);
  });

  it("无换行自由文本 → event 原文其余空", () => {
    expect(journalFields({ text: "哈哈哈" })).toEqual(["哈哈哈", "", ""]);
  });

  it("段数不足补齐空串", () => {
    expect(journalFields({ text: "只有一段" })).toEqual(["只有一段", "", ""]);
  });
});
