<script setup lang="ts">
// ToolView —— 工具箱页（对齐 pages_tool.py）
// 状态分流 → 3 条最快推荐 → 呼吸训练/三步冷静法/蝴蝶拍常驻 → 科学方法库分组折叠 → 情绪日记。
import { computed, ref } from "vue";
import BaseCard from "@/shared/ui/BaseCard.vue";
import BaseChip from "@/shared/ui/BaseChip.vue";
import { useCheckinStore } from "@/core/store/use-checkin";
import { nowTime, todayStr } from "@/shared/lib/date";
import type { ToolMethod } from "@/core/domain";
import BreathGuideModal from "./BreathGuideModal.vue";
import JournalEditModal from "./JournalEditModal.vue";
import JournalAllModal from "./JournalAllModal.vue";
import {
  allEmotionWords,
  breathModeFromAction,
  journalFields,
  methodByKey,
  methodsByGroup,
  recommendedMethods,
  toolkit,
  type BreathMode,
} from "./tool-data";

const store = useCheckinStore();

// ① 状态分流（默认 acute，对齐旧版 _tool_state_var）
const stateKey = ref<string>("acute");
const recMethods = computed<ToolMethod[]>(() => recommendedMethods(stateKey.value));

// ② 推荐卡：非呼吸法「立即开始」在卡下展开步骤
const expandedRecKey = ref<string | null>(null);

// ③ 呼吸引导弹窗
const breathOpen = ref(false);
const breathMode = ref<BreathMode>("478");
function openBreath(mode: BreathMode): void {
  breathMode.value = mode;
  breathOpen.value = true;
}
function startMethod(key: string): void {
  const m = methodByKey(key);
  if (!m) return;
  const mode = breathModeFromAction(m.action);
  if (mode) {
    openBreath(mode);
  } else {
    expandedRecKey.value = expandedRecKey.value === key ? null : key;
  }
}

// ⑥ 科学方法库：默认首组（A）展开，其余收起（对齐旧版 _toolkit_collapsed）
const collapsedGroups = ref<string[]>(toolkit.groups.slice(1).map((g) => g[0]));
const openSteps = ref<string[]>([]);
function toggleGroup(g: string): void {
  collapsedGroups.value = collapsedGroups.value.includes(g)
    ? collapsedGroups.value.filter((x) => x !== g)
    : [...collapsedGroups.value, g];
}
function toggleSteps(key: string): void {
  openSteps.value = openSteps.value.includes(key)
    ? openSteps.value.filter((k) => k !== key)
    : [...openSteps.value, key];
}

// ⑦ 情绪日记
const journalEditOpen = ref(false);
const journalAllOpen = ref(false);
const emotionWords = computed(() => allEmotionWords(store.data.custom_emotions));
const journalEntries = computed(() => store.data.journal ?? []);

async function onJournalSave(event: string, feeling: string, action: string): Promise<void> {
  if (!store.data.journal) store.data.journal = [];
  store.data.journal.push({ date: todayStr(), time: nowTime(), event, feeling, action });
  await store.save();
  journalEditOpen.value = false;
}

async function onJournalRemove(index: number): Promise<void> {
  if (index < 0 || index >= journalEntries.value.length) return;
  journalEntries.value.splice(index, 1);
  await store.save();
}

/** 最近一篇预览（event 优先，空则 feeling；截断 40 字；兼容旧 text 格式） */
const recentPreview = computed<string>(() => {
  const j = journalEntries.value;
  if (!j.length) return "";
  const last = j[j.length - 1];
  const [event, feeling] = journalFields(last);
  const summary = (event || feeling || "").slice(0, 40);
  if (!summary) return "";
  return `最近一篇（${last.date ?? ""} ${last.time ?? "—"}）：${summary}`;
});
</script>

