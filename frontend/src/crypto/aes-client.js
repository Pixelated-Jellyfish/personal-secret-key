/**
 * Client-side AES-128 implementation (FIPS-197) with animation support.
 * Mirrors the backend Python implementation for consistency.
 * Row-major state representation: state[row][col]
 */

// Standard AES S-Box (Rijndael)
const S_BOX = [
  0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
  0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
  0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
  0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
  0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
  0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
  0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
  0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
  0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
  0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
  0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
  0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
  0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
  0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
  0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
  0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
]

// Inverse S-Box for decryption
const INV_S_BOX = new Array(256)
for (let i = 0; i < 256; i++) {
  INV_S_BOX[S_BOX[i]] = i
}

// Rcon (Round Constant) for key expansion
const RCON = [
  0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36
]

// MixColumns matrix (row-major)
const MIX_COL_MATRIX = [
  [0x02, 0x03, 0x01, 0x01],
  [0x01, 0x02, 0x03, 0x01],
  [0x01, 0x01, 0x02, 0x03],
  [0x03, 0x01, 0x01, 0x02],
]

const INV_MIX_COL_MATRIX = [
  [0x0e, 0x0b, 0x0d, 0x09],
  [0x09, 0x0e, 0x0b, 0x0d],
  [0x0d, 0x09, 0x0e, 0x0b],
  [0x0b, 0x0d, 0x09, 0x0e],
]

/**
 * Convert 16 bytes to 4x4 state matrix (row-major)
 * AES state: row 0 = bytes 0,4,8,12; row 1 = bytes 1,5,9,13; etc.
 */
export function bytesToState(data) {
  if (data.length !== 16) {
    throw new Error('Input must be 16 bytes')
  }
  const state = []
  for (let r = 0; r < 4; r++) {
    state[r] = []
    for (let c = 0; c < 4; c++) {
      state[r][c] = data[r + 4 * c]
    }
  }
  return state
}

/**
 * Convert 4x4 state matrix (row-major) to 16 bytes
 */
export function stateToBytes(state) {
  const bytes = new Uint8Array(16)
  let idx = 0
  for (let c = 0; c < 4; c++) {
    for (let r = 0; r < 4; r++) {
      bytes[idx++] = state[r][c]
    }
  }
  return bytes
}

/**
 * Convert state to hex string representation for display
 */
export function stateToHex(state) {
  return state.map(row => row.map(val => val.toString(16).padStart(2, '0')))
}

/**
 * SubBytes transformation
 */
export function subBytes(state, inverse = false) {
  const box = inverse ? INV_S_BOX : S_BOX
  return state.map(row => row.map(val => box[val]))
}

/**
 * ShiftRows transformation (row-major)
 */
export function shiftRows(state, inverse = false) {
  const result = Array.from({ length: 4 }, () => new Array(4))
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const newC = inverse ? (c + r) % 4 : (c - r + 4) % 4
      result[r][newC] = state[r][c]
    }
  }
  return result
}

/**
 * Galois Field multiplication GF(2^8)
 */
function galoisMul(a, b) {
  let result = 0
  while (b) {
    if (b & 1) result ^= a
    a <<= 1
    if (a & 0x100) a ^= 0x11b
    b >>= 1
  }
  return result & 0xff
}

/**
 * MixColumns transformation (row-major)
 */
export function mixColumns(state, inverse = false) {
  const matrix = inverse ? INV_MIX_COL_MATRIX : MIX_COL_MATRIX
  const result = Array.from({ length: 4 }, () => new Array(4))
  for (let c = 0; c < 4; c++) {
    for (let r = 0; r < 4; r++) {
      let val = 0
      for (let k = 0; k < 4; k++) {
        val ^= galoisMul(matrix[r][k], state[k][c])
      }
      result[r][c] = val
    }
  }
  return result
}

/**
 * AddRoundKey transformation (XOR state with round key)
 */
export function addRoundKey(state, roundKey) {
  return state.map((row, r) => row.map((val, c) => val ^ roundKey[r][c]))
}

/**
 * RotWord: rotate word 1 byte left
 */
function rotWord(word) {
  return [word[1], word[2], word[3], word[0]]
}

/**
 * SubWord: substitute each byte with S-Box
 */
function subWord(word) {
  return word.map(b => S_BOX[b])
}

/**
 * Key Expansion for AES-128
 * Input: 16 bytes key
 * Output: 11 round keys (each 4x4 row-major state)
 */
