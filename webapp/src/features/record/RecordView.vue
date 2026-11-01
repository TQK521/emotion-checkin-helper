<script setup lang="ts">
/**
 * RecordView.vue —— 记录洞察域（对齐旧版 src/pages_record.py）
 * 统计三卡 / 周一开头日历（画点+翻月+回今天+当天记录）/ 本周情绪横条 /
 * 本周复盘（top3+主要场景+肯定语）/ 分页历史记录（按天分组+触底加载+删除确认）/ 备份入口。
 * 数据源唯一：useCheckinStore（Pinia），统计口径一律走 core/stats/statistics 纯函数。
 */
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import BaseCard from "@/shared/ui/BaseCard.vue";
import BaseModal from "@/shared/ui/BaseModal.vue";
import { useCheckinStore } from "@/core/store/use-checkin";
import {
  calendarDates,
  fmtEmotions,
  monthDays,
  recordsOnDate,
  sceneCounts,
  topEmotions,
} from "@/core/stats/statistics";
import { parseDate, todayStr } from "@/shared/lib/date";
import type { CheckinRecord } from "@/core/domain";

// ── 本周复盘肯定语映射表（旧版 pages_record.py 提取，feature 私有常量）──
const AFFIRMATIONS: Record<string, string> = {
  焦虑: "焦虑说明你在乎，允许自己慢慢来，一步一步走。",
  疲惫: "疲惫是身体在提醒你休息，好好照顾自己。",
  难过: "难过的时候允许自己哭一会儿，情绪没有对错。",
  生气: "生气说明你有边界，这份感受值得被看见。",
  孤独: "孤独不是你的错，你正在学习和自己相处。",
  压力: "压力之下你还在坚持，这本身就很了不起。",
  自我否定: "你已经做得很好了，别对自己太苛刻。",
  委屈: "委屈是真实的，允许自己被理解。",
};
const AFFIRM_FALLBACK = "这周的每一次记录，都是你照顾自己的证明。";
const WEEK_EMPTY_TEXT = "这周还没记录，没关系。下一次记录时，这里会慢慢长出你的复盘。";

const WEEK_HEADERS = ["一", "二", "三", "四", "五", "六", "日"];
/** 历史记录首批渲染条数（对齐旧版 _HIST_PAGE=40，核心约束七） */
const HIST_PAGE = 40;

const store = useCheckinStore();

// ── 统计三卡（累计 / 今日 / 本月记录天数）──
const totalCount = computed(() => store.totalCount);
const todayCount = computed(() => store.todayCount);
const monthDayCount = computed(() => monthDays(store.data));

// ── 日历（周一开头网格）──
const calYear = ref(new Date().getFullYear());
const calMonth = ref(new Date().getMonth() + 1);
const selectedDate = ref(todayStr());

interface CalCell {
  date: string | null;
  day: number;
  recorded: boolean;
  isToday: boolean;
}

const recordedDates = computed(() => calendarDates(store.data, calYear.value, calMonth.value));

