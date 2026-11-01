/**
 * ManualView.test.ts —— 手册域（波2）验收测试。
 * mount + jsdom；Pinia InMemory 注入（不碰项目根 checkin_data.json）。
 * 断言全部可真实失败：渲染文本/元素计数/状态切换/store 变化。
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia, type Pinia } from "pinia";
import ManualView from "./ManualView.vue";
import { useCheckinStore } from "@/core/store/use-checkin";
import { InMemoryStorageAdapter } from "@/services/memory-storage.adapter";
import { todayStr } from "@/shared/lib/date";
import type { CheckinData, CheckinRecord, CustomEmotion } from "@/core/domain";
import chaptersJson from "@/assets/data/chapters.json";
import emotionsJson from "@/assets/data/emotions.json";

const chapters = chaptersJson.chapters;
const builtinEmotions = emotionsJson.emotions;
const builtinGlossary = emotionsJson.glossary;
const FALLBACK = "这个词是后来加入的，等你来定义它";

function rec(emotions: string[]): CheckinRecord {
  return {
    ts: `${todayStr()} 08:00:00`,
    date: todayStr(),
    time: "08:00",
    emotions,
    action: "",
  };
}

function seedData(records: CheckinRecord[], custom: CustomEmotion[] = []): CheckinData {
  return { start_date: null, records, best_streak: 0, journal: [], custom_emotions: custom };
}

interface Harness {
  wrapper: ReturnType<typeof mount>;
  store: ReturnType<typeof useCheckinStore>;
  pinia: Pinia;
}

async function mountManual(records: CheckinRecord[], custom: CustomEmotion[] = []): Promise<Harness> {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useCheckinStore();
  store.setStorage(new InMemoryStorageAdapter(seedData(records, custom)));
  await store.load();
  const wrapper = mount(ManualView, { global: { plugins: [pinia] } });
  await wrapper.vm.$nextTick();
  return { wrapper, store, pinia };
}

/** 断言选择器是否存在（本 VTU 版本 find() 类型 omit 了 exists，用 findAll 计数） */
function has(w: { findAll(s: string): unknown[] }, selector: string): boolean {
  return w.findAll(selector).length > 0;
}

/** 轮询等待 Teleport 内元素出现（Transition 进出在 jsdom 下有时序竞争） */
async function waitFor(testid: string, timeout = 1500): Promise<HTMLElement> {
  const start = Date.now();
  for (;;) {
    const el = document.querySelector(`[data-testid="${testid}"]`);
    if (el) return el as HTMLElement;
    if (Date.now() - start > timeout) throw new Error(`waitFor timeout: ${testid}`);
    await new Promise((r) => setTimeout(r, 10));
  }
}

/** 在 Teleport 弹窗内设置 v-model 输入值 */
async function setTeleportInput(testid: string, value: string): Promise<void> {
  const el = (await waitFor(testid)) as HTMLInputElement;
  el.value = value;
  el.dispatchEvent(new Event("input", { bubbles: true }));
}