export function keyExpansion(key) {
  if (key.length !== 16) {
    throw new Error('Key must be 16 bytes (AES-128)')
  }

  const words = Array.from({ length: 44 }, () => new Array(4))

  // First 4 words from original key
  for (let i = 0; i < 4; i++) {
    words[i] = [key[4 * i], key[4 * i + 1], key[4 * i + 2], key[4 * i + 3]]
  }

  // Generate remaining words
  for (let i = 4; i < 44; i++) {
    let temp = [...words[i - 1]]
    if (i % 4 === 0) {
      temp = rotWord(temp)
      temp = subWord(temp)
      temp[0] ^= RCON[i / 4]
    }
    for (let j = 0; j < 4; j++) {
      words[i][j] = words[i - 4][j] ^ temp[j]
    }
  }

  // Convert to 11 round keys (4x4 row-major)
  const roundKeys = []
  for (let i = 0; i < 11; i++) {
    const rk = Array.from({ length: 4 }, () => new Array(4))
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        rk[r][c] = words[4 * i + c][r]
      }
    }
    roundKeys.push(rk)
  }

  return roundKeys
}

/**
 * Key Expansion with trace info for visualization
 */
export function keyExpansionWithTrace(key) {
  if (key.length !== 16) {
    throw new Error('Key must be 16 bytes (AES-128)')
  }

  const words = Array.from({ length: 44 }, () => new Array(4))
  const traceInfo = []

  for (let i = 0; i < 4; i++) {
    words[i] = [key[4 * i], key[4 * i + 1], key[4 * i + 2], key[4 * i + 3]]
  }

  for (let i = 4; i < 44; i++) {
    let temp = [...words[i - 1]]
    const info = { wordIndex: i, rotword: false, subword: false, rcon: null }

    if (i % 4 === 0) {
      temp = rotWord(temp)
      info.rotword = true
      temp = subWord(temp)
      info.subword = true
      const rconVal = RCON[i / 4]
      temp[0] ^= rconVal
      info.rcon = rconVal.toString(16).padStart(2, '0')
    }

    for (let j = 0; j < 4; j++) {
      words[i][j] = words[i - 4][j] ^ temp[j]
    }
    traceInfo.push(info)
  }

  const roundKeys = []
  for (let i = 0; i < 11; i++) {
    const rk = Array.from({ length: 4 }, () => new Array(4))
    for (let r = 0; r < 4; r++) {
      for (let c = 0; c < 4; c++) {
        rk[r][c] = words[4 * i + c][r]
      }
    }
    roundKeys.push(rk)
  }

  return { roundKeys, traceInfo }
}

/**
 * Encrypt single block (16 bytes) with AES-128
 * @param {Uint8Array} block - 16-byte plaintext block
 * @param {Array<Array<Array<number>>>} roundKeys - 11 round keys (each 4x4 row-major matrix)
 * @param {boolean} trace - Whether to return step-by-step trace
 * @returns {{ciphertext: Uint8Array, trace: Array<{round: number, step: string, state: Array<Array<string>>, description: string}>|null}}
 *   If trace=true: { ciphertext: Uint8Array, trace: TraceStep[] }
 *   If trace=false: { ciphertext: Uint8Array, trace: null }
 *   TraceStep: { round: 0-10, step: 'add_round_key_initial'|'sub_bytes'|'shift_rows'|'mix_columns'|'add_round_key',
 *                state: 4x4 hex string matrix, description: human-readable step description }
 */
