use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

struct ApiProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .manage(ApiProcess(Mutex::new(None)))
        .setup(|app| {
            let (_rx, child) = app
                .shell()
                .sidecar("api-server")
                .expect("api-server sidecar not configured")
                .spawn()
                .expect("failed to spawn api-server");
            *app.state::<ApiProcess>().0.lock().unwrap() = Some(child);
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let api = window.app_handle().state::<ApiProcess>();
                let mut guard = api.0.lock().unwrap();
                if let Some(child) = guard.take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}