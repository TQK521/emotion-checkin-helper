<script setup lang="ts">
// NavBar —— 顶部导航（四个功能域入口）
const navItems = [
  { to: "/", label: "首页" },
  { to: "/record", label: "记录" },
  { to: "/tool", label: "工具箱" },
  { to: "/manual", label: "手册" },
];
</script>

<template>
  <nav class="navbar">
    <div class="brand">学习情绪打卡</div>
    <div class="nav-links">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
      >
        {{ item.label }}
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--col-card);
  border-bottom: 1px solid var(--col-line);
}

.brand {
  font-weight: 600;
  color: var(--col-primary-dk);
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 6px 14px;
  border-radius: 999px;
  color: var(--col-sub);
  font-size: 14px;
}

.nav-link:hover {
  background: var(--col-soft);
  color: var(--col-primary-dk);
}

.nav-link.router-link-active {
  background: var(--col-primary);
  color: #fff;
}
</style>