export function encryptBlock(block, roundKeys, trace = false) {
  if (block.length !== 16) {
    throw new Error('Block must be 16 bytes')
  }

  let state = bytesToState(block)
  const traceData = []

  // Initial AddRoundKey (Round 0)
  state = addRoundKey(state, roundKeys[0])
  if (trace) {
    traceData.push({
      round: 0,
      step: 'add_round_key_initial',
      state: stateToHex(state),
      description: 'Initial AddRoundKey (Round 0)'
    })
  }

  // Rounds 1-9
  for (let roundNum = 1; roundNum <= 9; roundNum++) {
    state = subBytes(state)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'sub_bytes',
        state: stateToHex(state),
        description: `Round ${roundNum}: SubBytes`
      })
    }

    state = shiftRows(state)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'shift_rows',
        state: stateToHex(state),
        description: `Round ${roundNum}: ShiftRows`
      })
    }

    state = mixColumns(state)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'mix_columns',
        state: stateToHex(state),
        description: `Round ${roundNum}: MixColumns`
      })
    }

    state = addRoundKey(state, roundKeys[roundNum])
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'add_round_key',
        state: stateToHex(state),
        description: `Round ${roundNum}: AddRoundKey`
      })
    }
  }

  // Round 10 (no MixColumns)
  state = subBytes(state)
  if (trace) {
    traceData.push({
      round: 10,
      step: 'sub_bytes',
      state: stateToHex(state),
      description: 'Round 10: SubBytes'
    })
  }

  state = shiftRows(state)
  if (trace) {
    traceData.push({
      round: 10,
      step: 'shift_rows',
      state: stateToHex(state),
      description: 'Round 10: ShiftRows'
    })
  }

  state = addRoundKey(state, roundKeys[10])
  if (trace) {
    traceData.push({
      round: 10,
      step: 'add_round_key',
      state: stateToHex(state),
      description: 'Round 10: AddRoundKey (Final)'
    })
  }

  return {
    ciphertext: stateToBytes(state),
    trace: traceData
  }
}

/**
 * Decrypt single block (16 bytes) with AES-128
 * @param {Uint8Array} block - 16-byte ciphertext block
 * @param {Array<Array<Array<number>>>} roundKeys - 11 round keys (each 4x4 row-major matrix)
 * @param {boolean} trace - Whether to return step-by-step trace
 * @returns {{plaintext: Uint8Array, trace: Array<{round: number, step: string, state: Array<Array<string>>, description: string}>|null}}
 *   If trace=true: { plaintext: Uint8Array, trace: TraceStep[] }
 *   If trace=false: { plaintext: Uint8Array, trace: null }
 *   TraceStep: { round: 0-10, step: 'add_round_key_initial'|'inv_shift_rows'|'inv_sub_bytes'|'add_round_key'|'inv_mix_columns',
 *                state: 4x4 hex string matrix, description: human-readable step description }
 */
export function decryptBlock(block, roundKeys, trace = false) {
  if (block.length !== 16) {
    throw new Error('Block must be 16 bytes')
  }

  let state = bytesToState(block)
  const traceData = []

  // Initial AddRoundKey (Round 10)
  state = addRoundKey(state, roundKeys[10])
  if (trace) {
    traceData.push({
      round: 10,
      step: 'add_round_key_initial',
      state: stateToHex(state),
      description: 'Initial AddRoundKey (Round 10)'
    })
  }

  // Rounds 9-1 (inverse order)
  for (let roundNum = 9; roundNum >= 1; roundNum--) {
    state = shiftRows(state, true)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'inv_shift_rows',
        state: stateToHex(state),
        description: `Round ${roundNum}: InvShiftRows`
      })
    }

    state = subBytes(state, true)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'inv_sub_bytes',
        state: stateToHex(state),
        description: `Round ${roundNum}: InvSubBytes`
      })
    }

    state = addRoundKey(state, roundKeys[roundNum])
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'add_round_key',
        state: stateToHex(state),
        description: `Round ${roundNum}: AddRoundKey`
      })
    }

    state = mixColumns(state, true)
    if (trace) {
      traceData.push({
        round: roundNum,
        step: 'inv_mix_columns',
        state: stateToHex(state),
        description: `Round ${roundNum}: InvMixColumns`
      })
    }
  }

  // Round 0
  state = shiftRows(state, true)
  if (trace) {
    traceData.push({
      round: 0,
      step: 'inv_shift_rows',
      state: stateToHex(state),
      description: 'Round 0: InvShiftRows'
    })
  }

  state = subBytes(state, true)
  if (trace) {
    traceData.push({
      round: 0,
      step: 'inv_sub_bytes',
      state: stateToHex(state),
      description: 'Round 0: InvSubBytes'
    })
  }

  state = addRoundKey(state, roundKeys[0])
  if (trace) {
    traceData.push({
      round: 0,
      step: 'add_round_key',
      state: stateToHex(state),
      description: 'Round 0: AddRoundKey (Final)'
    })
  }

  return {
    plaintext: stateToBytes(state),
    trace: traceData
  }
}

/**
 * PKCS#7 padding
 */
export function pkcs7Pad(data, blockSize = 16) {
  const padLen = blockSize - (data.length % blockSize)
  const padding = new Uint8Array(padLen).fill(padLen)
  const result = new Uint8Array(data.length + padLen)
  result.set(data)
  result.set(padding, data.length)
  return result
}

