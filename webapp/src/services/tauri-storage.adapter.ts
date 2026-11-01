/**
 * tauri-storage.adapter.ts —— 生产/桌面适配器（Tauri invoke 调 Rust 命令）
 * 命令在 src-tauri 侧实现（波3）；波1~2 开发期不触发本适配器。
 */
import { invoke } from "@tauri-apps/api/core";
import type { StoragePort } from "@/services/storage.port";
import type { CheckinData } from "@/core/domain";

const COMMANDS = {
  load: "load_data",
  save: "save_data",
  backup: "backup_data",
} as const;

export class TauriStorageAdapter implements StoragePort {
  async load(): Promise<CheckinData> {
    return invoke<CheckinData>(COMMANDS.load);
  }

  async save(data: CheckinData): Promise<void> {
    await invoke(COMMANDS.save, { data });
  }

  async backup(): Promise<string> {
    return invoke<string>(COMMANDS.backup);
  }
}
