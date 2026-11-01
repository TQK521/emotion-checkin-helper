/**
 * RecordView.test.ts —— 记录洞察域组件测试（@vue/test-utils + jsdom）
 * 断言口径对齐旧版 pages_record.py；数据一律 InMemory 注入，不碰真实存储。
 */
import { afterEach, describe, expect, it } from "vitest";
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import RecordView from "./RecordView.vue";
import { useCheckinStore } from "@/core/store/use-checkin";
import { InMemoryStorageAdapter } from "@/services/memory-storage.adapter";
import type { CheckinData, CheckinRecord } from "@/core/domain";
import { mondayOf, todayStr } from "@/shared/lib/date";

// ── fixture 构造 ──
function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function dateStrOf(d: Date): string {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

/** base 日期 +/- n 天 */
function addDays(base: string, n: number): string {
  const d = new Date(`${base}T12:00:00`);
  d.setDate(d.getDate() + n);
  return dateStrOf(d);
}

function mkRec(
  date: string,
  opts: Partial<{
    time: string;
    ts: string;
    emotions: string[];
    action: string;
    scene: string;
    intensity: number;
  }> = {},
): CheckinRecord {
  return {
    ts: opts.ts ?? `${date} 08:00:00`,
    date,
    time: opts.time ?? "08:00",
    emotions: opts.emotions ?? [],
    action: opts.action ?? "",
    scene: opts.scene ?? "",
    intensity: opts.intensity ?? 3,
  };
}

// ── 挂载辅助 ──
let wrapper: VueWrapper | null = null;

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  document.body.innerHTML = "";
});

async function mountView(records: CheckinRecord[]): Promise<{
  store: ReturnType<typeof useCheckinStore>;
  adapter: InMemoryStorageAdapter;
}> {
  setActivePinia(createPinia());
  const store = useCheckinStore();
  const data: CheckinData = {
    start_date: null,
    records,
    best_streak: 0,
    journal: [],
    custom_emotions: [],
  };
  const adapter = new InMemoryStorageAdapter(data);
  store.setStorage(adapter);
  await store.load();
  wrapper = mount(RecordView, { attachTo: document.body });
  await flushPromises();
  return { store, adapter };
}

function q(sel: string): Element | null {
  return document.body.querySelector(sel);
}

function qAll(sel: string): Element[] {
  return [...document.body.querySelectorAll(sel)];
}

function text(sel: string): string {
  return q(sel)?.textContent?.trim() ?? "";
}

/** 当前日历视图中 data-recorded="true" 的日期集合 */
function actualRecorded(): Set<string> {
  return new Set(
    qAll('.cal-cell[data-recorded="true"]')
      .map((e) => e.getAttribute("data-date"))
      .filter((v): v is string => !!v),
  );
}

// ── 用例 ──
describe("统计三卡", () => {
  it("累计 / 今日 / 本月天数 与注入数据一致", async () => {
    const t = todayStr();
    const y = addDays(t, -1);
    const recs = [
      mkRec(t, { emotions: ["平静"] }),
      mkRec(t, { emotions: ["开心"] }),
      mkRec(t, { emotions: ["焦虑"] }),
      mkRec(y, { emotions: ["疲惫"] }),
    ];
    const { store } = await mountView(recs);

    expect(text('[data-test="stat-total"]')).toBe("4");
    expect(text('[data-test="stat-today"]')).toBe("3");
    // 本月天数 = 本月去重日期数（动态算，跨月也成立）
    const prefix = t.slice(0, 7);
    const expectedMonthDays = new Set(
      recs.filter((r) => r.date.startsWith(prefix)).map((r) => r.date),
    ).size;
    expect(text('[data-test="stat-month"]')).toBe(String(expectedMonthDays));
    // 与 store getter 一致
    expect(store.totalCount).toBe(4);
    expect(store.todayCount).toBe(3);
  });
});

