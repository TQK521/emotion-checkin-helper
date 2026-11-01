<script setup lang="ts">
/**
 * HomeView.vue —— 首页情绪打卡（对齐旧版 pages_home.py）
 * 问候卡 + 情绪多选（频次置顶）+ 自定义词 + 场景单选（可取消）+ 强度 1-5
 * + 一句话 + 记录/撤销/清空；切页草稿走 feature 私有模块态（draft.ts）。
 */
import { computed, onMounted, onUnmounted, ref } from "vue";

import BaseCard from "@/shared/ui/BaseCard.vue";
import BaseChip from "@/shared/ui/BaseChip.vue";
import { useCheckinStore } from "@/core/store/use-checkin";
import { allEmotions, calcStreak, countBy, greeting, monthDays } from "@/core/stats/statistics";
import { monthDayWeekday, todayStr } from "@/shared/lib/date";
import emotionsJson from "@/assets/data/emotions.json";

import { clearHomeDraft, getHomeDraft, saveHomeDraft } from "./draft";

/** 场景选项（对齐 theme.py SCENES 11 词；web 侧无现成常量，feature 私有） */
const SCENES = [
  "备考",
  "自习",
  "作业论文",
  "学生工作",
  "人际",
  "家庭关系",
  "睡眠状况",
  "身体",
  "娱乐休闲",
  "突发状况",
  "其他",
] as const;

/** 内置情绪词（emotions.json 56 词） */
const BUILTIN_EMOTIONS: readonly string[] = emotionsJson.emotions;

/** 一句话占位提示（对齐旧版 note_entry 初始文本） */
const NOTE_PLACEHOLDER = "例如：复习不下去，心里堵得慌";

const store = useCheckinStore();

// ---- 表单状态 ----
const selectedEmotions = ref<string[]>([]);
const customInput = ref("");
const scene = ref("");
const intensity = ref(3);
const note = ref(NOTE_PLACEHOLDER);
/** 温柔内联提示（未选情绪 / 撤销失败等） */
const tip = ref("");
/** 记录成功反馈 */
const done = ref("");
/** 记录成功摘要 */
const summary = ref("");

/** 情绪候选 = 内置 56 + 自定义词库；按历史频次降序置顶（同频稳定排序） */
const orderedEmotions = computed<string[]>(() => {
  const words = allEmotions(store.data, BUILTIN_EMOTIONS);
  const freq = countBy(store.data.records, "emotions");
  // Array.sort 稳定：频次相同保持 allEmotions 的原序（内置序 + 自定义追加序）
  return [...words].sort((a, b) => (freq.get(b) ?? 0) - (freq.get(a) ?? 0));
});

/** 问候卡主文案（对齐旧版 greeting_label） */
const greetingLine = computed(() => `${greeting()}，难受的时候，把它说出来。`);

/** 问候卡日期行：日期 · 今天已记录 N 次 · 累计 M 次 · 连续 K 天 */
const greetingMeta = computed(() => {
  const d = todayStr();
  return `${monthDayWeekday(d)} · 今天已记录 ${store.todayCount} 次 · 累计 ${store.totalCount} 次 · 连续 ${calcStreak(store.data)} 天`;
});

/** 「你叫它…」选中提示（对齐旧版 emo_selected_label） */
const selectedLabel = computed(() => {
  const parts = selectedEmotions.value.map((e) => `「${e}」`);
  const custom = customInput.value.trim();
  if (custom) parts.push(`「${custom}」`);
  if (parts.length === 0) return "";
  if (parts.length === 1) return `你叫它：${parts[0]}——好，你看见它了。`;
  return `你叫它们：${parts.join("")}——好，你看见它们了。`;
});

/** 情绪多选：再点一次取消 */
function toggleEmotion(word: string): void {
  tip.value = "";
  const i = selectedEmotions.value.indexOf(word);
  if (i >= 0) selectedEmotions.value.splice(i, 1);
  else selectedEmotions.value.push(word);
}

/** 场景单选：再次点击已选项 → 取消（落库空串） */
function onSceneClick(opt: string): void {
  scene.value = scene.value === opt ? "" : opt;
}

/** 强度单选（点击已选项保持选中，不取消） */
function onIntensity(i: number): void {
  intensity.value = i;
}

/** 备注聚焦：首次聚焦清掉占位提示 */
function onNoteFocus(): void {
  if (note.value === NOTE_PLACEHOLDER) note.value = "";
}

