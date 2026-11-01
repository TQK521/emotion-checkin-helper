/**
 * HomeView.test.ts —— 首页打卡域组件测试（InMemory 隔离，断言可真实失败）
 * 对齐验收清单 10 条；草稿用 feature 私有模块态，每例前后 clearHomeDraft。
 */
import { beforeEach, describe, expect, it } from "vitest";
import { mount, type VueWrapper } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import HomeView from "./HomeView.vue";
import { clearHomeDraft, getHomeDraft } from "./draft";
import { useCheckinStore } from "@/core/store/use-checkin";
import { InMemoryStorageAdapter } from "@/services/memory-storage.adapter";
import { todayStr } from "@/shared/lib/date";
import type { CheckinRecord, CustomEmotion } from "@/core/domain";

function makeRec(emotions: string[], date: string = todayStr(), time = "08:00"): CheckinRecord {
  return { ts: `${date} ${time}:00`, date, time, emotions, action: "" };
}

interface SetupOpts {
  records?: CheckinRecord[];
  custom?: CustomEmotion[];
}

async function setup(opts: SetupOpts = {}) {
  setActivePinia(createPinia());
  clearHomeDraft();
  const store = useCheckinStore();
  store.setStorage(
    new InMemoryStorageAdapter({
      start_date: null,
      records: opts.records ?? [],
      best_streak: 0,
      journal: [],
      custom_emotions: opts.custom ?? [],
    }),
  );
  await store.load();
  const wrapper = mount(HomeView);
  await wrapper.vm.$nextTick();
  return { wrapper, store };
}

/** 等待异步 handler（addRecord/undoLast 的 await 链）跑完并刷 DOM */
async function flush(wrapper: VueWrapper): Promise<void> {
  await new Promise((r) => setTimeout(r, 0));
  await wrapper.vm.$nextTick();
}

function emoChip(wrapper: VueWrapper, word: string) {
  const btn = wrapper.findAll('[data-test="emotion-chips"] button').find((b) => b.text() === word);
  if (!btn) throw new Error(`情绪标签未找到：${word}`);
  return btn;
}

function sceneChip(wrapper: VueWrapper, opt: string) {
  const btn = wrapper.findAll('[data-test="scene-chips"] button').find((b) => b.text() === opt);
  if (!btn) throw new Error(`场景标签未找到：${opt}`);
  return btn;
}

function noteValue(wrapper: VueWrapper): string {
  return (wrapper.find('[data-test="note-input"]').element as HTMLTextAreaElement).value;
}

beforeEach(() => {
  clearHomeDraft();
});

describe("HomeView 渲染", () => {
  it("mount 后问候文案/情绪 chips/场景 chips/强度 1-5/备注输入渲染可见", async () => {
    const { wrapper } = await setup();

    // 问候卡：旧版文案片段 + 今日计数
    expect(wrapper.find('[data-test="greeting-line"]').text()).toContain("难受的时候，把它说出来");
    expect(wrapper.find('[data-test="greeting-meta"]').text()).toContain("今天已记录 0 次");
    // 情绪 chips = 内置 56 词
    expect(wrapper.findAll('[data-test="emotion-chips"] button')).toHaveLength(56);
    // 场景 chips = SCENES 11 词
    expect(wrapper.findAll('[data-test="scene-chips"] button')).toHaveLength(11);
    // 强度 5 钮 + 备注输入存在
    expect(wrapper.findAll('[data-test="inten-btn"]')).toHaveLength(5);
    expect(wrapper.find('[data-test="note-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="custom-input"]').exists()).toBe(true);
  });

  it("强度默认选中 3", async () => {
    const { wrapper } = await setup();
    const btns = wrapper.findAll('[data-test="inten-btn"]');
    // index 2 = 数字 3
    expect(btns[2].classes()).toContain("on");
    expect(btns[0].classes()).not.toContain("on");
  });
});

