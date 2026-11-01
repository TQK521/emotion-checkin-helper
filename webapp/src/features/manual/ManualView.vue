<script setup lang="ts">
/**
 * ManualView.vue —— 手册域（成长 Tab）：今日一课 / 课程目录 / 情绪词库。
 * 行为对齐旧版 src/pages_manual.py（三 Tab 固定栏、情绪推荐映射、目录分组折叠、
 * 词库搜索/展开/增词、详情上一篇/下一篇、返回保持原 Tab 与折叠状态）。
 * 详情翻页按 chapters.json 全局顺序循环（首课上一篇→末课，末课下一篇→首课）。
 */
import { computed, ref } from "vue";
import BaseCard from "@/shared/ui/BaseCard.vue";
import BaseModal from "@/shared/ui/BaseModal.vue";
import { allEmotions } from "@/core/stats/statistics";
import { useCheckinStore } from "@/core/store/use-checkin";
import type { Chapter, ChaptersFile, EmotionsFile } from "@/core/domain";
import chaptersJson from "@/assets/data/chapters.json";
import emotionsJson from "@/assets/data/emotions.json";

/* ---------- 静态数据（冻结契约） ---------- */
const chaptersFile = chaptersJson as unknown as ChaptersFile;
const emotionsFile = emotionsJson as unknown as EmotionsFile;
const chapters: Chapter[] = chaptersFile.chapters;
const groupOrder: string[] = chaptersFile.group_order;
const builtinEmotions: string[] = emotionsFile.emotions;
const builtinGlossary: Record<string, string> = emotionsFile.glossary;

/** 自定义词无释义兜底文案（对齐旧版 pages_manual.py fallback） */
const FALLBACK_GLOSS = "这个词是后来加入的，等你来定义它";

/**
 * 情绪 → 章节索引推荐映射（旧版 EMOTION_LESSON_MAP，56 内置情绪全覆盖）。
 * feature 私有常量；索引按 chapters.json 0 基顺序。
 */
const EMOTION_LESSON_MAP: Record<string, number> = {
  焦虑: 2, 紧张: 2, 心慌: 43, 烦躁: 39,
  拖延: 0, 疲惫: 54, 无聊: 40, 走神: 1,
  自责: 29, 迷茫: 58, 害怕: 43, 委屈: 16,
  没劲: 54, 想放弃: 64, 平静: 67, 期待: 67,
  麻木: 35, 憋屈: 38, 内疚: 29, 羞耻: 28,
  嫉妒: 19, 孤独: 12, 沮丧: 64, 无助: 64,
  不安: 43, 空落落: 12, 自我怀疑: 26, 反刍: 31,
  冒名顶替感: 26, 习得性无助: 64, 完美主义瘫痪: 4, 坐立不安: 39,
  高敏感: 27, 患得患失: 13, 戒断感: 50, 想哭: 37,
  愤怒: 38, 怀旧: 41, 敬畏: 42, 惊恐: 43,
  易被带跑: 44, 舍不得睡: 45, 情绪性嘴馋: 46, 信息过载: 47,
  冲动消费: 48, 假笑: 49, 躯体不适: 52, 深夜emo: 53,
  倦怠: 54, 虚无感: 58, 错失感: 59, 选择困难: 61,
  哀伤: 63, 感恩: 66, 三分钟热度: 51, 怕添麻烦: 23,
};

type ManualTab = "today" | "catalog" | "glossary";
const TABS: { key: ManualTab; label: string }[] = [
  { key: "today", label: "今日一课" },
  { key: "catalog", label: "课程目录" },
  { key: "glossary", label: "情绪词库" },
];

const store = useCheckinStore();

/* ---------- 视图状态（组件内 Tab 切换，路由不变） ---------- */
const activeTab = ref<ManualTab>("today");
/** detail 视图覆盖 tab 内容区；tab 栏仍固定可见 */
const view = ref<{ kind: "tab" } | { kind: "detail"; idx: number }>({ kind: "tab" });
/** 从哪个 Tab 进入详情，返回时还原 */
const detailReturnTab = ref<ManualTab>("today");

/* ---------- 今日一课 ---------- */
const todayIdx = ref<number | null>(null);

/** 最近一次打卡情绪（emotions 首词起）命中映射的章节索引；无记录/无映射返回 null */
function recoIndex(): number | null {
  const recs = store.data.records;
  if (!recs.length) return null;
  const last = recs[recs.length - 1];
  for (const emo of last.emotions ?? []) {
    const hit = EMOTION_LESSON_MAP[emo];
    if (hit !== undefined && hit >= 0 && hit < chapters.length) return hit;
  }
  return null;
}

