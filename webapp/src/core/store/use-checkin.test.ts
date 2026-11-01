/**
 * use-checkin.test.ts —— 核心 CheckinStore 段门（InMemory 适配器隔离，断言可失败）
 */
import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useCheckinStore } from "./use-checkin";
import { InMemoryStorageAdapter } from "@/services/memory-storage.adapter";
import { todayStr } from "@/shared/lib/date";
import type { CheckinData } from "@/core/domain";

function withRecords(records: CheckinData["records"]): CheckinData {
  return { start_date: null, records, best_streak: 0, journal: [], custom_emotions: [] };
}

describe("useCheckinStore 核心写入", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("addRecord append 尾部并生成完整契约字段", async () => {
    const store = useCheckinStore();
    store.setStorage(new InMemoryStorageAdapter(withRecords([])));
    await store.load();

    const rec = await store.addRecord({ emotions: ["开心", "平静"], action: "散步", scene: "学习", intensity: 5 });

    expect(rec.ts).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/);
    expect(rec.date).toBe(todayStr());
    expect(rec.time).toMatch(/^\d{2}:\d{2}$/);
    expect(rec.emotions).toEqual(["开心", "平静"]);
    expect(rec.scene).toBe("学习");
    expect(rec.intensity).toBe(5);

    expect(store.data.records).toHaveLength(1);
    // pinia state 是 reactive 代理，引用不相等但内容一致
    expect(store.data.records[0]).toStrictEqual(rec);
    expect(store.lastRecord).toStrictEqual(rec);
    expect(store.data.start_date).toBe(todayStr());
  });

  it("addRecord 更新 best_streak 与今日计数 getter", async () => {
    const store = useCheckinStore();
    const yesterday = new Date(Date.now() - 86_400_000);
    const y = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;
    store.setStorage(new InMemoryStorageAdapter(withRecords([{ ts: `${y} 08:00:00`, date: y, time: "08:00", emotions: ["平静"], action: "" }])));
    await store.load();

    await store.addRecord({ emotions: ["开心"], action: "" });
    expect(store.data.best_streak).toBe(2); // 昨天+今天连续
    expect(store.todayCount).toBe(1);
    expect(store.totalCount).toBe(2);
  });

  it("undoLast pop 尾部并恢复 lastRecord 状态", async () => {
    const store = useCheckinStore();
    store.setStorage(new InMemoryStorageAdapter(withRecords([])));
    await store.load();

    await store.addRecord({ emotions: ["开心"], action: "a" });
    const removed = await store.undoLast();
    expect(removed?.emotions).toEqual(["开心"]);
    expect(store.data.records).toHaveLength(0);
    expect(store.lastRecord).toBeNull();
    // 再撤销返回 null（无待撤销记录）
    expect(await store.undoLast()).toBeNull();
  });

  it("undoLast 仅当最后一条仍是刚记的（外部改动后不撤销）", async () => {
    const store = useCheckinStore();
    store.setStorage(new InMemoryStorageAdapter(withRecords([])));
    await store.load();

    await store.addRecord({ emotions: ["开心"], action: "" });
    // 模拟外部写入一条新记录（例如另一窗口），最后一条不再是 lastRecord
    store.data.records.push({ ts: "2026-11-01 09:00:00", date: todayStr(), time: "09:00", emotions: ["烦躁"], action: "" });
    expect(await store.undoLast()).toBeNull();
    expect(store.data.records).toHaveLength(2);
  });

  it("addCustomEmotion 去重与空词拒绝", async () => {
    const store = useCheckinStore();
    store.setStorage(new InMemoryStorageAdapter(withRecords([])));
    await store.load();

    expect(await store.addCustomEmotion("摆烂")).toBe(true);
    expect(await store.addCustomEmotion("摆烂")).toBe(false); // 重复拒绝
    expect(await store.addCustomEmotion("   ")).toBe(false); // 空白拒绝
    expect(store.data.custom_emotions).toEqual([{ word: "摆烂", gloss: "" }]);
    expect(await store.addCustomEmotion("心累", "就是不想动")).toBe(true);
  });

  it("load 迁移旧 checkins 数据", async () => {
    const store = useCheckinStore();
    store.setStorage(
      new InMemoryStorageAdapter({
        start_date: "2026-10-01",
        best_streak: 1,
        checkins: { "2026-10-01": { emotions: ["开心"], action: "散步" } },
      } as unknown as CheckinData),
    );
    await store.load();
    expect(store.data.records).toHaveLength(1);
    expect(store.data.records[0].ts).toBe("2026-10-01T00:00:00");
    expect(store.data.start_date).toBe("2026-10-01");
  });

  it("load 后 save 持久化到存储可回读", async () => {
    const adapter = new InMemoryStorageAdapter(withRecords([]));
    const store = useCheckinStore();
    store.setStorage(adapter);
    await store.load();
    await store.addRecord({ emotions: ["开心"], action: "" });

    const persisted = await adapter.load();
    expect(persisted.records).toHaveLength(1);
  });
});