/**
 * Remove PKCS#7 padding
 */
export function pkcs7Unpad(data) {
  if (data.length === 0) throw new Error('Empty data')
  const padLen = data[data.length - 1]
  if (padLen > 16 || padLen === 0) throw new Error('Invalid padding')
  for (let i = data.length - padLen; i < data.length; i++) {
    if (data[i] !== padLen) throw new Error('Invalid padding')
  }
  return data.slice(0, data.length - padLen)
}

/**
 * Encrypt with AES-128-CBC
 * Returns: { ciphertext: Uint8Array, iv: Uint8Array }
 */
export function encryptCBC(plaintext, key) {
  if (key.length !== 16) throw new Error('Key must be 16 bytes')

  const iv = crypto.getRandomValues(new Uint8Array(16))
  const roundKeys = keyExpansion(key)

  const padded = pkcs7Pad(plaintext)
  const blocks = []
  for (let i = 0; i < padded.length; i += 16) {
    blocks.push(padded.slice(i, i + 16))
  }

  const ciphertext = new Uint8Array(padded.length)
  let prevBlock = iv

  for (let i = 0; i < blocks.length; i++) {
    // XOR with IV or previous ciphertext block
    const xorBlock = new Uint8Array(16)
    for (let j = 0; j < 16; j++) {
      xorBlock[j] = blocks[i][j] ^ prevBlock[j]
    }
    const { ciphertext: encBlock } = encryptBlock(xorBlock, roundKeys)
    ciphertext.set(encBlock, i * 16)
    prevBlock = encBlock
  }

  return { ciphertext, iv }
}

/**
 * Decrypt with AES-128-CBC
 */
export function decryptCBC(ciphertext, key, iv) {
  if (key.length !== 16) throw new Error('Key must be 16 bytes')
  if (iv.length !== 16) throw new Error('IV must be 16 bytes')
  if (ciphertext.length % 16 !== 0) throw new Error('Ciphertext must be multiple of 16 bytes')

  const roundKeys = keyExpansion(key)
  const blocks = []
  for (let i = 0; i < ciphertext.length; i += 16) {
    blocks.push(ciphertext.slice(i, i + 16))
  }

  const plaintext = new Uint8Array(ciphertext.length)
  let prevBlock = iv

  for (let i = 0; i < blocks.length; i++) {
    const { plaintext: decBlock } = decryptBlock(blocks[i], roundKeys)
    // XOR with IV or previous ciphertext block
    for (let j = 0; j < 16; j++) {
      plaintext[i * 16 + j] = decBlock[j] ^ prevBlock[j]
    }
    prevBlock = blocks[i]
  }

  return pkcs7Unpad(plaintext)
}

/**
 * Encrypt string and return base64 encoded ciphertext + IV
 */
export function encryptCBCBase64(plaintext, key) {
  const encoder = new TextEncoder()
  const { ciphertext, iv } = encryptCBC(encoder.encode(plaintext), key)
  return {
    ciphertext: btoa(String.fromCharCode(...ciphertext)),
    iv: btoa(String.fromCharCode(...iv))
  }
}

/**
 * Decrypt base64 encoded ciphertext + IV
 */
export function decryptCBCBase64(ciphertextB64, key, ivB64) {
  const ct = Uint8Array.from(atob(ciphertextB64), c => c.charCodeAt(0))
  const iv = Uint8Array.from(atob(ivB64), c => c.charCodeAt(0))
  const pt = decryptCBC(ct, key, iv)
  return new TextDecoder().decode(pt)
}

/**
 * Derive AES key from passphrase using PBKDF2 (Web Crypto API)
 */
export async function deriveKeyPBKDF2(passphrase, salt = null) {
  const DEFAULT_SALT = new TextEncoder().encode('secretnotes-salt-123456789012') // 32 bytes
  const ITERATIONS = 100000
  const KEY_LENGTH = 16 // AES-128

  const saltBytes = salt || DEFAULT_SALT
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(passphrase),
    'PBKDF2',
    false,
    ['deriveBits']
  )

  const keyBits = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: saltBytes,
      iterations: ITERATIONS,
      hash: 'SHA-256'
    },
    keyMaterial,
    KEY_LENGTH * 8
  )

  return new Uint8Array(keyBits)
}

/**
 * Format bytes as hex string
 */
export function bytesToHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Parse hex string to Uint8Array
 */
export function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2)
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.slice(i, i + 2), 16)
  }
  return bytes
}