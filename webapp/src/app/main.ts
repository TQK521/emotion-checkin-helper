import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { storage } from "./providers/storage";
import { useCheckinStore } from "@/core/store/use-checkin";
import "@/shared/styles/global.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// 装配运行期存储（浏览器开发态 = localStorage "checkin-dev-db"；桌面态 = Tauri invoke）并载入数据
const checkin = useCheckinStore(pinia);
checkin.setStorage(storage);
void checkin.load();

app.mount("#app");
