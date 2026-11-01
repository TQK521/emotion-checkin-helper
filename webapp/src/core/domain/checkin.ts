/**
 * checkin.ts —— 打卡数据契约（权威类型，冻结）
 * 对齐 Python data_store.py；旧数据缺字段用可选 + 读取侧兜底，不迁移不覆盖。
 */

/** 单条打卡记录（契约 7 字段；scene/intensity 为后加，旧数据缺省） */
export interface CheckinRecord {
  /** 完整时间戳 "YYYY-MM-DD HH:mm:ss"（字符串，非数字） */
  ts: string;
  /** 日期 "YYYY-MM-DD" */
  date: string;
  /** 时间 "HH:mm" */
  time: string;
  /** 选中的情绪词 */
  emotions: string[];
  /** 一句话行动记录 */
  action: string;
  /** 场景（旧数据缺失，读取兜底 ""） */
  scene?: string;
  /** 情绪强度 1-5（旧数据缺失，读取兜底 3） */
  intensity?: number;
}

/** 用户自定义情绪词（v1.4.3 词库生长契约） */
export interface CustomEmotion {
  word: string;
  gloss?: string;
}

/** 树洞日志条目（新结构；旧结构为 text 单字段） */
export interface JournalEntry {
  date?: string;
  time?: string;
  event?: string;
  feeling?: string;
  action?: string;
  /** 旧格式：三句用 "\n" 连接 */
  text?: string;
}

/** 顶层数据（5 字段；部分字段旧数据缺省，故可选） */
export interface CheckinData {
  /** 开始打卡日期，首次为 null */
  start_date: string | null;
  records: CheckinRecord[];
  best_streak: number;
  journal?: JournalEntry[];
  custom_emotions?: CustomEmotion[];
}

/** 空数据工厂（对齐 load_data 默认结构） */
export function createEmptyData(): CheckinData {
  return {
    start_date: null,
    records: [],
    best_streak: 0,
    journal: [],
    custom_emotions: [],
  };
}
