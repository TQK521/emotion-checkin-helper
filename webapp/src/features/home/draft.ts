/**
 * draft.ts —— home 域切页草稿（feature 私有模块态）
 *
 * App.vue 无 KeepAlive，路由切换即卸载 HomeView；
 * 未提交的表单输入（已选情绪/场景/强度/备注/自定义词）用模块级变量保留，
 * 组件重新挂载时恢复。提交成功或主动「清空选择」时清草稿。
 */

export interface HomeDraft {
  /** 已选情绪词 */
  emotions: string[];
  /** 场景（空串 = 未选） */
  scene: string;
  /** 强度 1-5 */
  intensity: number;
  /** 备注（用户真实输入，不含占位提示文案） */
  note: string;
  /** 自定义情绪输入框内容 */
  custom: string;
}

let draft: HomeDraft | null = null;

/** 读取当前草稿（无草稿返回 null） */
export function getHomeDraft(): HomeDraft | null {
  return draft ? { ...draft, emotions: [...draft.emotions] } : null;
}

/** 保存草稿（内部拷贝，防止外部引用篡改） */
export function saveHomeDraft(d: HomeDraft): void {
  draft = {
    emotions: [...d.emotions],
    scene: d.scene,
    intensity: d.intensity,
    note: d.note,
    custom: d.custom,
  };
}

/** 清草稿（提交成功 / 主动清空 / 测试重置共用） */
export function clearHomeDraft(): void {
  draft = null;
}
