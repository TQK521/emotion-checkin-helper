/**
 * manual.ts —— 手册「每日一课」数据类型（对齐 chapters_data.py / chapters.json）
 */

/** 长文 full 区块类型 */
export type FullBlockType = "h2" | "bullet" | "body";

/** 长文区块：[类型, 文本]（Python 元组转 JSON 数组） */
export type FullBlock = [type: FullBlockType, text: string];

/** 单章课程 */
export interface Chapter {
  name: string;
  group: string;
  tag: string;
  intro: string;
  essence: string;
  signs: string[];
  why: string;
  tip_title: string;
  tip: string;
  warm: string;
  full: FullBlock[];
}

/** chapters.json 文件结构 */
export interface ChaptersFile {
  chapters: Chapter[];
  group_order: string[];
  chapter_count: number;
  warm_intro: string;
}