/** 随机选一课时索引；exclude 为需排除的当前课（换一课时） */
function randomIdx(exclude?: number): number {
  const cand: number[] = [];
  for (let i = 0; i < chapters.length; i++) if (i !== exclude) cand.push(i);
  return cand[Math.floor(Math.random() * cand.length)];
}

/** 解析今日一课：有推荐用推荐，否则随机一课 */
function resolveToday(): void {
  const reco = recoIndex();
  if (reco !== null) {
    todayIdx.value = reco;
    return;
  }
  if (todayIdx.value === null) todayIdx.value = randomIdx();
}

const todayChapter = computed<Chapter | null>(() =>
  todayIdx.value === null ? null : chapters[todayIdx.value] ?? null,
);

function swapLesson(): void {
  todayIdx.value = randomIdx(todayIdx.value ?? undefined);
}

/* ---------- 目录 ---------- */
/** 分组折叠状态：默认第一组（group_order[0]）展开，其余收起（对齐旧版） */
const catalogCollapsed = ref<Set<string>>(new Set(groupOrder.slice(1)));

function toggleGroup(g: string): void {
  const next = new Set(catalogCollapsed.value);
  if (next.has(g)) next.delete(g);
  else next.add(g);
  catalogCollapsed.value = next;
}

/** 按分组顺序展开为 [{ group, chapters:[{ch, idx}] }] */
const catalogGroups = computed(
  () =>
    groupOrder.map((g) => ({
      group: g,
      items: chapters
        .map((ch, idx) => ({ ch, idx }))
        .filter((x) => x.ch.group === g),
    })),
);

/* ---------- 词库 ---------- */
const kw = ref("");
const expandedWords = ref<Set<string>>(new Set());

const allWords = computed<string[]>(() => allEmotions(store.data, builtinEmotions));

const filteredWords = computed<string[]>(() => {
  const k = kw.value.trim();
  return k ? allWords.value.filter((w) => w.includes(k)) : allWords.value;
});

function customGlossOf(word: string): string {
  const hit = (store.data.custom_emotions ?? []).find((e) => e.word === word);
  return hit?.gloss ?? "";
}

function glossOf(word: string): string {
  return builtinGlossary[word] || customGlossOf(word) || FALLBACK_GLOSS;
}

function toggleWord(w: string): void {
  const next = new Set(expandedWords.value);
  if (next.has(w)) next.delete(w);
  else next.add(w);
  expandedWords.value = next;
}

/* 添加自定义词（BaseModal） */
const addOpen = ref(false);
const addWord = ref("");
const addErr = ref("");

function openAdd(): void {
  addWord.value = "";
  addErr.value = "";
  addOpen.value = true;
}

async function confirmAdd(): Promise<void> {
  const ok = await store.addCustomEmotion(addWord.value);
  if (!ok) {
    addErr.value = "空词或已存在的情绪词";
    return;
  }
  addOpen.value = false;
  addWord.value = "";
  addErr.value = "";
}

/* ---------- 详情 ---------- */
const detailChapter = computed<Chapter | null>(() =>
  view.value.kind === "detail" ? chapters[view.value.idx] ?? null : null,
);

function openDetail(idx: number): void {
  detailReturnTab.value = activeTab.value;
  view.value = { kind: "detail", idx };
}

/** 上一篇(-1)/下一篇(+1)：全局顺序循环 */
function navDetail(delta: number): void {
  if (view.value.kind !== "detail") return;
  const n = chapters.length;
  view.value = { kind: "detail", idx: (view.value.idx + delta + n) % n };
}

function backFromDetail(): void {
  view.value = { kind: "tab" };
  activeTab.value = detailReturnTab.value;
  if (detailReturnTab.value === "today") resolveToday();
}

/* ---------- Tab 切换 ---------- */
function onSelectTab(tab: ManualTab): void {
  activeTab.value = tab;
  view.value = { kind: "tab" };
  if (tab === "today") resolveToday();
}

/* 初始：解析今日一课 */
resolveToday();
</script>

