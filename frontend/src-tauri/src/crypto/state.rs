use zeroize::{Zeroize, ZeroizeOnDrop};

/// Holds the master encryption key in memory for the lifetime of the application.
/// The key is zeroed from memory when this struct is dropped — it never lingers.
#[derive(ZeroizeOnDrop)]
pub struct CryptoState {
    pub master_key: Vec<u8>,
}

impl CryptoState {
    pub fn new(key: Vec<u8>) -> Self {
        Self { master_key: key }
    }

    pub fn key(&self) -> &[u8] {
        &self.master_key
    }
}
