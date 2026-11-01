/**
 * storage.ts —— 装配（环境检测，唯一决定具体适配器的位置）
 * 对应 v2 方案 4.5：桌面成品走 Tauri invoke，浏览器开发走 localStorage；
 * 测试单独注入 InMemory，不经过本模块。
 */
import { isTauri } from "@tauri-apps/api/core";
import type { StoragePort } from "@/services/storage.port";
import { TauriStorageAdapter } from "@/services/tauri-storage.adapter";
import { BrowserDevStorageAdapter } from "@/services/browser-storage.adapter";

/** 应用运行期唯一存储实现（导入即绑定，模块级单例） */
export const storage: StoragePort = isTauri()
  ? new TauriStorageAdapter()
  : new BrowserDevStorageAdapter();
