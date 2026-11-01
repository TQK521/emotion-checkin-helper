<script setup lang="ts">
// JournalEditModal —— 情绪日记三问弹窗（对齐 pages_tool.py JournalDialog）
// 事件/感受/行动三个输入；情绪词 chips 点击追加到感受框（顿号分隔）。
import { ref, watch } from "vue";
import BaseModal from "@/shared/ui/BaseModal.vue";
import BaseChip from "@/shared/ui/BaseChip.vue";

const props = defineProps<{
  open: boolean;
  /** 全部可选情绪词（内置 56 + 自定义） */
  emotionWords: string[];
}>();

const emit = defineEmits<{
  close: [];
  save: [event: string, feeling: string, action: string];
}>();

const eventText = ref("");
const feelingText = ref("");
const actionText = ref("");

// 每次打开重置输入
watch(
  () => props.open,
  (v) => {
    if (v) {
      eventText.value = "";
      feelingText.value = "";
      actionText.value = "";
    }
  },
);

/** 点击情绪词 → 追加到感受框末尾（顿号分隔，对齐 _append_emotion） */
function appendWord(word: string): void {
  const cur = feelingText.value.trim();
  feelingText.value = cur ? (cur.endsWith("、") ? cur : cur + "、") + word : word;
}

function onSave(): void {
  emit("save", eventText.value.trim(), feelingText.value.trim(), actionText.value.trim());
}
</script>

<template>
  <BaseModal :open="open" title="情绪日记" @close="emit('close')">
    <div data-test="journal-edit">
      <p class="j-head">记三句话就够</p>

      <p class="q">刚才发生了什么事？</p>
      <p class="q-hint">1-2 句写客观事实就好，不用加对错评价</p>
      <textarea
        v-model="eventText"
        data-test="journal-event"
        class="j-input"
        rows="2"
        placeholder="例如：机房值班出了小故障"
      ></textarea>

      <p class="q">我身体和心里是什么感觉？</p>
      <p class="q-hint">可以写身体反应，也可以点下面的情绪词</p>
      <textarea
        v-model="feelingText"
        data-test="journal-feeling"
        class="j-input"
        rows="2"
      ></textarea>

      <div class="emo-row">
        <BaseChip
          v-for="w in emotionWords"
          :key="w"
          data-test="emo-chip"
          @click="appendWord(w)"
        >
          {{ w }}
        </BaseChip>
      </div>

      <p class="q q-soft">接下来我想做点什么？（选填）</p>
      <p class="q-hint">可以是 1 件小事，也可以是一句想对自己说的话</p>
      <textarea
        v-model="actionText"
        data-test="journal-action"
        class="j-input"
        rows="2"
      ></textarea>

      <div class="j-actions">
        <button type="button" class="btn-primary" data-test="journal-save" @click="onSave">
          记下了
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.j-head {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--col-primary-dk);
}

.q {
  margin: 12px 0 2px;
  font-size: 13px;
  font-weight: 600;
  color: var(--col-text);
}

.q-soft {
  font-weight: 400;
  color: var(--col-sub);
}

.q-hint {
  margin: 0;
  font-size: 12px;
  color: var(--col-sub);
}

.j-input {
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
  border: 1px solid var(--col-line);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  font-family: var(--font-family);
  resize: vertical;
}

.emo-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.j-actions {
  margin-top: 14px;
  text-align: center;
}

.btn-primary {
  border: none;
  border-radius: 999px;
  padding: 8px 30px;
  background: var(--col-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
</style>
