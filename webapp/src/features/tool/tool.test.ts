/**
 * tool.test.ts —— 工具箱域验收（@vue/test-utils + jsdom + fake timers）
 * 每条断言对应验收清单一项；弹窗 Teleport 到 body，统一从 document.body 查询。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia, type Pinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import ToolView from "./ToolView.vue";
import { InMemoryStorageAdapter } from "@/services/memory-storage.adapter";
import { useCheckinStore } from "@/core/store/use-checkin";
import { todayStr } from "@/shared/lib/date";
import type { CheckinData, JournalEntry } from "@/core/domain";

function emptyData(): CheckinData {
  return { start_date: null, records: [], best_streak: 0, journal: [], custom_emotions: [] };
}

/** 从 document.body 查 Teleport 出的弹窗节点 */
function q(sel: string): HTMLElement | null {
  return document.body.querySelector(sel) as HTMLElement | null;
}

function setup(seedJournal: JournalEntry[] = [], seedCustom: { word: string; gloss?: string }[] = []) {
  const pinia: Pinia = createPinia();
  setActivePinia(pinia);
  const store = useCheckinStore();
  store.setStorage(new InMemoryStorageAdapter(emptyData()));
  // 直接播种 reactive state（UI 域测试不经过 load）
  store.data.journal = [...seedJournal];
  store.data.custom_emotions = [...seedCustom];
  const wrapper = mount(ToolView, { global: { plugins: [pinia] } });
  return { wrapper, store };
}

beforeEach(() => {
  document.body.innerHTML = "";
});

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = "";
});

describe("① 状态分流与推荐卡", () => {
  it("6 态 chips 单选生效；推荐按 time 升序（最短在前）", async () => {
    const { wrapper } = setup();
    const chips = wrapper.findAll('[data-test^="state-chip-"]');
    expect(chips.length).toBe(6); // 失败口径：不是 6 态即错
    expect(wrapper.find('[data-test="state-chip-acute"]').classes()).toContain("active");

    // acute 推荐 keys=[physio_sigh(1分钟), grounding_54321(2-3→2), box_breath(1-2→1)]
    // 升序后：生理性叹息(1) → 盒式呼吸(1) → 接地法(2)
    const acuteNames = wrapper.findAll(".rec-item .rec-name").map((e) => e.text());
    expect(acuteNames).toEqual(["生理性叹息", "盒式呼吸 4-4-4-4", "5-4-3-2-1 接地法"]);

    // 切到「低落没劲」：单选互斥
    await wrapper.find('[data-test="state-chip-low"]').trigger("click");
    expect(wrapper.find('[data-test="state-chip-low"]').classes()).toContain("active");
    expect(wrapper.find('[data-test="state-chip-acute"]').classes()).not.toContain("active");

    // low keys=[behavior_act(15), aerobic(20-30→20), outdoor(10-20→10)] → outdoor, behavior_act, aerobic
    const lowNames = wrapper.findAll(".rec-item .rec-name").map((e) => e.text());
    expect(lowNames).toEqual(["户外自然接触", "行为激活", "有氧运动"]);
  });

  it("推荐卡「立即开始」：非呼吸法展开步骤卡", async () => {
    const { wrapper } = setup();
    // 默认 acute 第一条生理性叹息是呼吸法（开弹窗，不展开步骤）；接地法在列
    const grounding = wrapper.find('[data-test="rec-grounding_54321"]');
    await grounding.find(".btn-primary").trigger("click");
    expect(wrapper.find('[data-test="rec-steps"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="rec-steps"]').text()).toContain("看到 5 样东西");
  });
});

