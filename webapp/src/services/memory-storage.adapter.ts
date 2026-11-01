/**
 * memory-storage.adapter.ts —— 内存适配器（测试/隔离用）
 * 克隆用 JSON 序列化：数据契约是纯 JSON，且能安全克隆 pinia 的 reactive Proxy state。
 */
import type { StoragePort } from "@/services/storage.port";
import type { CheckinData } from "@/core/domain";

function clone(data: CheckinData): CheckinData {
  return JSON.parse(JSON.stringify(data)) as CheckinData;
}

export class InMemoryStorageAdapter implements StoragePort {
  private data: CheckinData;

  constructor(initial?: CheckinData) {
    this.data = initial ? clone(initial) : emptyData();
  }

  async load(): Promise<CheckinData> {
    return clone(this.data);
  }

  async save(data: CheckinData): Promise<void> {
    this.data = clone(data);
  }

  async backup(): Promise<string> {
    return "in-memory";
  }
}

function emptyData(): CheckinData {
  return { start_date: null, records: [], best_streak: 0, journal: [], custom_emotions: [] };
}