describe("日历", () => {
  it("画点集合正确、翻月、回今天、当天记录与空态", async () => {
    const t = todayStr();
    const old = addDays(t, -60); // 保证跨月
    const fixture = [mkRec(t, { emotions: ["平静"] }), mkRec(old, { emotions: ["疲惫"] })];
    await mountView(fixture);

    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth() + 1;
    expect(text('[data-test="cal-title"]')).toBe(`${y} 年 ${m} 月`);

    const expectedFor = (year: number, month: number): Set<string> => {
      const p = `${year}-${pad2(month)}`;
      return new Set(fixture.filter((r) => r.date.startsWith(p)).map((r) => r.date));
    };

    // 当前月画点集合 = fixture 中本月日期（不多不少）
    expect(actualRecorded()).toEqual(expectedFor(y, m));
    // 今天的格子必然有记录点
    expect(q(`.cal-cell[data-date="${t}"]`)?.getAttribute("data-recorded")).toBe("true");
    // 初始选中今天 → 当天详情显示
    expect(text('[data-test="day-detail"]')).toContain("共 1 次");

    // 翻上月：标题正确、画点集合切换、今天格子离开视图
    await wrapper!.find('[data-test="cal-prev"]').trigger("click");
    const prevMonthNum = m === 1 ? 12 : m - 1;
    const prevYear = m === 1 ? y - 1 : y;
    expect(text('[data-test="cal-title"]')).toBe(`${prevYear} 年 ${prevMonthNum} 月`);
    expect(actualRecorded()).toEqual(expectedFor(prevYear, prevMonthNum));
    expect(q(`.cal-cell[data-date="${t}"]`)).toBeNull();

    // 上月视图（均为过去日期）：点一个无记录日期 → 空态"没有记录"
    const unrec = wrapper!.findAll('.cal-cell[data-recorded="false"]')[0];
    expect(unrec).toBeTruthy();
    await unrec.trigger("click");
    await flushPromises();
    expect(text('[data-test="day-detail"]')).toContain("没有记录");

    // 回今天
    await wrapper!.find('[data-test="cal-today"]').trigger("click");
    expect(text('[data-test="cal-title"]')).toBe(`${y} 年 ${m} 月`);
    expect(q(`.cal-cell[data-date="${t}"]`)).not.toBeNull();
  });
});

describe("本周情绪横条", () => {
  it("top5 降序、比例条按最高频归一", async () => {
    const t = todayStr();
    const mon = mondayOf(t);
    const d1 = addDays(mon, 1);
    const d2 = addDays(mon, 2);
    const lastWeek = addDays(mon, -2); // 上周，应被排除
    await mountView([
      mkRec(mon, { emotions: ["焦虑", "焦虑"], scene: "学习" }),
      mkRec(d1, { emotions: ["焦虑"], scene: "学习" }),
      mkRec(d2, { emotions: ["疲惫", "疲惫"], scene: "工作" }),
      mkRec(lastWeek, { emotions: ["焦虑"] }),
    ]);

    const names = qAll(".emo-name").map((e) => e.textContent?.trim());
    expect(names).toEqual(["焦虑", "疲惫"]);
    const bars = qAll(".emo-bar");
    expect(bars[0].getAttribute("data-count")).toBe("3");
    expect(bars[0].getAttribute("data-pct")).toBe("100"); // 最高频 = 100%
    expect(bars[1].getAttribute("data-count")).toBe("2");
    expect(bars[1].getAttribute("data-pct")).toBe(String(Math.round((2 / 3) * 100))); // 67
    // 上周的焦虑未计入：总条数不是 4
    expect(text('[data-test="stat-total"]')).toBe("4");
  });
});