/** 备注当前有效值（占位提示视同空） */
function effectiveNote(): string {
  const n = note.value.trim();
  return n === NOTE_PLACEHOLDER ? "" : n;
}

/** 记录这次情绪（对齐旧版 _record_emotion） */
async function onRecord(): Promise<void> {
  const emotions = [...selectedEmotions.value];
  const custom = customInput.value.trim();
  if (custom) emotions.push(custom);

  if (emotions.length === 0) {
    // 温柔内联提示，不用浏览器原生弹窗
    tip.value = "先给情绪起个名字吧——说出口，它才开始变小。可以点一个或多个情绪词，也可以自己输入一个名字。";
    return;
  }
  tip.value = "";

  await store.addRecord({
    emotions,
    action: effectiveNote(),
    scene: scene.value,
    intensity: intensity.value,
  });

  // v1.4.3 词库生长：非内置新词同步写入自定义词库（store 内部去重/空词拒绝）
  if (custom && !BUILTIN_EMOTIONS.includes(custom)) {
    await store.addCustomEmotion(custom);
  }

  // H3：保留已选情绪/场景/强度（可再记一条），只清备注与自定义输入
  customInput.value = "";
  note.value = NOTE_PLACEHOLDER;

  done.value = "我听见了，已记录。可以再记一条，或点「清空选择」重新开始。";
  summary.value = `今天已记录 ${store.todayCount} 次・本月 ${monthDays(store.data)} 天`;

  // 提交成功：草稿清空
  clearHomeDraft();
}

/** 撤销上一条（对齐旧版 _undo_last_record） */
async function onUndo(): Promise<void> {
  const rec = await store.undoLast();
  if (!rec) {
    // store 已保证：最后一条不是刚记的（外部改动/无记录）时返回 null
    tip.value = "没有可撤销的记录";
    return;
  }
  tip.value = "";
  // 把被撤销记录恢复回表单
  selectedEmotions.value = [...rec.emotions];
  scene.value = rec.scene ?? "";
  intensity.value = rec.intensity ?? 3;
  note.value = rec.action ? rec.action : NOTE_PLACEHOLDER;
  customInput.value = "";
  done.value = "已撤销上一条，可以重新调整后再记录。";
  summary.value = "";
}

/** 清空选择（对齐旧版 _clear_form） */
function onClear(): void {
  selectedEmotions.value = [];
  customInput.value = "";
  scene.value = "";
  intensity.value = 3;
  note.value = NOTE_PLACEHOLDER;
  tip.value = "";
  done.value = "";
  summary.value = "";
  clearHomeDraft();
}

// ---- 切页草稿：挂载恢复，卸载保存 ----
onMounted(() => {
  const d = getHomeDraft();
  if (!d) return;
  selectedEmotions.value = [...d.emotions];
  scene.value = d.scene;
  intensity.value = d.intensity;
  note.value = d.note || NOTE_PLACEHOLDER;
  customInput.value = d.custom;
});

onUnmounted(() => {
  saveHomeDraft({
    emotions: selectedEmotions.value,
    scene: scene.value,
    intensity: intensity.value,
    note: effectiveNote(),
    custom: customInput.value,
  });
});
</script>