async function clickTeleport(testid: string): Promise<void> {
  (await waitFor(testid)).click();
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("ManualView · 三 Tab 固定栏", () => {
  it("默认今日一课；切换后仅渲染目标 Tab 内容（互斥）", async () => {
    const { wrapper } = await mountManual([]);
    expect(has(wrapper, '[data-testid="pane-today"]')).toBe(true);
    expect(has(wrapper, '[data-testid="pane-catalog"]')).toBe(false);
    expect(has(wrapper, '[data-testid="pane-glossary"]')).toBe(false);

    await wrapper.get('[data-testid="tab-catalog"]').trigger("click");
    expect(has(wrapper, '[data-testid="pane-today"]')).toBe(false);
    expect(has(wrapper, '[data-testid="pane-catalog"]')).toBe(true);
    expect(has(wrapper, '[data-testid="pane-glossary"]')).toBe(false);

    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");
    expect(has(wrapper, '[data-testid="pane-today"]')).toBe(false);
    expect(has(wrapper, '[data-testid="pane-catalog"]')).toBe(false);
    expect(has(wrapper, '[data-testid="pane-glossary"]')).toBe(true);
  });
});

describe("ManualView · 今日一课推荐", () => {
  it("最近打卡情绪命中 EMOTION_LESSON_MAP → 展示对应章节", async () => {
    const { wrapper } = await mountManual([rec(["焦虑"])]);
    // 焦虑 → 索引 2（考试焦虑与临场紧张）
    expect(wrapper.get('[data-testid="today-name"]').text()).toBe(chapters[2].name);
  });

  it("按 emotions 顺序取首个命中映射的词（走神在前则取走神→1）", async () => {
    const { wrapper } = await mountManual([rec(["走神", "焦虑"])]);
    expect(wrapper.get('[data-testid="today-name"]').text()).toBe(chapters[1].name);
  });

  it("换一课：随机换成 ≠ 当前课的另一课（stub Math.random=0 使结果确定）", async () => {
    const { wrapper } = await mountManual([rec(["焦虑"])]);
    const before = wrapper.get('[data-testid="today-name"]').text();
    expect(before).toBe(chapters[2].name);

    const orig = Math.random;
    Math.random = vi.fn(() => 0);
    try {
      await wrapper.get('[data-testid="btn-swap"]').trigger("click");
    } finally {
      Math.random = orig;
    }
    // 排除当前课后候选首项 = 索引 0
    const after = wrapper.get('[data-testid="today-name"]').text();
    expect(after).toBe(chapters[0].name);
    expect(after).not.toBe(before);
  });

  it("无打卡记录 → 随机展示一合法章节（索引在 0..69）", async () => {
    const { wrapper } = await mountManual([]);
    const name = wrapper.get('[data-testid="today-name"]').text();
    expect(chapters.some((c) => c.name === name)).toBe(true);
  });
});

describe("ManualView · 课程详情", () => {
  it("读全文进入详情：full 三段 h2/bullet/body 数量正确 + tip 块渲染", async () => {
    const { wrapper } = await mountManual([rec(["焦虑"])]);
    await wrapper.get('[data-testid="btn-read"]').trigger("click");

    expect(has(wrapper, '[data-testid="pane-today"]')).toBe(false);
    const detail = wrapper.get('[data-testid="pane-detail"]');
    expect(detail.get('[data-testid="detail-title"]').text()).toBe(chapters[2].name);

    expect(detail.findAll('[data-testid="blk-h2"]').length).toBe(
      chapters[2].full.filter((b) => b[0] === "h2").length,
    );
    expect(detail.findAll('[data-testid="blk-bullet"]').length).toBe(
      chapters[2].full.filter((b) => b[0] === "bullet").length,
    );
    expect(detail.findAll('[data-testid="blk-body"]').length).toBe(
      chapters[2].full.filter((b) => b[0] === "body").length,
    );
    expect(has(detail, '[data-testid="tip-block"]')).toBe(true);
    expect(has(detail, '[data-testid="warm"]')).toBe(true);
  });

  it("上一篇/下一篇按全局顺序循环：首课再上一篇→末课；末课再下一篇→首课", async () => {
    const { wrapper } = await mountManual([rec(["焦虑"])]); // idx 2
    await wrapper.get('[data-testid="btn-read"]').trigger("click");

    const prev = () => wrapper.get('[data-testid="btn-prev"]').trigger("click");
    // 2 → 1 → 0（首课）
    await prev();
    expect(wrapper.get('[data-testid="detail-title"]').text()).toBe(chapters[1].name);
    await prev();
    expect(wrapper.get('[data-testid="detail-title"]').text()).toBe(chapters[0].name);
    // 首课再上一篇 → 循环到末课（69）
    await prev();
    expect(wrapper.get('[data-testid="detail-title"]').text()).toBe(
      chapters[chapters.length - 1].name,
    );
    // 末课再下一篇 → 循环回首课（0）
    await wrapper.get('[data-testid="btn-next"]').trigger("click");
    expect(wrapper.get('[data-testid="detail-title"]').text()).toBe(chapters[0].name);
  });

  it("从今日一课进详情 → 返回仍回到今日一课 Tab", async () => {
    const { wrapper } = await mountManual([rec(["焦虑"])]);
    await wrapper.get('[data-testid="btn-read"]').trigger("click");
    expect(has(wrapper, '[data-testid="pane-detail"]')).toBe(true);
    await wrapper.get('[data-testid="btn-back"]').trigger("click");
    expect(has(wrapper, '[data-testid="pane-detail"]')).toBe(false);
    expect(has(wrapper, '[data-testid="pane-today"]')).toBe(true);
  });
});

describe("ManualView · 课程目录", () => {
  it("按 group_order 分组：默认仅第一组（学习）展开，其余收起", async () => {
    const { wrapper } = await mountManual([]);
    await wrapper.get('[data-testid="tab-catalog"]').trigger("click");

    const firstGroup = chaptersJson.group_order[0];
    const firstCount = chapters.filter((c) => c.group === firstGroup).length;
    expect(wrapper.findAll('[data-testid="lesson-row"]').length).toBe(firstCount);
    // 组头可见
    expect(wrapper.get('[data-testid="group-head-学习"]').text()).toContain("学习");
  });

  it("点击组头折叠/展开切换；点课行进详情；返回目录且折叠状态保持", async () => {
    const { wrapper } = await mountManual([]);
    await wrapper.get('[data-testid="tab-catalog"]').trigger("click");

    const studyRows = wrapper.findAll('[data-testid="lesson-row"]').length;
    // 展开第二组（人际）
    await wrapper.get('[data-testid="group-head-人际"]').trigger("click");
    const renCount = chapters.filter((c) => c.group === "人际").length;
    expect(wrapper.findAll('[data-testid="lesson-row"]').length).toBe(studyRows + renCount);

    // 点第一行课 → 详情
    const firstName = wrapper
      .findAll('[data-testid="lesson-name"]')[0]
      .text();
    await wrapper.findAll('[data-testid="lesson-row"]')[0].trigger("click");
    expect(wrapper.get('[data-testid="detail-title"]').text()).toBe(firstName);

    // 返回 → 仍在目录，且人际保持展开（行数不变）
    await wrapper.get('[data-testid="btn-back"]').trigger("click");
    expect(has(wrapper, '[data-testid="pane-catalog"]')).toBe(true);
    expect(wrapper.findAll('[data-testid="lesson-row"]').length).toBe(studyRows + renCount);
  });
});

describe("ManualView · 情绪词库", () => {
  it("默认渲染全部内置词（56）", async () => {
    const { wrapper } = await mountManual([]);
    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");
    expect(wrapper.findAll('[data-testid="word-card"]').length).toBe(builtinEmotions.length);
  });

  it("搜索即时过滤：仅含关键词的词出现", async () => {
    const { wrapper } = await mountManual([]);
    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");

    await wrapper.get('[data-testid="gloss-search"]').setValue("焦虑");
    const names = wrapper
      .findAll('[data-testid="word-name"]')
      .map((w) => w.text());
    const expected = builtinEmotions.filter((w) => w.includes("焦虑"));
    expect(names).toEqual(expected);
    expect(names).toEqual(["焦虑"]);
  });

  it("内置词点击展开显示 glossary 释义", async () => {
    const { wrapper } = await mountManual([]);
    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");

    await wrapper.findAll('[data-testid="word-card"]')[0].trigger("click");
    expect(wrapper.get('[data-testid="word-gloss"]').text()).toBe(builtinGlossary["焦虑"]);
  });

  it("自定义词无释义 → 展开显示兜底文案；预置自定义词出现在列表", async () => {
    const { wrapper, store } = await mountManual([], [{ word: "摆烂", gloss: "" }]);
    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");
    expect(store.data.custom_emotions).toHaveLength(1);
    expect(wrapper.findAll('[data-testid="word-card"]').length).toBe(builtinEmotions.length + 1);

    await wrapper.get('[data-testid="gloss-search"]').setValue("摆烂");
    const cards = wrapper.findAll('[data-testid="word-card"]');
    expect(cards.length).toBe(1);
    expect(wrapper.get('[data-testid="word-name"]').text()).toBe("摆烂");
    await cards[0].trigger("click");
    expect(wrapper.get('[data-testid="word-gloss"]').text()).toBe(FALLBACK);
  });

  it("添加新词 → store.custom_emotions +1 且出现在列表；重复词被拒绝并提示", async () => {
    const { wrapper, store } = await mountManual([]);
    await wrapper.get('[data-testid="tab-glossary"]').trigger("click");
    expect(store.data.custom_emotions ?? []).toHaveLength(0);

    // 打开弹窗（BaseModal Teleport 到 body）
    await wrapper.get('[data-testid="btn-add"]').trigger("click");
    await setTeleportInput("add-input", "新情绪词X");
    await clickTeleport("add-confirm");
    await wrapper.vm.$nextTick();

    expect(store.data.custom_emotions ?? []).toHaveLength(1);
    expect((store.data.custom_emotions ?? [])[0].word).toBe("新情绪词X");
    const names = wrapper.findAll('[data-testid="word-name"]').map((w) => w.text());
    expect(names).toContain("新情绪词X");

    // 等待弹窗 leave 过渡结束、旧节点从 body 移除，避免命中残留节点
    await new Promise((r) => setTimeout(r, 80));

    // 重复添加 → 拒绝并显示错误，store 不增长
    await wrapper.get('[data-testid="btn-add"]').trigger("click");
    await setTeleportInput("add-input", "新情绪词X");
    await clickTeleport("add-confirm");

    // addErr 在 store.addCustomEmotion 的 await 链之后才赋值渲染，轮询等待
    await waitFor("add-err");
    expect(store.data.custom_emotions ?? []).toHaveLength(1);
  });
});
