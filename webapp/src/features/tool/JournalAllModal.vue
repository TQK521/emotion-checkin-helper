<script setup lang="ts">
// JournalAllModal —— 全部日记弹窗（对齐 pages_tool.py _show_journal_all）
// 倒序展示、按天分组（每天大日期一次）、每条可删除；旧 text 格式经 journalFields 兼容。
import { computed } from "vue";
import BaseModal from "@/shared/ui/BaseModal.vue";
import type { JournalEntry } from "@/core/domain";
import { journalFields } from "./tool-data";

const props = defineProps<{
  open: boolean;
  entries: JournalEntry[];
}>();

const emit = defineEmits<{
  close: [];
  /** 删除底层数组下标（非展示序） */
  remove: [index: number];
}>();

interface EntryRow {
  /** 底层数组下标 */
  index: number;
  time: string;
  event: string;
  feeling: string;
  action: string;
}

type DisplayRow = { kind: "day"; day: string } | { kind: "entry"; row: EntryRow };

/** 倒序行（新的在前），新一天首行插日期分组标题 */
const rows = computed<DisplayRow[]>(() => {
  const out: DisplayRow[] = [];
  let lastDay: string | null = null;
  for (let i = props.entries.length - 1; i >= 0; i--) {
    const e = props.entries[i];
    const [event, feeling, action] = journalFields(e);
    const date = e.date ?? "";
    if (date !== lastDay) {
      out.push({ kind: "day", day: date });
      lastDay = date;
    }
    out.push({
      kind: "entry",
      row: { index: i, time: e.time ?? "—", event, feeling, action },
    });
  }
  return out;
});

const countText = computed(() =>
  props.entries.length ? `情绪日记 · 共 ${props.entries.length} 篇` : "",
);
</script>

<template>
  <BaseModal :open="open" title="情绪日记 · 全部" @close="emit('close')">
    <div data-test="journal-all">
      <p v-if="!entries.length" class="empty">还没有写过日记。难受的时候，来写三句话。</p>
      <template v-else>
        <p class="all-count" data-test="journal-all-count">{{ countText }}</p>
        <div v-for="(r, i) in rows" :key="i">
          <p v-if="r.kind === 'day'" class="day-head" data-test="j-day">{{ r.day }}</p>
          <div v-else class="j-card" :data-test="`j-card-${r.row.index}`">
            <div class="j-card-head">
              <span class="j-time">{{ r.row.time }}</span>
              <button
                type="button"
                class="j-del"
                :data-test="`j-del-${r.row.index}`"
                @click="emit('remove', r.row.index)"
              >
                删除
              </button>
            </div>
            <p v-if="r.row.event" class="j-line">📌 事件：{{ r.row.event }}</p>
            <p v-if="r.row.feeling" class="j-line">💭 感受：{{ r.row.feeling }}</p>
            <p v-if="r.row.action" class="j-line j-line-soft">✨ 打算：{{ r.row.action }}</p>
          </div>
        </div>
      </template>
    </div>
  </BaseModal>
</template>

<style scoped>
.empty {
  margin: 8px 0;
  font-size: 13px;
  color: var(--col-sub);
}

.all-count {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.day-head {
  margin: 12px 0 2px;
  font-size: 14px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.j-card {
  border: 1px solid var(--col-line);
  border-radius: 10px;
  padding: 8px 12px;
  margin: 4px 0;
  background: var(--col-bg);
}

.j-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.j-time {
  font-size: 12px;
  color: var(--col-sub);
}

.j-del {
  border: none;
  background: none;
  color: var(--col-sub);
  font-size: 12px;
  cursor: pointer;
}

.j-del:hover {
  color: #b00020;
}

.j-line {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--col-text);
}

.j-line-soft {
  color: var(--col-sub);
}
</style>