describe("③ 四呼吸引导弹窗", () => {
  it("fake timers：阶段推进/倒计时递减/轮次文案/停止清定时器", async () => {
    vi.useFakeTimers();
    try {
      const { wrapper } = setup();
      await wrapper.find('[data-test="breath-478"]').trigger("click");
      await flushPromises();

      expect(q('[data-test="breath-modal"]')).toBeTruthy();
      expect(q('[data-test="breath-circle"]')).toBeTruthy();

      // 开始：吸气 4s，倒计时 4，轮次 1/3
      q('[data-test="breath-start"]')!.click();
      await flushPromises();
      expect(q('[data-test="breath-phase"]')!.textContent).toContain("吸气");
      expect(q('[data-test="breath-count"]')!.textContent).toBe("4");
      expect(q('[data-test="breath-round"]')!.textContent).toBe("第 1/3 轮");

      // 走 1s → 倒计时 3
      vi.advanceTimersByTime(1000);
      await flushPromises();
      expect(q('[data-test="breath-count"]')!.textContent).toBe("3");

      // 再走 3s（吸气共 4s 结束）→ 切换屏息，倒计时 7
      vi.advanceTimersByTime(3000);
      await flushPromises();
      expect(q('[data-test="breath-phase"]')!.textContent).toContain("屏息");
      expect(q('[data-test="breath-count"]')!.textContent).toBe("7");

      // 停止 → 无遗留 pending timer（真实失败口径：有残留即 FAIL）
      q('[data-test="breath-stop"]')!.click();
      await flushPromises();
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("⑥ 科学方法库", () => {
  it("7 组、默认首组展开；展开步骤；折叠切换不重建滚动容器", async () => {
    const { wrapper } = setup();
    const groupHeads = wrapper.findAll('[data-test^="group-"]');
    expect(groupHeads.length).toBe(7);

    // 默认：A 组（急性难受）展开可见 6 条；B 组方法不可见
    expect(wrapper.find('[data-test="method-physio_sigh"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="method-pmr_short"]').exists()).toBe(false);
    const bodyEl = wrapper.find('[data-test="toolkit-body"]').element;
    const physioEl = wrapper.find('[data-test="method-physio_sigh"]').element;

    // 展开 B 组
    await wrapper.find('[data-test="group-B"]').trigger("click");
    expect(wrapper.find('[data-test="method-pmr_short"]').exists()).toBe(true);

    // 展开 A 组首条步骤
    await wrapper.find('[data-test="method-physio_sigh"]').find(".btn-soft").trigger("click");
    expect(wrapper.find('[data-test="steps-physio_sigh"]').exists()).toBe(true);

    // 折叠 B 组：滚动容器与 A 组方法卡节点身份不变（内容级更新，不整页重建）
    await wrapper.find('[data-test="group-B"]').trigger("click");
    expect(wrapper.find('[data-test="method-pmr_short"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="toolkit-body"]').element).toBe(bodyEl);
    expect(wrapper.find('[data-test="method-physio_sigh"]').element).toBe(physioEl);
  });
});

describe("⑦ 情绪日记", () => {
  it("三问保存 → data.journal +1 且字段正确；chips 追加感受；预览显示最新一条", async () => {
    const { wrapper, store } = setup();
    await wrapper.find('[data-test="journal-new"]').trigger("click");
    await flushPromises();

    const eventEl = q('[data-test="journal-event"]') as HTMLTextAreaElement;
    eventEl.value = "机房值班出了小故障";
    eventEl.dispatchEvent(new Event("input"));
    const feelingEl = q('[data-test="journal-feeling"]') as HTMLTextAreaElement;
    feelingEl.value = "紧张";
    feelingEl.dispatchEvent(new Event("input"));
    const actionEl = q('[data-test="journal-action"]') as HTMLTextAreaElement;
    actionEl.value = "喝口水";
    actionEl.dispatchEvent(new Event("input"));

    // 点情绪 chip → 追加到感受框（顿号分隔）
    const emoChips = document.body.querySelectorAll('[data-test="emo-chip"]');
    expect(emoChips.length).toBeGreaterThan(50); // 内置 56 词渲染
    (emoChips[0] as HTMLElement).click();
    await flushPromises();
    const newFeeling = (q('[data-test="journal-feeling"]') as HTMLTextAreaElement).value;
    expect(newFeeling.startsWith("紧张、")).toBe(true);

    // 保存
    (q('[data-test="journal-save"]') as HTMLElement).click();
    await flushPromises();

    expect(store.data.journal).toHaveLength(1); // 真实失败口径：长度不变即 FAIL
    const e = store.data.journal![0];
    expect(e.date).toBe(todayStr());
    expect(e.time).toMatch(/^\d{2}:\d{2}$/);
    expect(e.event).toBe("机房值班出了小故障");
    expect(e.feeling).toContain("紧张、");
    expect(e.action).toBe("喝口水");

    // 弹窗已关闭 + 预览显示最新一条
    expect(q('[data-test="journal-edit"]')).toBeNull();
    expect(wrapper.find('[data-test="journal-preview"]').text()).toContain("机房值班出了小故障");
  });

  it("自定义情绪词出现在日记 chips", async () => {
    const { wrapper } = setup([], [{ word: "摆烂" }]);
    await wrapper.find('[data-test="journal-new"]').trigger("click");
    await flushPromises();
    const words = Array.from(document.body.querySelectorAll('[data-test="emo-chip"]')).map(
      (c) => c.textContent,
    );
    expect(words).toContain("摆烂");
  });

  it("查看全部：按天分组倒序；删除后 journal 减一", async () => {
    const seeded: JournalEntry[] = [
      { date: "2026-10-30", time: "21:00", event: "第一条", feeling: "低落", action: "" },
      { date: "2026-10-31", time: "09:00", event: "第二条", feeling: "平静", action: "" },
    ];
    const { wrapper, store } = setup(seeded);
    await wrapper.find('[data-test="journal-all-btn"]').trigger("click");
    await flushPromises();

    // 倒序：两天分组标题，最新一天在前
    const days = document.body.querySelectorAll('[data-test="j-day"]');
    expect(days.length).toBe(2);
    expect(days[0]!.textContent).toBe("2026-10-31");

    // 删除最新一篇（底层下标 1）
    (q('[data-test="j-del-1"]') as HTMLElement).click();
    await flushPromises();
    expect(store.data.journal).toHaveLength(1);
    expect(store.data.journal![0].event).toBe("第一条");
  });

  it("旧 text 格式日记兼容：预览取首段 event", async () => {
    const { wrapper } = setup([{ text: "机房值班出了小故障\n紧张\n散步" }]);
    expect(wrapper.find('[data-test="journal-preview"]').text()).toContain("机房值班出了小故障");
  });
});
