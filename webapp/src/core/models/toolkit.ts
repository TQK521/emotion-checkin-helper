/**
 * toolkit.ts —— 工具箱数据类型（对齐 toolkit_data.py / toolkit.json）
 */

/** 呼吸引导动作；null 表示普通步骤卡 */
export type BreathAction = "breath_sigh" | "breath_478" | "breath_box" | null;

/** 科学循证方法 */
export interface ToolMethod {
  key: string;
  name: string;
  group: string;
  time: string;
  why: string;
  steps: string[];
  evidence: string;
  action: BreathAction;
}

/** toolkit.json 文件结构（元组均转为数组） */
export interface ToolkitFile {
  /** 状态分流：[key, label] */
  states: [string, string][];
  /** 状态 → 推荐方法 key */
  state_recs: Record<string, string[]>;
  /** 方法分组：[key, name, desc] */
  groups: [string, string, string][];
  methods: ToolMethod[];
}