describe("HomeView 记录流程", () => {
  it("选情绪→填备注→记录：records +1、todayCount +1、已选情绪保留、备注与自定义输入清空", async () => {
    const { wrapper, store } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="note-input"]').setValue("复习不下去");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records).toHaveLength(1);
    expect(store.todayCount).toBe(1);
    expect(store.data.records[0].emotions).toEqual(["平静"]);
    expect(store.data.records[0].action).toBe("复习不下去");
    // H3：已选情绪保留（chip 仍 active）
    expect(emoChip(wrapper, "平静").classes()).toContain("active");
    // H3：备注清空回占位提示、自定义输入清空
    expect(noteValue(wrapper)).toBe("例如：复习不下去，心里堵得慌");
    expect((wrapper.find('[data-test="custom-input"]').element as HTMLInputElement).value).toBe("");
    // 成功反馈可见
    expect(wrapper.find('[data-test="done"]').text()).toContain("已记录");
  });

  it("未选情绪点记录：不写入 records，出现温柔内联提示", async () => {
    const { wrapper, store } = await setup();

    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records).toHaveLength(0);
    const tip = wrapper.find('[data-test="tip"]');
    expect(tip.exists()).toBe(true);
    expect(tip.text()).toContain("先给情绪起个名字");
  });

  it("记录后立即撤销：records 回退、表单（情绪/场景/强度/备注）全部回填", async () => {
    const { wrapper, store } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await sceneChip(wrapper, "备考").trigger("click");
    await wrapper.findAll('[data-test="inten-btn"]')[4].trigger("click"); // 强度 5
    await wrapper.find('[data-test="note-input"]').setValue("散步");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);
    expect(store.data.records).toHaveLength(1);

    await wrapper.find('[data-test="undo-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records).toHaveLength(0);
    // 表单恢复
    expect(emoChip(wrapper, "平静").classes()).toContain("active");
    expect(sceneChip(wrapper, "备考").classes()).toContain("active");
    expect(wrapper.findAll('[data-test="inten-btn"]')[4].classes()).toContain("on");
    expect(noteValue(wrapper)).toBe("散步");
  });

  it("外部改动后调用撤销：返回 null、无回退、有温柔提示", async () => {
    const { wrapper, store } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);
    // 模拟外部 push 一条（最后一条不再是刚记的）
    store.data.records.push(makeRec(["烦躁"], todayStr(), "09:00"));

    await wrapper.find('[data-test="undo-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records).toHaveLength(2); // 无回退
    expect(wrapper.find('[data-test="tip"]').text()).toBe("没有可撤销的记录");
  });

  it("场景再次点击取消后提交：record.scene 为空字符串", async () => {
    const { wrapper, store } = await setup();

    await sceneChip(wrapper, "备考").trigger("click");
    expect(sceneChip(wrapper, "备考").classes()).toContain("active");
    await sceneChip(wrapper, "备考").trigger("click"); // 再次点击 → 取消
    expect(sceneChip(wrapper, "备考").classes()).not.toContain("active");

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records).toHaveLength(1);
    expect(store.data.records[0].scene).toBe("");
  });

  it("未点强度直接提交：落库 intensity 为默认 3", async () => {
    const { wrapper, store } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records[0].intensity).toBe(3);
  });
});

describe("HomeView 自定义情绪词", () => {
  it("自定义词随记录写入 emotions 并生长词库；重复词不重复入词库", async () => {
    const { wrapper, store } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="custom-input"]').setValue("摆烂");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(store.data.records[0].emotions).toEqual(["平静", "摆烂"]);
    expect(store.data.custom_emotions).toContainEqual({ word: "摆烂", gloss: "" });

    // 第二次再记同一个自定义词 → 词库不重复
    await wrapper.find('[data-test="custom-input"]').setValue("摆烂");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);
    expect(store.data.custom_emotions?.filter((e) => e.word === "摆烂")).toHaveLength(1);
  });

  it("addCustomEmotion 契约：空词返回 false、重复词返回 false 且词库不重复", async () => {
    const { store } = await setup();

    expect(await store.addCustomEmotion("   ")).toBe(false);
    expect(await store.addCustomEmotion("心累")).toBe(true);
    expect(await store.addCustomEmotion("心累")).toBe(false);
    expect((store.data.custom_emotions ?? []).map((e) => e.word)).toEqual(["心累"]);
  });
});

describe("HomeView 情绪排序", () => {
  it("历史高频词置顶（全部 records 频次降序，未用词保持原序在后）", async () => {
    const records = [
      makeRec(["感恩"]),
      makeRec(["感恩"]),
      makeRec(["感恩"]),
      makeRec(["平静"]),
    ];
    const { wrapper } = await setup({ records });

    const chips = wrapper.findAll('[data-test="emotion-chips"] button');
    // 「感恩」用过 3 次，应排在「焦虑」（内置第 0、0 次）之前
    expect(chips[0].text()).toBe("感恩");
    expect(chips[1].text()).toBe("平静"); // 用过 1 次
  });
});

describe("HomeView 切页草稿", () => {
  it("卸载重挂后草稿（情绪/场景/备注）恢复", async () => {
    const { wrapper } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await sceneChip(wrapper, "备考").trigger("click");
    await wrapper.find('[data-test="note-input"]').setValue("散步");
    wrapper.unmount();

    // 模块态草稿已保存
    const d = getHomeDraft();
    expect(d?.emotions).toEqual(["平静"]);
    expect(d?.scene).toBe("备考");
    expect(d?.note).toBe("散步");

    // 重新挂载（模拟路由切回）→ 表单恢复
    const wrapper2 = mount(HomeView);
    await wrapper2.vm.$nextTick();
    expect(emoChip(wrapper2, "平静").classes()).toContain("active");
    expect(sceneChip(wrapper2, "备考").classes()).toContain("active");
    expect(noteValue(wrapper2)).toBe("散步");
    wrapper2.unmount();
  });

  it("提交成功后草稿清空", async () => {
    const { wrapper } = await setup();

    await emoChip(wrapper, "平静").trigger("click");
    await wrapper.find('[data-test="record-btn"]').trigger("click");
    await flush(wrapper);

    expect(getHomeDraft()).toBeNull();
  });
});
