/**
 * use-checkin.ts —— 核心 CheckinStore（Pinia 单一数据源）
 * 持有唯一 CheckinData；所有功能域经它读写，不重复持有记录。
 * 对齐 pages_home._record_emotion / _undo_last_record 的写入与撤销口径。
 */
import { defineStore } from "pinia";
import type { StoragePort } from "@/services/storage.port";
import type { CheckinData, CheckinRecord, CustomEmotion } from "@/core/domain";
import { createEmptyData } from "@/core/domain";
import { nowTs, nowTime, todayStr } from "@/shared/lib/date";
import { calcStreak } from "@/core/stats/statistics";
import { migrateOldData } from "@/services/importer/importer";

/** 记录表单输入（对应 make_record 的参数） */
export interface RecordInput {
  emotions: string[];
  action: string;
  scene?: string;
  intensity?: number;
}

interface UseCheckinState {
  /** 唯一数据源 */
  data: CheckinData;
  /** 是否已从存储载入 */
  loaded: boolean;
  /** 刚记录的最后一条（供撤销上一条） */
  lastRecord: CheckinRecord | null;
  /** 存储实现（测试注入 InMemory；运行期由 providers 装配） */
  storage: StoragePort | null;
  /** 载入失败原因（供 UI 提示） */
  loadError: string | null;
}

export const useCheckinStore = defineStore("checkin", {
  state: (): UseCheckinState => ({
    data: createEmptyData(),
    loaded: false,
    lastRecord: null,
    storage: null,
    loadError: null,
  }),

  getters: {
    /** 今日记录数（对齐 records_today） */
    todayCount: (state): number =>
      state.data.records.filter((r) => r.date === todayStr()).length,
    /** 累计记录数 */
    totalCount: (state): number => state.data.records.length,
  },

  actions: {
    /** 注入存储实现（App 启动时由 providers 装配；测试注入 InMemory） */
    setStorage(storage: StoragePort): void {
      this.storage = storage;
    },

    /** 从存储载入并迁移旧数据 */
    async load(): Promise<void> {
      if (!this.storage) return;
      try {
        const raw = await this.storage.load();
        this.data = migrateOldData(raw);
        this.loadError = null;
      } catch (e) {
        this.loadError = e instanceof Error ? e.message : String(e);
        this.data = createEmptyData();
      }
      this.loaded = true;
    },

    /** 全量写回存储 */
    async save(): Promise<void> {
      if (this.storage) await this.storage.save(this.data);
    },

    /**
     * 记录一次情绪（append 尾部；首次设置 start_date；实时更新 best_streak）。
     * 对齐 _record_emotion：构造 → append → 设 start_date → calc_streak → 更新 best → save。
     */
    async addRecord(input: RecordInput): Promise<CheckinRecord> {
      const rec: CheckinRecord = {
        ts: nowTs(),
        date: todayStr(),
        time: nowTime(),
        emotions: [...input.emotions],
        action: input.action,
        scene: input.scene ?? "",
        intensity: input.intensity ?? 3,
      };
      this.data.records.push(rec);
      this.lastRecord = rec;
      if (!this.data.start_date) this.data.start_date = rec.date;
      const s = calcStreak(this.data);
      if (s > this.data.best_streak) this.data.best_streak = s;
      await this.save();
      return rec;
    },

    /** 撤销上一条（pop 尾部），仅当最后一条仍是刚记的 */
    async undoLast(): Promise<CheckinRecord | null> {
      const recs = this.data.records;
      if (!this.lastRecord || recs.length === 0 || recs[recs.length - 1] !== this.lastRecord) {
        return null;
      }
      const removed = recs.pop()!;
      this.lastRecord = null;
      await this.save();
      return removed;
    },

    /** 按索引删除一条（记录页历史列表用） */
    async removeRecord(index: number): Promise<void> {
      if (index < 0 || index >= this.data.records.length) return;
      this.data.records.splice(index, 1);
      if (this.lastRecord === this.data.records[index]) this.lastRecord = null;
      await this.save();
    },

    /** 新增自定义情绪词（v1.4.3 词库生长契约，去重） */
    async addCustomEmotion(word: string, gloss = ""): Promise<boolean> {
      const w = word.trim();
      if (!w) return false;
      const existing = this.data.custom_emotions ?? [];
      if (existing.some((e) => e.word === w)) return false;
      this.data.custom_emotions = [...existing, { word: w, gloss }];
      await this.save();
      return true;
    },

    /** 删除自定义情绪词 */
    async removeCustomEmotion(word: string): Promise<void> {
      this.data.custom_emotions = (this.data.custom_emotions ?? []).filter(
        (e: CustomEmotion) => e.word !== word,
      );
      await this.save();
    },

    /** 备份当前数据 */
    async backup(): Promise<string> {
      if (!this.storage) return "";
      return this.storage.backup();
    },
  },
});
