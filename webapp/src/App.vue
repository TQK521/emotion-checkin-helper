<script setup lang="ts">
// App 根组件：导航 + 路由出口（内容区居中限宽）
import NavBar from "@/shared/ui/NavBar.vue";
</script>

<template>
  <div class="app-shell">
    <NavBar />
    <main class="app-main">
      <div class="app-content">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.app-content {
  max-width: 1000px;
  min-width: var(--content-min);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
