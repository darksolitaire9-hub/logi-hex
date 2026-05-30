// crypto.ts
// Native WebCrypto Engine for Application-Level AES-GCM Encryption
// ZERO Dependencies. Relies on OS-level C++ hardware acceleration via the browser.

const ITERATIONS = 100000
const SALT_SIZE = 16
const IV_SIZE = 12

/**
 * Derives a 256-bit AES-GCM CryptoKey from a user PIN and Workspace ID.
 * We use the Workspace ID as the base salt to ensure the same PIN yields different keys across workspaces.
 */
export async function deriveKeyFromPin(pin: string, workspaceId: string): Promise<CryptoKey> {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    enc.encode(pin),
    { name: 'PBKDF2' },
    false,
    ['deriveBits', 'deriveKey']
  )

  // Use the workspaceId to create a deterministic salt for this specific workspace
  // We hash it to ensure it's exactly the right length and entropy
  const saltHash = await crypto.subtle.digest('SHA-256', enc.encode(workspaceId))

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: saltHash,
      iterations: ITERATIONS,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )
}

/**
 * Encrypts a plaintext string into a base64 encoded ciphertext string containing the IV and Auth Tag.
 * Format: base64(iv + ciphertext)
 */
export async function encryptField(plaintext: string | null | undefined, key: CryptoKey | null): Promise<string | null> {
  if (!plaintext || !key) return plaintext || null // Return null or original if empty/no key

  const enc = new TextEncoder()
  const iv = crypto.getRandomValues(new Uint8Array(IV_SIZE))
  const data = enc.encode(plaintext)

  const encryptedBuffer = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    data
  )

  // Combine IV and Ciphertext for storage
  const encryptedBytes = new Uint8Array(encryptedBuffer)
  const combined = new Uint8Array(iv.length + encryptedBytes.length)
  combined.set(iv, 0)
  combined.set(encryptedBytes, iv.length)

  // Convert to Base64 for SQLite text storage
  return btoa(String.fromCharCode(...combined))
}

/**
 * Decrypts a base64 encoded ciphertext string back to plaintext.
 */
export async function decryptField(base64Ciphertext: string | null | undefined, key: CryptoKey | null): Promise<string> {
  if (!base64Ciphertext || !key) return base64Ciphertext || ''

  try {
    // Basic heuristics for base64: length is multiple of 4, only valid chars
    const isBase64 = /^[a-zA-Z0-9+/]*={0,2}$/.test(base64Ciphertext) && (base64Ciphertext.length % 4 === 0)
    
    if (!isBase64) {
      // If it's not even valid base64, it's definitely legacy plaintext
      return base64Ciphertext
    }

    // Convert Base64 back to Uint8Array
    const binaryStr = atob(base64Ciphertext)
    const combined = new Uint8Array(binaryStr.length)
    for (let i = 0; i < binaryStr.length; i++) {
      combined[i] = binaryStr.charCodeAt(i)
    }

    // Extract IV and Ciphertext
    const iv = combined.slice(0, IV_SIZE)
    const data = combined.slice(IV_SIZE)

    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    )

    const dec = new TextDecoder()
    return dec.decode(decryptedBuffer)
  } catch (e) {
    // If decryption fails (e.g., bad key, corrupted MAC, or just edge-case plaintext that happens to look like base64),
    // we return the original string as a fallback to prevent data loss. 
    // In a strict zero-trust environment we would throw, but for graceful degradation we return the raw string.
    console.warn('Decryption failed, falling back to raw payload. If this is legacy data, it is expected.', e)
    return base64Ciphertext
  }
}