<template>
  <section class="manual">
    <!-- 固定 Tab 栏（sticky，不随内容滚动） -->
    <nav class="tabbar">
      <button
        v-for="t in TABS"
        :key="t.key"
        type="button"
        class="tab"
        :class="{ on: activeTab === t.key && view.kind === 'tab' }"
        :data-testid="`tab-${t.key}`"
        @click="onSelectTab(t.key)"
      >
        {{ t.label }}
      </button>
    </nav>

    <!-- 今日一课 -->
    <div v-if="view.kind === 'tab' && activeTab === 'today'" class="pane" data-testid="pane-today">
      <BaseCard v-if="todayChapter" data-testid="today-card">
        <div class="today-group">今日推荐 · {{ todayChapter.group }}</div>
        <h2 class="today-name" data-testid="today-name">{{ todayChapter.name }}</h2>
        <p class="today-essence">{{ todayChapter.essence }}</p>
        <div class="tip-block">
          <div class="tip-title">{{ todayChapter.tip_title }}</div>
          <div class="tip-text">{{ todayChapter.tip }}</div>
        </div>
        <div class="today-actions">
          <button type="button" class="btn-soft" data-testid="btn-read" @click="openDetail(todayIdx ?? 0)">
            读全文
          </button>
          <button type="button" class="btn-ghost" data-testid="btn-swap" @click="swapLesson">换一课</button>
        </div>
      </BaseCard>
    </div>

    <!-- 课程目录 -->
    <div v-else-if="view.kind === 'tab' && activeTab === 'catalog'" class="pane" data-testid="pane-catalog">
      <div v-for="g in catalogGroups" :key="g.group" class="catalog-group">
        <button
          type="button"
          class="group-head"
          :data-testid="`group-head-${g.group}`"
          @click="toggleGroup(g.group)"
        >
          {{ g.group }}（{{ g.items.length }} 课）{{ catalogCollapsed.has(g.group) ? "▲" : "▼" }}
        </button>
        <div v-if="!catalogCollapsed.has(g.group)" class="lesson-grid">
          <button
            v-for="x in g.items"
            :key="x.idx"
            type="button"
            class="lesson-row"
            data-testid="lesson-row"
            @click="openDetail(x.idx)"
          >
            <div class="lesson-name" data-testid="lesson-name">{{ x.ch.name }}</div>
            <div class="lesson-intro">{{ x.ch.intro }}</div>
          </button>
        </div>
      </div>
    </div>

    <!-- 情绪词库 -->
    <div v-else-if="view.kind === 'tab' && activeTab === 'glossary'" class="pane" data-testid="pane-glossary">
      <div class="gloss-top">
        <input
          v-model="kw"
          class="gloss-search"
          placeholder="搜索情绪词"
          data-testid="gloss-search"
        />
        <button type="button" class="btn-soft" data-testid="btn-add" @click="openAdd">＋ 添加情绪词</button>
      </div>
      <div class="word-grid">
        <div
          v-for="w in filteredWords"
          :key="w"
          class="word-card"
          data-testid="word-card"
          @click="toggleWord(w)"
        >
          <div class="word-name" data-testid="word-name">{{ w }}</div>
          <div v-if="expandedWords.has(w)" class="word-gloss" data-testid="word-gloss">
            {{ glossOf(w) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 课程详情（覆盖内容区，Tab 栏仍在） -->
    <div v-else class="pane detail" data-testid="pane-detail">
      <template v-if="detailChapter">
        <h2 class="detail-title" data-testid="detail-title">{{ detailChapter.name }}</h2>
        <template v-for="(blk, i) in detailChapter.full" :key="i">
          <h3 v-if="blk[0] === 'h2'" class="blk-h2" data-testid="blk-h2">{{ blk[1] }}</h3>
          <div v-else-if="blk[0] === 'bullet'" class="blk-bullet" data-testid="blk-bullet">· {{ blk[1] }}</div>
          <p v-else class="blk-body" data-testid="blk-body">{{ blk[1] }}</p>
        </template>
        <div v-if="detailChapter.tip_title || detailChapter.tip" class="tip-block" data-testid="tip-block">
          <div class="tip-title">{{ detailChapter.tip_title }}</div>
          <div class="tip-text">{{ detailChapter.tip }}</div>
        </div>
        <p v-if="detailChapter.warm" class="warm" data-testid="warm">{{ detailChapter.warm }}</p>
        <div class="detail-nav">
          <button type="button" class="btn-ghost" data-testid="btn-prev" @click="navDetail(-1)">← 上一篇</button>
          <button type="button" class="btn-ghost" data-testid="btn-next" @click="navDetail(1)">下一篇 →</button>
        </div>
        <button type="button" class="btn-soft back" data-testid="btn-back" @click="backFromDetail">← 返回</button>
      </template>
    </div>

    <!-- 添加情绪词弹窗 -->
    <BaseModal :open="addOpen" title="添加情绪词" @close="addOpen = false">
      <input v-model="addWord" class="add-input" placeholder="输入新的情绪词" data-testid="add-input" />
      <p v-if="addErr" class="add-err" data-testid="add-err">{{ addErr }}</p>
      <button type="button" class="btn-soft" data-testid="add-confirm" @click="confirmAdd">添加</button>
    </BaseModal>
  </section>
</template>

<style scoped>
.manual {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 固定 Tab 栏：随容器吸附，不随内容滚动 */
.tabbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  gap: 22px;
  background: var(--col-bg);
  padding: 4px 0 8px;
  border-bottom: 1px solid var(--col-line);
}

.tab {
  border: none;
  background: none;
  font-size: 15px;
  font-weight: 600;
  color: var(--col-sub);
  padding: 4px 2px;
  border-bottom: 2px solid transparent;
}

.tab.on {
  color: var(--col-primary-dk);
  border-bottom-color: var(--col-primary);
}

.pane {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 今日一课大卡 */
.today-group {
  font-size: 13px;
  color: var(--col-primary-dk);
}

.today-name {
  font-size: 22px;
  margin: 6px 0 4px;
}

.today-essence {
  margin: 0 0 12px;
  color: var(--col-text);
}

.tip-block {
  background: var(--col-soft);
  border-radius: 12px;
  padding: 12px 16px;
  margin: 4px 0 12px;
}

.tip-title {
  font-weight: 600;
  color: var(--col-primary-dk);
  margin-bottom: 2px;
}

.tip-text {
  color: var(--col-text);
}

.today-actions {
  display: flex;
  gap: 10px;
}

/* 按钮 */
.btn-soft {
  border: none;
  background: var(--col-soft);
  color: var(--col-primary-dk);
  border-radius: 8px;
  padding: 6px 16px;
  font-size: 14px;
}

.btn-ghost {
  border: 1px solid var(--col-line);
  background: var(--col-card);
  color: var(--col-sub);
  border-radius: 8px;
  padding: 6px 16px;
  font-size: 14px;
}

/* 目录 */
.catalog-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.group-head {
  border: none;
  background: var(--col-chip);
  color: var(--col-text);
  text-align: left;
  font-weight: 600;
  border-radius: 8px;
  padding: 8px 12px;
}

.lesson-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

/* 大屏（app-content 内 ≥720px）双列 */
@media (min-width: 720px) {
  .lesson-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.lesson-row {
  border: 1px solid var(--col-line);
  background: var(--col-card);
  border-radius: 10px;
  text-align: left;
  padding: 10px 12px;
}

.lesson-row:hover {
  border-color: var(--col-primary);
}

.lesson-name {
  font-weight: 600;
  color: var(--col-primary-dk);
}

.lesson-intro {
  font-size: 13px;
  color: var(--col-sub);
}

/* 词库 */
.gloss-top {
  display: flex;
  gap: 10px;
  align-items: center;
}

.gloss-search {
  flex: 1;
  border: 1px solid var(--col-line);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  background: var(--col-card);
}

.word-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

@media (min-width: 720px) {
  .word-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.word-card {
  background: var(--col-card);
  border: 1px solid var(--col-line);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
}

.word-name {
  font-weight: 600;
  color: var(--col-primary-dk);
}

.word-gloss {
  margin-top: 4px;
  font-size: 13px;
  color: var(--col-sub);
}

/* 详情 */
.detail-title {
  color: var(--col-primary-dk);
  font-size: 20px;
}

.blk-h2 {
  color: var(--col-primary-dk);
  font-size: 16px;
  margin: 8px 0 4px;
}

.blk-bullet {
  color: var(--col-primary-dk);
  padding: 2px 0;
}

.blk-body {
  margin: 4px 0;
  color: var(--col-text);
}

.warm {
  font-weight: 600;
  color: var(--col-primary-dk);
}

.detail-nav {
  display: flex;
  justify-content: space-between;
}

.back {
  align-self: flex-start;
}

.add-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid var(--col-line);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  margin-bottom: 10px;
}

.add-err {
  color: #c0392b;
  font-size: 13px;
  margin: 0 0 8px;
}
</style>
