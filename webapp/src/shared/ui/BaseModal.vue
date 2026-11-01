<script setup lang="ts">
// BaseModal —— 通用弹窗（对齐 Python soft_showinfo 语义的轻量封装）
const props = withDefaults(
  defineProps<{
    /** 是否显示 */
    open: boolean;
    /** 标题 */
    title?: string;
    /** 点击遮罩是否可关闭 */
    dismissible?: boolean;
  }>(),
  { title: "", dismissible: true },
);

const emit = defineEmits<{ close: [] }>();

function onMask(): void {
  if (props.dismissible) emit("close");
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-mask" @click.self="onMask">
        <div class="modal-panel">
          <header v-if="title" class="modal-head">
            <span class="modal-title">{{ title }}</span>
            <button type="button" class="modal-close" aria-label="关闭" @click="emit('close')">
              ×
            </button>
          </header>
          <div class="modal-body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(68, 68, 68, 0.35);
}

.modal-panel {
  width: min(420px, calc(100vw - 48px));
  max-height: calc(100vh - 96px);
  display: flex;
  flex-direction: column;
  background: var(--col-card);
  border-radius: var(--card-radius);
  border: 1px solid var(--col-line);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--col-line);
}

.modal-title {
  font-weight: 600;
  color: var(--col-text);
}

.modal-close {
  border: none;
  background: none;
  font-size: 20px;
  line-height: 1;
  color: var(--col-sub);
  cursor: pointer;
  padding: 0 4px;
}

.modal-close:hover {
  color: var(--col-text);
}

.modal-body {
  padding: 18px;
  overflow: auto;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.18s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
