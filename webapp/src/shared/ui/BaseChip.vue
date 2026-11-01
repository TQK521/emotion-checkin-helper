<script setup lang="ts">
// BaseChip —— 标签/选择块（对齐首页情绪/场景 chips）
withDefaults(
  defineProps<{
    /** 选中态 */
    active?: boolean;
    /** 禁用态 */
    disabled?: boolean;
  }>(),
  { active: false, disabled: false },
);

defineEmits<{ click: [] }>();
</script>

<template>
  <button
    type="button"
    class="base-chip"
    :class="{ active, disabled }"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<style scoped>
.base-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--col-line);
  background: var(--col-chip);
  color: var(--col-text);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.base-chip:hover:not(.disabled) {
  border-color: var(--col-primary);
  color: var(--col-primary-dk);
}

.base-chip.active {
  background: var(--col-primary);
  border-color: var(--col-primary);
  color: #fff;
}

.base-chip.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
