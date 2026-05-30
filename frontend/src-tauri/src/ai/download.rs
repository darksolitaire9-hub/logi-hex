use std::path::PathBuf;
use std::fs::{File, OpenOptions};
use std::io::{Write, Read};
use sha2::{Sha256, Digest};
use futures_util::StreamExt;
use reqwest::header::RANGE;
use tauri::Manager;

/// A robust, resumable downloader with SHA-256 verification.
pub async fn download_ai_pack(
    app_handle: tauri::AppHandle, 
    url: &str, 
    expected_sha256: &str, 
    filename: &str
) -> Result<PathBuf, String> {
    
    // 1. Resolve Application Data Directory (e.g. AppData/Roaming/com.logihex.app/models/)
    let mut model_dir = app_handle.path().app_data_dir().map_err(|_| "Failed to resolve app data dir")?;
    model_dir.push("models");
    std::fs::create_dir_all(&model_dir).map_err(|e| format!("Failed to create models directory: {}", e))?;

    let file_path = model_dir.join(filename);
    
    let client = reqwest::Client::new();
    
    // 2. Check if file already exists and matches checksum
    if file_path.exists() {
        if verify_checksum(&file_path, expected_sha256).unwrap_or(false) {
            return Ok(file_path);
        }
    }

    // 3. Determine Resumable Start Position
    let mut start_byte = 0;
    if let Ok(metadata) = std::fs::metadata(&file_path) {
        start_byte = metadata.len();
    }

    // 4. Request the File (with Range header if resuming)
    let mut request = client.get(url);
    if start_byte > 0 {
        request = request.header(RANGE, format!("bytes={}-", start_byte));
    }

    let response = request.send().await.map_err(|e| format!("Network error: {}", e))?;
    
    if !response.status().is_success() {
        // If range failed or file changed on server, restart from 0
        if response.status() == reqwest::StatusCode::RANGE_NOT_SATISFIABLE {
            let _ = start_byte; // Reset implicit — we remove the file and return anyway
            // Let's not loop here for simplicity; just clear file and error out for retry
            let _ = std::fs::remove_file(&file_path);
            return Err("Download interrupted, please try again".to_string());
        }
        return Err(format!("HTTP Error: {}", response.status()));
    }

    let mut file = OpenOptions::new()
        .create(true)
        .write(true)
        .append(true)
        .open(&file_path)
        .map_err(|e| format!("File access error: {}", e))?;

    if start_byte == 0 {
        file.set_len(0).unwrap(); // truncate if starting fresh
    }

    // 5. Stream the chunks to disk
    let mut stream = response.bytes_stream();
    while let Some(chunk_result) = stream.next().await {
        let chunk = chunk_result.map_err(|e| format!("Chunk error: {}", e))?;
        file.write_all(&chunk).map_err(|e| format!("Write error: {}", e))?;
    }
    
    file.sync_all().map_err(|e| format!("Sync error: {}", e))?;

    // 6. Verify Checksum
    if !verify_checksum(&file_path, expected_sha256).unwrap_or(false) {
        let _ = std::fs::remove_file(&file_path);
        return Err("Checksum mismatch! The file is corrupted. Deleted.".to_string());
    }

    Ok(file_path)
}

/// Verifies the SHA-256 hash of a file on disk
fn verify_checksum(path: &PathBuf, expected_hex: &str) -> Result<bool, std::io::Error> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0; 8192];

    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }

    let result = hasher.finalize();
    let result_hex = format!("{:x}", result);
    
    Ok(result_hex == expected_hex)
}
