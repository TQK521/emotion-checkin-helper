<script setup lang="ts">
// BaseCard —— 圆角卡片容器（对齐 Python rounded_card）
withDefaults(
  defineProps<{
    /** 内边距（CSS 值），默认 16px */
    padding?: string;
    /** 是否带极淡描边 */
    outlined?: boolean;
  }>(),
  { padding: "16px", outlined: false },
);
</script>

<template>
  <section class="base-card" :class="{ outlined }" :style="{ padding }">
    <slot />
  </section>
</template>

<style scoped>
.base-card {
  background: var(--col-card);
  border-radius: var(--card-radius);
  border: 1px solid var(--col-line);
}

.base-card.outlined {
  border-color: var(--col-line);
  box-shadow: none;
}
</style>