const cells = computed<CalCell[]>(() => {
  const first = new Date(calYear.value, calMonth.value - 1, 1);
  // getDay(): 0=周日 → 周一开头列序（对齐 mondayOf）
  const startCol = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(calYear.value, calMonth.value, 0).getDate();
  const rec = recordedDates.value;
  const today = todayStr();
  const out: CalCell[] = [];
  for (let i = 0; i < startCol; i++) out.push({ date: null, day: 0, recorded: false, isToday: false });
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = `${calYear.value}-${String(calMonth.value).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    out.push({ date: ds, day: d, recorded: rec.has(ds), isToday: ds === today });
  }
  while (out.length % 7 !== 0) out.push({ date: null, day: 0, recorded: false, isToday: false });
  return out;
});

function prevMonth(): void {
  calMonth.value -= 1;
  if (calMonth.value === 0) {
    calMonth.value = 12;
    calYear.value -= 1;
  }
}

function nextMonth(): void {
  calMonth.value += 1;
  if (calMonth.value === 13) {
    calMonth.value = 1;
    calYear.value += 1;
  }
}

function backToday(): void {
  const now = new Date();
  calYear.value = now.getFullYear();
  calMonth.value = now.getMonth() + 1;
  selectedDate.value = todayStr();
}

function pickDate(ds: string | null): void {
  if (ds) selectedDate.value = ds;
}

// ── 当天记录（点击日历日期展示）──
const dayRecords = computed(() => recordsOnDate(store.data, selectedDate.value));

function dayLabel(ds: string): string {
  const d = parseDate(ds);
  return d ? `${d.getMonth() + 1}月${d.getDate()}日` : ds;
}

const dayDetailTitle = computed(() => {
  if (dayRecords.value.length === 0) return "";
  return `${dayLabel(selectedDate.value)} 共 ${dayRecords.value.length} 次`;
});

const dayLines = computed(() =>
  [...dayRecords.value]
    .sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0))
    .map((r) => {
      let line = `${r.time || "—"} · ${fmtEmotions(r)}`;
      if (r.action) line += ` · ${r.action}`;
      return line;
    }),
);

const dayEmptyText = computed(() => {
  const label = dayLabel(selectedDate.value);
  return selectedDate.value > todayStr()
    ? `${label} 还没到。`
    : `${label} 没有记录。没记录也没关系，下一次难受时来记就行。`;
});

// ── 本周情绪横条（top5 降序，比例=条数/本周最高频）──
const weekEmos = computed<[string, number][]>(() => topEmotions(store.data, 5));
const emoMax = computed(() => (weekEmos.value.length > 0 ? weekEmos.value[0][1] : 1));

function emoPct(cnt: number): number {
  return Math.round((cnt / emoMax.value) * 100);
}

// ── 本周复盘（高频 top3 + 主要场景 + 肯定语）──
const review = computed<{ top3: string; topScene: string; affirm: string } | null>(() => {
  if (weekEmos.value.length === 0) return null;
  const top3 = weekEmos
    .value
    .slice(0, 3)
    .map(([w]) => w)
    .join("、");
  const scenes = sceneCounts(store.data);
  let topScene = "—";
  let max = 0;
  for (const [s, c] of scenes) {
    if (c > max) {
      max = c;
      topScene = s;
    }
  }
  const affirm = AFFIRMATIONS[weekEmos.value[0][0]] ?? AFFIRM_FALLBACK;
  return { top3, topScene, affirm };
});

// ── 历史记录区（默认收起；展开后按天分组 + 分页渲染）──
const histOpen = ref(false);
const histShown = ref(HIST_PAGE);

interface HistEntry {
  origIndex: number;
  rec: CheckinRecord;
}

/** 全部记录按时间倒序（保留原始下标供 removeRecord） */
const histSorted = computed<HistEntry[]>(() =>
  store.data.records
    .map((rec, origIndex) => ({ rec, origIndex }))
    .sort((a, b) => (a.rec.ts < b.rec.ts ? 1 : a.rec.ts > b.rec.ts ? -1 : 0)),
);

type HistItem =
  | { kind: "day"; date: string; label: string }
  | { kind: "rec"; origIndex: number; rec: CheckinRecord };

const histItems = computed<HistItem[]>(() => {
  const slice = histSorted.value.slice(0, histShown.value);
  const items: HistItem[] = [];
  let lastDay: string | null = null;
  for (const { rec, origIndex } of slice) {
    if (rec.date !== lastDay) {
      items.push({ kind: "day", date: rec.date, label: dayLabel(rec.date) });
      lastDay = rec.date;
    }
    items.push({ kind: "rec", origIndex, rec });
  }
  return items;
});

function toggleHistory(): void {
  histOpen.value = !histOpen.value;
  if (histOpen.value) histShown.value = HIST_PAGE;
}

/** 触底加载下一批（jsdom 测试直接调用此函数断言分批逻辑） */
function loadMore(): void {
  if (histShown.value < histSorted.value.length) histShown.value += HIST_PAGE;
}

/** 滚动近底部（>93%）自动加载下一批；scroll 不冒泡，用 capture 捕获 .app-main 滚动 */
function onPageScroll(): void {
  if (!histOpen.value || histShown.value >= histSorted.value.length) return;
  const main = document.querySelector(".app-main");
  const el: Element | null =
    main && main.scrollHeight > main.clientHeight ? main : document.scrollingElement;
  if (!el || el.scrollHeight === 0) return;
  const ratio = (el.scrollTop + el.clientHeight) / el.scrollHeight;
  if (ratio > 0.93) loadMore();
}

onMounted(() => window.addEventListener("scroll", onPageScroll, true));
onBeforeUnmount(() => window.removeEventListener("scroll", onPageScroll, true));

function histText(r: CheckinRecord): string {
  let s = fmtEmotions(r);
  if (r.action) s += ` · ${r.action}`;
  const scene = r.scene || "—";
  const inten = r.intensity ? `强度${r.intensity}` : "—";
  s += ` · ${scene} · ${inten}`;
  return `${r.time || "—"}  ${s}`;
}

// ── 删除确认（BaseModal，禁止 window.confirm）──
const pendingDelete = ref<number | null>(null);
const deleteFeedback = ref("");
let fbTimer: ReturnType<typeof setTimeout> | undefined;

const pendingRec = computed<CheckinRecord | null>(() => {
  if (pendingDelete.value === null) return null;
  return store.data.records[pendingDelete.value] ?? null;
});

function askDelete(origIndex: number): void {
  pendingDelete.value = origIndex;
}

function cancelDelete(): void {
  pendingDelete.value = null;
}

async function confirmDelete(): Promise<void> {
  const idx = pendingDelete.value;
  pendingDelete.value = null;
  if (idx === null) return;
  await store.removeRecord(idx);
  deleteFeedback.value = "已删除，过去的就让它过去。";
  clearTimeout(fbTimer);
  fbTimer = setTimeout(() => {
    deleteFeedback.value = "";
  }, 2500);
}

// ── 备份数据入口（store.backup 返回适配器标识，据此展示）──
const backupResult = ref("");

async function doBackup(): Promise<void> {
  const tag = await store.backup();
  backupResult.value = tag ? `备份完成（${tag}）` : "暂无可用存储，备份未执行。";
}

defineExpose({ loadMore, toggleHistory });
</script>

<template>
  <div class="record-page">
    <!-- 页头：标题 + 备份入口 + 历史展开开关 -->
    <header class="rec-head">
      <h2 class="rec-title">打卡记录</h2>
      <div class="head-actions">
        <button type="button" class="backup-btn" data-test="backup-btn" @click="doBackup">
          备份数据
        </button>
        <button type="button" class="hist-toggle" data-test="history-toggle" @click="toggleHistory">
          {{ histOpen ? "📁 收起历史记录" : "📖 查看历史记录" }}
        </button>
      </div>
    </header>
    <p v-if="backupResult" data-test="backup-result" class="backup-result">{{ backupResult }}</p>

    <!-- 统计三卡 -->
    <div class="stat-row">
      <BaseCard class="stat-card">
        <p class="stat-name">累计次数</p>
        <p class="stat-num" data-test="stat-total">{{ totalCount }}</p>
      </BaseCard>
      <BaseCard class="stat-card">
        <p class="stat-name">今日次数</p>
        <p class="stat-num" data-test="stat-today">{{ todayCount }}</p>
      </BaseCard>
      <BaseCard class="stat-card">
        <p class="stat-name">本月记录天数</p>
        <p class="stat-num" data-test="stat-month">{{ monthDayCount }}</p>
      </BaseCard>
    </div>

    <!-- 日历 -->
    <BaseCard padding="12px" outlined>
      <div class="cal-head">
        <button type="button" class="cal-nav" data-test="cal-today" @click="backToday">今天</button>
        <button type="button" class="cal-nav" data-test="cal-prev" @click="prevMonth">◀</button>
        <span class="cal-title" data-test="cal-title">{{ calYear }} 年 {{ calMonth }} 月</span>
        <button type="button" class="cal-nav cal-next" data-test="cal-next" @click="nextMonth">▶</button>
      </div>
      <div class="cal-grid">
        <span v-for="w in WEEK_HEADERS" :key="w" class="cal-week">{{ w }}</span>
        <template v-for="(c, i) in cells" :key="i">
          <button
            v-if="c.date"
            type="button"
            class="cal-cell"
            :class="{ recorded: c.recorded, selected: c.date === selectedDate, today: c.isToday }"
            :data-date="c.date"
            :data-recorded="c.recorded ? 'true' : 'false'"
            @click="pickDate(c.date)"
          >
            <span class="cal-day">{{ c.day }}</span>
            <span v-if="c.recorded" class="cal-dot" />
          </button>
          <span v-else class="cal-cell blank" />
        </template>
      </div>
      <div class="day-detail" data-test="day-detail">
        <template v-if="dayRecords.length > 0">
          <p class="day-title">{{ dayDetailTitle }}</p>
          <p v-for="(line, i) in dayLines" :key="i" class="day-line">{{ line }}</p>
        </template>
        <p v-else class="day-empty">{{ dayEmptyText }}</p>
      </div>
    </BaseCard>

    <!-- 本周情绪横条 -->
    <BaseCard padding="12px" outlined>
      <h3 class="block-title">本周情绪</h3>
      <p v-if="weekEmos.length === 0" class="week-empty">这周还没记录，没关系。</p>
      <div v-for="[emo, cnt] in weekEmos" :key="emo" class="emo-row">
        <span class="emo-name">{{ emo }}</span>
        <div class="emo-track">
          <div
            class="emo-bar"
            :data-count="cnt"
            :data-pct="emoPct(cnt)"
            :style="{ width: emoPct(cnt) + '%' }"
          />
        </div>
        <span class="emo-count">{{ cnt }}</span>
      </div>
    </BaseCard>

    <!-- 本周复盘 -->
    <BaseCard padding="12px" outlined>
      <h3 class="block-title">本周复盘</h3>
      <p v-if="!review" class="week-empty" data-test="review-empty">{{ WEEK_EMPTY_TEXT }}</p>
      <template v-else>
        <p class="review-line" data-test="review-top3">高频情绪：{{ review.top3 }}</p>
        <p class="review-line sub" data-test="review-scene">主要场景：{{ review.topScene }}</p>
        <p class="review-line affirm" data-test="review-affirm">{{ review.affirm }}</p>
      </template>
    </BaseCard>

    <!-- 历史记录区（默认收起） -->
    <section v-if="histOpen" data-test="history-section">
      <h3 class="block-title hist-head">📖 历史记录</h3>
      <p v-if="deleteFeedback" data-test="delete-feedback" class="delete-fb">{{ deleteFeedback }}</p>
      <div data-test="history-list">
        <template v-for="(item, i) in histItems" :key="i">
          <div v-if="item.kind === 'day'" class="hist-day" :data-date="item.date">{{ item.label }}</div>
          <div v-else class="hist-row" data-test="hist-rec">
            <span class="hist-text">{{ histText(item.rec) }}</span>
            <button type="button" class="hist-del" data-test="delete-btn" @click="askDelete(item.origIndex)">
              删除
            </button>
          </div>
        </template>
        <p v-if="histSorted.length === 0" class="week-empty">
          还没有记录。学习时感到难受，就来这里把它说出来。
        </p>
      </div>
    </section>

    <!-- 删除确认弹窗（Teleport 到 body） -->
    <BaseModal :open="pendingDelete !== null" title="删除记录" @close="cancelDelete">
      <p v-if="pendingRec" class="modal-rec">
        确认删除这条记录吗？<br /><br />
        {{ fmtEmotions(pendingRec) }}<br /><br />
        删除后无法恢复，仅删除本条。
      </p>
      <div class="modal-actions">
        <button type="button" class="modal-btn" data-test="cancel-delete" @click="cancelDelete">取消</button>
        <button type="button" class="modal-btn danger" data-test="confirm-delete" @click="confirmDelete">
          确认删除
        </button>
      </div>
    </BaseModal>
  </div>
</template>

<style scoped>
.record-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rec-title {
  font-size: 20px;
  color: var(--col-text);
  margin: 0;
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.backup-btn {
  border: none;
  background: none;
  color: var(--col-sub);
  font-size: 12px;
  cursor: pointer;
}

.backup-btn:hover {
  color: var(--col-primary-dk);
}

.hist-toggle {
  border: none;
  background: none;
  color: var(--col-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.hist-toggle:hover {
  color: var(--col-primary-dk);
}

.backup-result {
  margin: 0;
  font-size: 13px;
  color: var(--col-primary-dk);
}

/* 统计三卡 */
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.stat-name {
  margin: 0;
  font-size: 12px;
  color: var(--col-sub);
  text-align: center;
}

.stat-num {
  margin: 4px 0 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--col-primary-dk);
  text-align: center;
}

/* 日历 */
.cal-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.cal-nav {
  border: none;
  background: none;
  color: var(--col-sub);
  font-size: 14px;
  cursor: pointer;
}

.cal-nav:hover {
  color: var(--col-primary-dk);
}

.cal-title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  color: var(--col-text);
}

.cal-next {
  text-align: right;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cal-week {
  text-align: center;
  font-size: 12px;
  color: var(--col-sub);
  padding: 2px 0;
}

.cal-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border: none;
  background: none;
  border-radius: 8px;
  padding: 6px 0;
  cursor: pointer;
  color: var(--col-text);
}

.cal-cell:hover {
  background: var(--col-chip);
}

.cal-cell.selected {
  background: var(--col-soft);
}

.cal-cell.today .cal-day {
  color: var(--col-primary-dk);
  font-weight: 700;
}

.cal-cell.recorded .cal-day {
  color: var(--col-primary-dk);
}

.cal-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--col-primary);
}

.day-detail {
  margin-top: 8px;
  font-size: 13px;
  color: var(--col-sub);
}

.day-title {
  margin: 0 0 4px;
  color: var(--col-text);
  font-weight: 600;
}

.day-line,
.day-empty {
  margin: 2px 0;
}

/* 本周情绪横条 */
.block-title {
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--col-text);
}

.week-empty {
  margin: 0;
  font-size: 13px;
  color: var(--col-sub);
}

.emo-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}

.emo-name {
  width: 56px;
  font-size: 13px;
  color: var(--col-text);
}

.emo-track {
  flex: 1;
  height: 12px;
  background: var(--col-chip);
  border-radius: 6px;
  overflow: hidden;
}

.emo-bar {
  height: 100%;
  background: var(--col-primary);
  border-radius: 6px;
}

.emo-count {
  width: 24px;
  text-align: right;
  font-size: 13px;
  color: var(--col-sub);
}

/* 本周复盘 */
.review-line {
  margin: 3px 0;
  font-size: 13px;
  color: var(--col-text);
}

.review-line.sub {
  color: var(--col-sub);
}

.review-line.affirm {
  margin-top: 6px;
  color: var(--col-primary-dk);
}

/* 历史记录 */
.hist-head {
  margin: 8px 0 4px;
  color: var(--col-primary-dk);
}

.delete-fb {
  margin: 0 0 4px;
  font-size: 13px;
  color: var(--col-primary-dk);
}

.hist-day {
  margin: 10px 0 2px;
  font-weight: 700;
  font-size: 14px;
  text-align: center;
  color: var(--col-primary-dk);
}

.hist-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--col-chip);
  border-radius: 10px;
  padding: 8px 12px;
  margin: 3px 0;
}

.hist-text {
  flex: 1;
  font-size: 13px;
  color: var(--col-text);
}

.hist-del {
  border: none;
  background: none;
  color: var(--col-sub);
  font-size: 13px;
  cursor: pointer;
}

.hist-del:hover {
  color: #d96666;
}

/* 弹窗按钮 */
.modal-rec {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--col-text);
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.modal-btn {
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid var(--col-line);
  background: var(--col-card);
  color: var(--col-text);
  cursor: pointer;
}

.modal-btn.danger {
  background: var(--col-primary);
  border-color: var(--col-primary);
  color: #fff;
}
</style>
