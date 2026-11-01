/**
 * browser-storage.adapter.ts —— 浏览器开发适配器（波0~2 无 Rust 时开发用）
 * localStorage key "checkin-dev-db"；load 失败（缺失/解析失败）返回空数据。
 */
import type { StoragePort } from "@/services/storage.port";
import type { CheckinData } from "@/core/domain";
import { createEmptyData } from "@/core/domain";

export const BROWSER_DEV_KEY = "checkin-dev-db";

export class BrowserDevStorageAdapter implements StoragePort {
  async load(): Promise<CheckinData> {
    try {
      const raw = localStorage.getItem(BROWSER_DEV_KEY);
      if (!raw) return createEmptyData();
      const parsed = JSON.parse(raw) as CheckinData;
      return normalize(parsed);
    } catch {
      // 数据损坏：保留现场避免覆盖，返回空数据（波3 桌面版有 Rust 侧隔离）
      return createEmptyData();
    }
  }

  async save(data: CheckinData): Promise<void> {
    localStorage.setItem(BROWSER_DEV_KEY, JSON.stringify(data));
  }

  async backup(): Promise<string> {
    return "browser-dev";
  }
}

/** 读取侧兜底：缺字段补齐为契约默认（对齐 Python 读取侧 get() 兜底） */
function normalize(raw: CheckinData): CheckinData {
  return {
    start_date: typeof raw.start_date === "string" ? raw.start_date : null,
    records: Array.isArray(raw.records) ? raw.records : [],
    best_streak: typeof raw.best_streak === "number" ? raw.best_streak : 0,
    journal: Array.isArray(raw.journal) ? raw.journal : [],
    custom_emotions: Array.isArray(raw.custom_emotions) ? raw.custom_emotions : [],
  };
}
