// lib.rs —— Tauri 后端：打卡数据存储命令（波3）
// 对应 v2 方案 4.2 + 第七节：数据路径 appDataDir / 原子写 / 自动备份 / 损坏隔离 / 导入向导。
// 数据契约与旧版 data_store.py 对齐：checkin_data.json 顶层 5 字段、备份/损坏命名规则一致。

use chrono::Local;
use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};
use tauri_plugin_dialog::DialogExt;

/// 数据文件名（对齐旧版，升级不丢历史）
const DATA_FILE: &str = "checkin_data.json";
/// 自动备份前缀（对齐旧版 BACKUP_PREFIX "checkin_data_备份_"）
const BACKUP_PREFIX: &str = "checkin_data_备份_";
/// 损坏隔离前缀（对齐旧版 quarantine "checkin_data_损坏_"）
const CORRUPT_PREFIX: &str = "checkin_data_损坏_";
/// 备份保留份数（对齐旧版 auto_backup max_keep=7）
const MAX_BACKUPS: usize = 7;

/// 数据目录 = Tauri appDataDir（%APPDATA%/<identifier>），独立于安装目录，升级不丢
fn data_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("定位数据目录失败: {e}"))?;
    fs::create_dir_all(&dir).map_err(|e| format!("创建数据目录失败: {e}"))?;
    Ok(dir)
}

fn data_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(data_dir(app)?.join(DATA_FILE))
}

/// 空数据（对齐前端 createEmptyData 契约结构）
fn empty_data() -> Value {
    json!({
        "start_date": null,
        "records": [],
        "best_streak": 0,
        "journal": [],
        "custom_emotions": [],
    })
}

/// 读取完整数据；文件缺失返回空数据；损坏则保留现场改名后返回空数据（禁止静默覆盖）
#[tauri::command]
fn load_data(app: AppHandle) -> Result<Value, String> {
    let path = data_path(&app)?;
    if !path.exists() {
        return Ok(empty_data());
    }
    let content = fs::read_to_string(&path).map_err(|e| format!("读取数据失败: {e}"))?;
    match serde_json::from_str::<Value>(&content) {
        Ok(v) if v.is_object() => Ok(v),
        _ => {
            // 损坏隔离：改名保留现场，后续加载空数据
            let ts = Local::now().format("%Y-%m-%d_%H-%M-%S").to_string();
            let saved = path.with_file_name(format!("{}{}.json", CORRUPT_PREFIX, ts));
            let _ = fs::rename(&path, &saved);
            Ok(empty_data())
        }
    }
}

/// 全量写回（原子写：先写临时文件再替换，崩溃不损坏原数据；对齐 save_data）
#[tauri::command]
fn save_data(app: AppHandle, data: Value) -> Result<(), String> {
    let path = data_path(&app)?;
    let tmp = path.with_file_name(format!("{}.tmp", DATA_FILE));
    let content = serde_json::to_string_pretty(&data).map_err(|e| format!("序列化失败: {e}"))?;
    fs::write(&tmp, content).map_err(|e| format!("写临时文件失败: {e}"))?;
    fs::rename(&tmp, &path).map_err(|e| format!("替换数据文件失败: {e}"))?;
    Ok(())
}

/// 备份当前数据：按日期命名（同天覆盖）、仅备份合法数据、保留最近 7 份（对齐 auto_backup）
#[tauri::command]
fn backup_data(app: AppHandle) -> Result<String, String> {
    let path = data_path(&app)?;
    if !path.exists() {
        return Err("还没有数据文件，无可备份".to_string());
    }
    let content = fs::read_to_string(&path).map_err(|e| format!("读取失败: {e}"))?;
    serde_json::from_str::<Value>(&content)
        .map_err(|_| "数据损坏，未备份".to_string())?;

    let dir = path.parent().unwrap().to_path_buf();
    let today = Local::now().format("%Y-%m-%d").to_string();
    let backup = dir.join(format!("{}{}.json", BACKUP_PREFIX, today));
    fs::copy(&path, &backup).map_err(|e| format!("备份失败: {e}"))?;

    // 保留最近 MAX_BACKUPS 份（按文件名排序清最旧）
    let mut list: Vec<PathBuf> = fs::read_dir(&dir)
        .map_err(|e| format!("读取备份目录失败: {e}"))?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .and_then(|n| n.to_str())
                .map(|n| n.starts_with(BACKUP_PREFIX) && n.ends_with(".json"))
                .unwrap_or(false)
        })
        .collect();
    list.sort();
    if list.len() > MAX_BACKUPS {
        for old in list.iter().take(list.len() - MAX_BACKUPS) {
            let _ = fs::remove_file(old);
        }
    }
    Ok(backup.to_string_lossy().to_string())
}

/// 导入向导：弹文件选择框读旧 checkin_data.json 原始内容（用户取消返回 None）
#[tauri::command]
fn pick_import_file(app: AppHandle) -> Result<Option<String>, String> {
    let picked = app
        .dialog()
        .file()
        .add_filter("打卡数据", &["json"])
        .blocking_pick_file();
    match picked {
        Some(fp) => {
            let path = fp
                .into_path()
                .map_err(|_| "所选不是本地文件".to_string())?;
            let content =
                fs::read_to_string(&path).map_err(|e| format!("读取所选文件失败: {e}"))?;
            Ok(Some(content))
        }
        None => Ok(None),
    }
}

/// 启动自动备份（数据正常时复制当日备份；失败静默，不阻塞启动）
fn auto_backup(app: &AppHandle) {
    let _ = backup_data(app.clone());
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            auto_backup(app.handle());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            load_data,
            save_data,
            backup_data,
            pick_import_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