<template>
  <section class="tool-page">
    <h2 class="page-title">情绪工具箱</h2>
    <p class="page-sub">情绪上来了不用硬扛，挑一个慢慢用。</p>

    <!-- ① 状态分流 -->
    <BaseCard data-test="state-card">
      <p class="card-title">我现在是……</p>
      <div class="chip-row">
        <BaseChip
          v-for="[key, label] in toolkit.states"
          :key="key"
          :active="stateKey === key"
          :data-test="`state-chip-${key}`"
          @click="stateKey = key"
        >
          {{ label }}
        </BaseChip>
      </div>
    </BaseCard>

    <!-- ② 推荐卡 -->
    <BaseCard data-test="rec-card">
      <p class="card-title">推荐给你</p>
      <p class="rec-hint">现在最合适的是这 {{ recMethods.length }} 条，挑一个马上用：</p>
      <div v-for="m in recMethods" :key="m.key" class="rec-item" :data-test="`rec-${m.key}`">
        <div class="rec-head">
          <span class="rec-name">{{ m.name }}</span>
          <span class="rec-time">{{ m.time }}</span>
          <button type="button" class="btn-primary" @click="startMethod(m.key)">立即开始</button>
        </div>
        <p class="rec-why">{{ m.why }}</p>
        <div v-if="expandedRecKey === m.key" class="rec-steps" data-test="rec-steps">
          <p class="steps-title">{{ m.name }}（{{ m.time }}）怎么做：</p>
          <p v-for="(s, i) in m.steps" :key="i" class="step-line">· {{ s }}</p>
        </div>
      </div>
    </BaseCard>

    <!-- ③ 呼吸训练 -->
    <BaseCard>
      <p class="card-title">呼吸训练</p>
      <p class="card-sub">跟着圆圈呼吸：吸气时圆变大，呼气时圆变小。</p>
      <div class="chip-row">
        <BaseChip data-test="breath-478" @click="openBreath('478')">4-7-8 呼吸</BaseChip>
        <BaseChip data-test="breath-belly" @click="openBreath('belly')">腹式呼吸</BaseChip>
        <BaseChip data-test="breath-box" @click="openBreath('box')">盒式呼吸</BaseChip>
        <BaseChip data-test="breath-sigh" @click="openBreath('sigh')">生理性叹息</BaseChip>
      </div>
    </BaseCard>

    <!-- ④ 三步冷静法（常驻静态卡，对齐旧版文案） -->
    <BaseCard>
      <p class="card-title">三步冷静法</p>
      <p class="card-sub">情绪上头时：① 暂停手上的动作 ② 做 3 次深呼吸 ③ 再决定下一步。</p>
    </BaseCard>

    <!-- ⑤ 蝴蝶拍（常驻静态卡，对齐旧版文案） -->
    <BaseCard>
      <p class="card-title">蝴蝶拍</p>
      <p class="card-sub">
        双臂在胸前交叉，双手轮流轻轻拍打自己肩膀，左右各一次为一组，做 6 到 8 组，边拍边告诉自己“我在安全的地方”。
      </p>
    </BaseCard>

    <!-- ⑥ 科学方法库（分组折叠；内容级更新，滚动容器不重建） -->
    <div data-test="toolkit-lib">
      <p class="lib-title">科学方法库</p>
      <p class="card-sub">都是经过科学验证、随时能用的方法，想细看哪组就点开。</p>
      <div class="toolkit-body" data-test="toolkit-body">
        <div v-for="[gkey, gname, gdesc] in toolkit.groups" :key="gkey" class="lib-group">
          <button
            type="button"
            class="group-head"
            :data-test="`group-${gkey}`"
            @click="toggleGroup(gkey)"
          >
            {{ gname }}（{{ methodsByGroup(gkey).length }} 条）
            {{ collapsedGroups.includes(gkey) ? "▲" : "▼" }}
          </button>
          <template v-if="!collapsedGroups.includes(gkey)">
            <p class="group-desc">{{ gdesc }}</p>
            <div
              v-for="m in methodsByGroup(gkey)"
              :key="m.key"
              class="method-card"
              :data-test="`method-${m.key}`"
            >
              <div class="method-head">
                <span class="rec-name">{{ m.name }}</span>
                <span class="rec-time">{{ m.time }}</span>
                <span class="evidence">{{ m.evidence }}</span>
              </div>
              <p class="rec-why">{{ m.why }}</p>
              <div v-if="openSteps.includes(m.key)" class="rec-steps" :data-test="`steps-${m.key}`">
                <p v-for="(s, i) in m.steps" :key="i" class="step-line">· {{ s }}</p>
              </div>
              <button type="button" class="btn-soft" @click="toggleSteps(m.key)">
                {{ openSteps.includes(m.key) ? "收起步骤" : "展开步骤" }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ⑦ 情绪日记 -->
    <BaseCard data-test="journal-card">
      <p class="card-title">情绪日记</p>
      <p class="card-sub">写三句话：刚才发生了什么、身体心里什么感觉、接下来想做点什么。</p>
      <div class="chip-row">
        <BaseChip data-test="journal-new" @click="journalEditOpen = true">写今天的日记</BaseChip>
        <BaseChip data-test="journal-all-btn" @click="journalAllOpen = true">查看全部日记</BaseChip>
      </div>
      <p v-if="recentPreview" class="journal-preview" data-test="journal-preview">
        {{ recentPreview }}
      </p>
    </BaseCard>

    <!-- 弹窗 -->
    <BreathGuideModal :open="breathOpen" :mode="breathMode" @close="breathOpen = false" />
    <JournalEditModal
      :open="journalEditOpen"
      :emotion-words="emotionWords"
      @close="journalEditOpen = false"
      @save="onJournalSave"
    />
    <JournalAllModal
      :open="journalAllOpen"
      :entries="journalEntries"
      @close="journalAllOpen = false"
      @remove="onJournalRemove"
    />
  </section>
</template>

<style scoped>
.tool-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.page-title {
  margin: 8px 0 0;
  font-size: 20px;
  color: var(--col-text);
}

.page-sub {
  margin: 0;
  font-size: 13px;
  color: var(--col-sub);
}

.card-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.card-sub {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--col-sub);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rec-hint {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--col-sub);
}

