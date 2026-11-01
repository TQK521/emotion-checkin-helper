/**
 * storage.port.ts —— 存储端口（业务只依赖此接口，不依赖具体实现）
 * 对应 v2 方案 4.1；适配器分别实现桌面/浏览器/内存三态。
 */
import type { CheckinData } from "@/core/domain";

export interface StoragePort {
  /** 读取完整数据；文件缺失/损坏由适配器兜底返回空数据 */
  load(): Promise<CheckinData>;
  /** 全量写回 */
  save(data: CheckinData): Promise<void>;
  /** 备份当前数据，返回备份标识（路径或描述串） */
  backup(): Promise<string>;
}
