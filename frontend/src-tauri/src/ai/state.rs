use tokio::sync::RwLock;
use serde::Serialize;
use crate::ai::timesfm::TimesFMEngine;
use tauri::Manager;

#[derive(Serialize, Clone)]
pub enum AiEngineStatus {
    NotInstalled,
    Loading,
    Ready,
    Failed(String),
}

pub struct AiStateManager {
    pub status: RwLock<AiEngineStatus>,
    pub engine: RwLock<Option<TimesFMEngine>>,
}

impl AiStateManager {
    pub fn new() -> Self {
        Self {
            status: RwLock::new(AiEngineStatus::NotInstalled),
            engine: RwLock::new(None),
        }
    }

    /// Attempts to load the ONNX model into memory.
    pub async fn warmup_engine(&self, app_handle: &tauri::AppHandle) -> Result<(), String> {
        let mut status = self.status.write().await;
        *status = AiEngineStatus::Loading;
        drop(status); // Release write lock immediately

        let mut model_path = app_handle.path().app_data_dir()
            .map_err(|_| "Failed to resolve app data dir".to_string())?;
        model_path.push("models");
        model_path.push(super::TIMESFM_MODEL_FILENAME);

        if !model_path.exists() {
            let mut status = self.status.write().await;
            *status = AiEngineStatus::NotInstalled;
            return Err("Model file not found. Please download the AI pack.".to_string());
        }

        // With load-dynamic, the ORT library path is specified via ORT_DYLIB_PATH env var.
        // We check if the DLL is bundled next to the exe (resource dir) and set the path.
        // If not bundled, ORT will search system PATH — a valid fallback for dev machines.
        let resource_dir = app_handle.path().resource_dir()
            .map_err(|_| "Failed to resolve resource dir".to_string())?;

        #[cfg(target_os = "windows")]       let lib_name = "onnxruntime.dll";
        #[cfg(target_os = "macos")]         let lib_name = "libonnxruntime.dylib";
        #[cfg(not(any(target_os = "windows", target_os = "macos")))] let lib_name = "libonnxruntime.so";

        let lib_path = resource_dir.join(lib_name);
        if lib_path.exists() {
            // Safety: This is safe on the single init path — called once per app lifecycle.
            unsafe { std::env::set_var("ORT_DYLIB_PATH", &lib_path); }
        }

        // In ort 2.0.0-rc, commit() returns bool (true = success), not a Result.
        ort::init().with_name("logi-hex").commit();

        match TimesFMEngine::new(&model_path) {
            Ok(loaded_engine) => {
                let mut engine = self.engine.write().await;
                *engine = Some(loaded_engine);
                let mut status = self.status.write().await;
                *status = AiEngineStatus::Ready;
                Ok(())
            }
            Err(e) => {
                let mut status = self.status.write().await;
                *status = AiEngineStatus::Failed(e.clone());
                Err(format!("Failed to load ONNX session: {}", e))
            }
        }
    }

    /// Fetches the loaded engine for inference, or lazy-loads it if not ready.
    pub async fn get_or_load_engine<'a>(&'a self, app_handle: &tauri::AppHandle) -> Result<tokio::sync::RwLockWriteGuard<'a, Option<TimesFMEngine>>, String> {
        {
            let engine = self.engine.write().await;
            if engine.is_some() {
                return Ok(engine);
            }
        }

        // Lazy Load
        self.warmup_engine(app_handle).await?;

        // After successful warmup, return the write guard
        let engine = self.engine.write().await;
        if engine.is_some() {
            Ok(engine)
        } else {
            Err("Engine warmup succeeded but pointer is null".to_string())
        }
    }
}