.rec-item {
  padding: 8px 0;
  border-top: 1px solid var(--col-line);
}

.rec-item:first-of-type {
  border-top: none;
}

.rec-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rec-name {
  font-weight: 600;
  color: var(--col-primary-dk);
}

.rec-time {
  font-size: 12px;
  color: var(--col-accent);
}

.rec-head .btn-primary {
  margin-left: auto;
}

.rec-why {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--col-sub);
}

.rec-steps {
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--col-chip);
  border-radius: 8px;
}

.steps-title {
  margin: 0 0 4px;
  font-size: 13px;
  color: var(--col-text);
}

.step-line {
  margin: 2px 0;
  font-size: 13px;
  color: var(--col-sub);
}

.lib-title {
  margin: 4px 0 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--col-text);
}

.group-head {
  width: 100%;
  text-align: left;
  border: none;
  border-radius: 8px;
  background: var(--col-chip);
  padding: 8px 12px;
  margin: 6px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--col-text);
  cursor: pointer;
}

.group-desc {
  margin: 4px 0 0 4px;
  font-size: 12px;
  color: var(--col-sub);
}

.method-card {
  border: 1px solid var(--col-line);
  border-radius: 10px;
  padding: 10px 12px;
  margin: 6px 0;
  background: var(--col-card);
}

.method-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.evidence {
  margin-left: auto;
  font-size: 12px;
  color: var(--col-sub);
}

.method-card .btn-soft {
  margin-top: 6px;
}

.btn-primary {
  border: none;
  border-radius: 999px;
  padding: 6px 18px;
  background: var(--col-primary);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.btn-soft {
  border: 1px solid var(--col-line);
  border-radius: 999px;
  padding: 5px 14px;
  background: var(--col-chip);
  color: var(--col-text);
  font-size: 12px;
  cursor: pointer;
}

.journal-preview {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--col-sub);
}
</style>
