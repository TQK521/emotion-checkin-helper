<script setup lang="ts">
/**
 * ImportWizard.vue —— 桌面版首次启动导入向导（波3）
 * 仅 Tauri 环境生效：应用数据目录无记录时提示用户导入旧版 checkin_data.json，
 * 经 dialog 选文件 → importer 迁移 → 写入数据目录（对齐 v2 方案 4.2 + 第七节 5）。
 * 浏览器开发态（localStorage）不出现。
 */
import { onMounted, ref } from "vue";
import { isTauri, invoke } from "@tauri-apps/api/core";
import { useCheckinStore } from "@/core/store/use-checkin";
import { migrateOldData } from "@/services/importer/importer";

const store = useCheckinStore();
const show = ref(false);
const importing = ref(false);
const error = ref("");
const done = ref(false);

/** 是否"尚无数据"（records 空且从未开始打卡） */
function isEmpty(): boolean {
  return store.data.records.length === 0 && !store.data.start_date;
}

onMounted(async () => {
  if (!isTauri()) return;
  if (!store.loaded) await store.load();
  // loaded 后数据仍空才显示（导入或跳过，本次会话不再自动弹出）
  show.value = isEmpty();
});

async function doImport() {
  importing.value = true;
  error.value = "";
  try {
    const raw = await invoke<string | null>("pick_import_file");
    if (raw == null) return; // 用户取消，保留弹窗
    const parsed: unknown = JSON.parse(raw);
    store.data = migrateOldData(parsed);
    await store.save();
    done.value = true;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    importing.value = false;
  }
}

function skip() {
  show.value = false;
}
</script>

<template>
  <Teleport to="body">
    <Transition name="wizard">
      <div v-if="show" class="import-overlay">
        <div class="import-card">
          <h2 class="import-title">导入旧版数据</h2>
          <p class="import-desc">
            检测到当前还没有打卡记录。如果你在旧版「学习情绪打卡」里记过数据，
            可以导入旧版数据文件（checkin_data.json），历史记录会完整带过来。
          </p>
          <p v-if="done" class="import-done">导入成功，历史记录已就位。</p>
          <p v-if="error" class="import-error">导入失败：{{ error }}</p>
          <div class="import-actions">
            <button class="import-btn primary" :disabled="importing" @click="doImport">
              {{ importing ? "读取中…" : "选择旧数据文件" }}
            </button>
            <button class="import-btn" :disabled="importing" @click="skip">跳过，从今天开始</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.import-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
}

.import-card {
  width: min(480px, 88vw);
  background: var(--col-bg);
  border: 1px solid var(--col-soft);
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.import-title {
  margin: 0 0 12px;
  font-size: 18px;
  color: var(--col-primary);
}

.import-desc {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--col-text);
}

.import-done {
  color: var(--col-primary);
  font-size: 14px;
  margin: 0 0 12px;
}

.import-error {
  color: #c0392b;
  font-size: 13px;
  margin: 0 0 12px;
}

.import-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.import-btn {
  padding: 9px 18px;
  border-radius: 8px;
  border: 1px solid var(--col-soft);
  background: var(--col-bg);
  color: var(--col-text);
  font-size: 14px;
  cursor: pointer;
}

.import-btn.primary {
  background: var(--col-primary);
  border-color: var(--col-primary);
  color: #fff;
}

.import-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.wizard-enter-active,
.wizard-leave-active {
  transition: opacity 0.2s;
}

.wizard-enter-from,
.wizard-leave-to {
  opacity: 0;
}
</style>
