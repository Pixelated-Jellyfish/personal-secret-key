/**
 * @typedef {Object} NoteListItem
 * @property {string} id - Note UUID
 * @property {string} title - Decrypted title
 * @property {string} updated_at - ISO8601 timestamp
 */

/**
 * @typedef {Object} NoteResponse
 * @property {string} id
 * @property {string} title - Decrypted title
 * @property {string} body - Decrypted body
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} NoteRaw
 * @property {string} id
 * @property {string} title_ciphertext - Base64 encrypted title
 * @property {string} title_iv - Base64 IV for title
 * @property {string} body_ciphertext - Base64 encrypted body
 * @property {string} body_iv - Base64 IV for body
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} TraceStep
 * @property {number} round - Round number (0-10)
 * @property {string} step - Step name (e.g., 'sub_bytes', 'shift_rows', 'mix_columns', 'add_round_key')
 * @property {string[][]} state - 4x4 hex string matrix
 * @property {string} description - Human-readable description
 */

/**
 * @typedef {Object} AesLogResponse
 * @property {string[][]} input_matrix - 4x4 hex matrix of input block
 * @property {TraceStep[]} trace - Array of trace steps
 */

/**
 * @typedef {Object} RoundKeysResponse
 * @property {string[][][]} round_keys - 11 x 4x4 hex matrices
 * @property {Object[]} key_expansion_trace - Key expansion trace info
 */

/**
 * @typedef {Object} CreateNotePayload
 * @property {string} title - Base64 encrypted title
 * @property {string} title_iv - Base64 IV for title
 * @property {string} body - Base64 encrypted body
 * @property {string} body_iv - Base64 IV for body
 * @property {boolean} client_encrypted - Must be true when sending pre-encrypted data
 */

const API_BASE = '/api'

function getAuthHeaders(aesKey) {
  return {
    'Content-Type': 'application/json',
    'X-AES-Key': aesKey
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function deriveKey(passphrase) {
  const response = await fetch(`${API_BASE}/crypto/derive`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passphrase })
  })
  const data = await handleResponse(response)
  return data.key
}

export const notesApi = {
  async list(aesKey) {
    const response = await fetch(`${API_BASE}/notes`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  },

  async create(aesKey, note) {
    const response = await fetch(`${API_BASE}/notes`, {
      method: 'POST',
      headers: getAuthHeaders(aesKey),
      body: JSON.stringify(note)
    })
    return handleResponse(response)
  },

  async get(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  },

  async update(aesKey, id, note) {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(aesKey),
      body: JSON.stringify(note)
    })
    return handleResponse(response)
  },

  async delete(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(aesKey)
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
  },

  async getRaw(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}/raw`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  },

  async getAesLog(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}/aes-log`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  },

  async getAesLogDecrypt(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}/aes-log-decrypt`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  },

  async getRoundKeys(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}/round-keys`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  }
}