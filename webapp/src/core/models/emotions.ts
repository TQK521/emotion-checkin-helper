/**
 * emotions.ts —— 情绪词与词库类型（对齐 emotions.json）
 */
export interface EmotionsFile {
  /** 内置情绪词（56） */
  emotions: string[];
  /** 情绪词 → 通俗解释（56 条） */
  glossary: Record<string, string>;
}
