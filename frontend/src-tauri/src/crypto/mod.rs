pub mod state;

use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Nonce,
};
use rand::RngCore;
use zeroize::Zeroizing;

const KEYRING_SERVICE: &str = "logi-hex";
const KEYRING_USER: &str = "master-key-v1";
const NONCE_LEN: usize = 12;

/// Loads the master key from the OS keyring.
/// If no key exists (first run), generates a 32-byte random key and stores it.
/// Returns a `Zeroizing` wrapper so the key is wiped from memory on drop.
pub fn load_or_create_master_key() -> Result<Zeroizing<Vec<u8>>, String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|e| format!("Keyring init error: {}", e))?;

    match entry.get_password() {
        Ok(hex_key) => {
            let bytes = hex::decode(&hex_key)
                .map_err(|e| format!("Keyring key corrupt (invalid hex): {}", e))?;
            if bytes.len() != 32 {
                return Err(format!("Keyring key has wrong length: {} (expected 32)", bytes.len()));
            }
            Ok(Zeroizing::new(bytes))
        }
        Err(keyring::Error::NoEntry) => {
            // First run: generate and store
            let mut key = Zeroizing::new(vec![0u8; 32]);
            OsRng.fill_bytes(&mut key);
            let hex_key = hex::encode(&*key);
            entry.set_password(&hex_key)
                .map_err(|e| format!("Failed to store key in keyring: {}", e))?;
            log::info!("Generated and stored new master encryption key in OS keyring.");
            Ok(key)
        }
        Err(e) => Err(format!("Keyring read error: {}", e)),
    }
}

/// Encrypts a plaintext field with AES-256-GCM.
/// Output format: base64(nonce || ciphertext) — self-contained for storage in SQLite TEXT columns.
pub fn encrypt_field(plaintext: &str, key: &[u8]) -> Result<String, String> {
    let cipher = Aes256Gcm::new_from_slice(key)
        .map_err(|e| format!("Cipher init error: {}", e))?;

    let mut nonce_bytes = [0u8; NONCE_LEN];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);

    let ciphertext = cipher.encrypt(nonce, plaintext.as_bytes())
        .map_err(|e| format!("Encryption failed: {}", e))?;

    // Concatenate nonce + ciphertext, then base64-encode the whole thing
    let mut payload = Vec::with_capacity(NONCE_LEN + ciphertext.len());
    payload.extend_from_slice(&nonce_bytes);
    payload.extend_from_slice(&ciphertext);

    Ok(base64::encode(&payload))
}

/// Decrypts a field previously encrypted by `encrypt_field`.
/// Returns `None` if the input is null/empty (not encrypted, stored as-is for backwards compat).
pub fn decrypt_field(encoded: &str, key: &[u8]) -> Result<String, String> {
    if encoded.is_empty() {
        return Ok(String::new());
    }

    let payload = base64::decode(encoded)
        .map_err(|e| format!("Base64 decode error: {}", e))?;

    if payload.len() < NONCE_LEN {
        return Err(format!("Payload too short to contain nonce: {} bytes", payload.len()));
    }

    let (nonce_bytes, ciphertext) = payload.split_at(NONCE_LEN);
    let nonce = Nonce::from_slice(nonce_bytes);

    let cipher = Aes256Gcm::new_from_slice(key)
        .map_err(|e| format!("Cipher init error: {}", e))?;

    let plaintext = cipher.decrypt(nonce, ciphertext)
        .map_err(|e| format!("Decryption failed (key mismatch or corrupt data): {}", e))?;

    String::from_utf8(plaintext)
        .map_err(|e| format!("Decrypted bytes are not valid UTF-8: {}", e))
}