describe("本周复盘", () => {
  it("top3 / 主要场景 / 肯定语 与预置数据一致", async () => {
    const t = todayStr();
    const mon = mondayOf(t);
    await mountView([
      mkRec(mon, { emotions: ["焦虑"], scene: "学习" }),
      mkRec(addDays(mon, 1), { emotions: ["焦虑"], scene: "学习" }),
      mkRec(addDays(mon, 2), { emotions: ["疲惫"], scene: "工作" }),
    ]);

    expect(text('[data-test="review-top3"]')).toBe("高频情绪：焦虑、疲惫");
    expect(text('[data-test="review-scene"]')).toBe("主要场景：学习");
    expect(text('[data-test="review-affirm"]')).toBe("焦虑说明你在乎，允许自己慢慢来，一步一步走。");
  });

  it("本周无记录时显示兜底文案", async () => {
    const t = todayStr();
    const lastWeek = addDays(mondayOf(t), -3);
    await mountView([mkRec(lastWeek, { emotions: ["焦虑"] })]);

    expect(text('[data-test="review-empty"]')).toContain("这周还没记录");
    expect(qAll(".emo-row")).toHaveLength(0);
  });
});

describe("历史记录区", () => {
  it("默认收起；展开首批 40；loadMore 补齐；按天分组；删除确认→持久化", async () => {
    const t = todayStr();
    const y = addDays(t, -1);
    const fixture: CheckinRecord[] = [];
    for (let i = 0; i < 40; i++) {
      fixture.push(
        mkRec(t, {
          time: `08:${pad2(i)}`,
          ts: `${t} 08:${pad2(i)}:00`,
          emotions: ["平静"],
          scene: "学习",
        }),
      );
    }
    for (let i = 0; i < 5; i++) {
      fixture.push(
        mkRec(y, {
          time: `09:0${i}`,
          ts: `${y} 09:0${i}:00`,
          emotions: ["疲惫"],
          scene: "工作",
          intensity: 4,
        }),
      );
    }
    const { store, adapter } = await mountView(fixture);

    // 默认收起
    expect(q('[data-test="history-section"]')).toBeNull();

    // 展开：首批只渲染 40 条（共 45）
    await wrapper!.find('[data-test="history-toggle"]').trigger("click");
    await flushPromises();
    expect(q('[data-test="history-section"]')).not.toBeNull();
    expect(qAll('[data-test="hist-rec"]')).toHaveLength(40);
    // 首批只渲染今天的 40 条 → 仅 1 个日期头（昨天的 5 条在第二批）
    expect(qAll(".hist-day")).toHaveLength(1);

    // 触底加载函数补齐剩余 5 条
    (wrapper!.vm as unknown as { loadMore: () => void }).loadMore();
    await flushPromises();
    expect(qAll('[data-test="hist-rec"]')).toHaveLength(45);
    // 两批齐全后按天分组 = 2 个日期头（date 降序）
    expect(qAll(".hist-day")).toHaveLength(2);
    expect(qAll(".hist-day")[0].getAttribute("data-date")).toBe(t);

    // 删除：先取消，数据不变（弹窗 Teleport 到 body，用原生 click 触发）
    await wrapper!.find('[data-test="delete-btn"]').trigger("click");
    await flushPromises();
    expect(q('[data-test="confirm-delete"]')).not.toBeNull();
    (q('[data-test="cancel-delete"]') as HTMLElement).click();
    await flushPromises();
    expect(store.data.records).toHaveLength(45);

    // 删除：确认后 records 减一 + InMemory 已持久化
    await wrapper!.find('[data-test="delete-btn"]').trigger("click");
    await flushPromises();
    (q('[data-test="confirm-delete"]') as HTMLElement).click();
    await flushPromises();
    expect(store.data.records).toHaveLength(44);
    expect(text('[data-test="delete-feedback"]')).toContain("已删除");
    const persisted = await adapter.load();
    expect(persisted.records).toHaveLength(44);
  });
});

describe("备份入口", () => {
  it("点击后展示备份结果文案", async () => {
    const t = todayStr();
    await mountView([mkRec(t, { emotions: ["平静"] })]);

    expect(q('[data-test="backup-result"]')).toBeNull();
    await wrapper!.find('[data-test="backup-btn"]').trigger("click");
    await flushPromises();
    expect(text('[data-test="backup-result"]')).toContain("备份完成");
  });
});
