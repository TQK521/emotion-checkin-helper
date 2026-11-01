import { createRouter, createWebHistory } from "vue-router";

import HomeView from "@/features/home/HomeView.vue";
import RecordView from "@/features/record/RecordView.vue";
import ToolView from "@/features/tool/ToolView.vue";
import ManualView from "@/features/manual/ManualView.vue";

const router = createRouter({
  // Tauri 支持 history 模式；浏览器开发期同样可用
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/record", name: "record", component: RecordView },
    { path: "/tool", name: "tool", component: ToolView },
    { path: "/manual", name: "manual", component: ManualView },
  ],
});

export default router;
