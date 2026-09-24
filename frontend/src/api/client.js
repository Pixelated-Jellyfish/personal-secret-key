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

  async getRoundKeys(aesKey, id) {
    const response = await fetch(`${API_BASE}/notes/${id}/round-keys`, {
      headers: getAuthHeaders(aesKey)
    })
    return handleResponse(response)
  }
}