<template>
  <div class="home-view">
    <!-- 问候卡 -->
    <BaseCard class="greeting-card">
      <p class="greeting-line" data-test="greeting-line">{{ greetingLine }}</p>
      <p class="greeting-meta" data-test="greeting-meta">{{ greetingMeta }}</p>
    </BaseCard>

    <!-- 情绪命名卡 -->
    <BaseCard>
      <h3 class="card-title">给此刻的情绪起个名字</h3>
      <p class="card-sub">说出名字，它就开始变小（情绪标记）· 情绪复杂时可以多选</p>

      <div class="chips" data-test="emotion-chips">
        <BaseChip
          v-for="w in orderedEmotions"
          :key="w"
          :active="selectedEmotions.includes(w)"
          @click="toggleEmotion(w)"
        >
          {{ w }}
        </BaseChip>
      </div>

      <div class="custom-row">
        <span class="field-label">或自己起个名字：</span>
        <input
          v-model="customInput"
          class="text-input"
          data-test="custom-input"
          placeholder="输入新词"
        />
      </div>

      <p v-if="selectedLabel" class="selected-label" data-test="selected-label">
        {{ selectedLabel }}
      </p>

      <!-- 场景单选（可取消） -->
      <div class="scene-row">
        <span class="field-label">此刻发生了什么（可选）：</span>
        <div class="chips" data-test="scene-chips">
          <BaseChip
            v-for="s in SCENES"
            :key="s"
            :active="scene === s"
            @click="onSceneClick(s)"
          >
            {{ s }}
          </BaseChip>
        </div>
      </div>

      <!-- 强度 1-5（默认 3） -->
      <div class="intensity-row">
        <span class="field-label">强度 1–5，5 最强烈：</span>
        <span class="weak-strong">弱</span>
        <button
          v-for="i in 5"
          :key="i"
          type="button"
          class="inten-btn"
          :class="{ on: intensity === i }"
          data-test="inten-btn"
          @click="onIntensity(i)"
        >
          {{ i }}
        </button>
        <span class="weak-strong">强</span>
      </div>
    </BaseCard>

    <!-- 一句话输入卡 -->
    <BaseCard>
      <h3 class="card-title">此刻想说的一句话（可选）</h3>
      <textarea
        v-model="note"
        class="text-area"
        data-test="note-input"
        rows="3"
        @focus="onNoteFocus"
      />
    </BaseCard>

    <!-- 记录按钮 -->
    <button type="button" class="record-btn" data-test="record-btn" @click="onRecord">
      记录这次情绪
    </button>

    <!-- 温柔内联提示 / 成功反馈 -->
    <p v-if="tip" class="inline-tip" data-test="tip">{{ tip }}</p>
    <p v-if="done" class="done-text" data-test="done">{{ done }}</p>
    <p v-if="summary" class="summary-text" data-test="summary">{{ summary }}</p>

    <!-- 撤销 / 清空 -->
    <div class="post-row">
      <button type="button" class="link-btn" data-test="undo-btn" @click="onUndo">
        撤销上一条
      </button>
      <button type="button" class="link-btn" data-test="clear-btn" @click="onClear">
        清空选择
      </button>
    </div>

    <p class="bottom-tip">每一次难受都值得被看见。记完之后，去「工具」页做几次呼吸也行。</p>
  </div>
</template>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.greeting-line {
  margin: 0;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--col-text);
}

.greeting-meta {
  margin: 8px 0 0;
  text-align: center;
  font-size: 13px;
  color: var(--col-sub);
}

.card-title {
  margin: 0;
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.card-sub {
  margin: 6px 0 12px;
  text-align: center;
  font-size: 12px;
  color: var(--col-sub);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.custom-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
}

.field-label {
  font-size: 12px;
  color: var(--col-sub);
}

.text-input {
  padding: 6px 10px;
  border: 1px solid var(--col-line);
  border-radius: 8px;
  background: var(--col-bg);
  font-size: 13px;
  color: var(--col-text);
}

.selected-label {
  margin: 10px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--col-accent);
}

.scene-row {
  margin-top: 14px;
}

.scene-row .field-label {
  display: block;
  text-align: center;
  margin-bottom: 8px;
}

.intensity-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 16px;
}

.weak-strong {
  font-size: 12px;
  color: var(--col-sub);
}

.inten-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid var(--col-line);
  background: var(--col-chip);
  color: var(--col-sub);
  font-size: 13px;
  cursor: pointer;
}

.inten-btn.on {
  background: var(--col-inten-on);
  border-color: var(--col-inten-on);
  color: #444;
  box-shadow: 0 0 8px var(--col-inten-glow);
}

.text-area {
  width: 100%;
  margin-top: 8px;
  padding: 10px;
  border: 1px solid var(--col-line);
  border-radius: 8px;
  background: var(--col-bg);
  font-size: 13px;
  color: var(--col-text);
  resize: vertical;
  box-sizing: border-box;
}

.record-btn {
  padding: 14px;
  border: none;
  border-radius: var(--card-radius);
  background: var(--col-primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.record-btn:hover {
  background: var(--col-primary-dk);
}

.inline-tip {
  margin: 0;
  text-align: center;
  font-size: 13px;
  color: var(--col-accent);
}

.done-text {
  margin: 0;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.summary-text {
  margin: 0;
  text-align: center;
  font-size: 12px;
  color: var(--col-sub);
}

.post-row {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.link-btn {
  border: none;
  background: none;
  font-size: 12px;
  color: var(--col-sub);
  cursor: pointer;
  padding: 4px 8px;
}

.link-btn:hover {
  color: var(--col-primary-dk);
}

.bottom-tip {
  margin: 0;
  text-align: center;
  font-size: 12px;
  color: var(--col-sub);
}
</style>
