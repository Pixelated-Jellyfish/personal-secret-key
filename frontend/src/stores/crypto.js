import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { deriveKeyPBKDF2 } from '@/crypto/aes-client'

export const useCryptoStore = defineStore('crypto', () => {
  const aesKey = ref(null)
  const passphrase = ref('')
  const keyDeriving = ref(false)

  const hasKey = computed(() => aesKey.value !== null)

  async function unlock(inputPassphrase) {
    if (inputPassphrase.length < 8) {
      return false
    }

    keyDeriving.value = true
    try {
      const key = await deriveKeyPBKDF2(inputPassphrase)
      aesKey.value = key
      passphrase.value = inputPassphrase
      return true
    } catch (e) {
      console.error('Key derivation failed:', e)
      return false
    } finally {
      keyDeriving.value = false
    }
  }

  function lock() {
    aesKey.value = null
    passphrase.value = ''
    clearPersistedKey()
  }

  function checkKeyFromMemory() {
    const stored = sessionStorage.getItem('secretnotes_key')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        // Convert array back to Uint8Array
        aesKey.value = new Uint8Array(parsed.key)
        passphrase.value = parsed.passphrase
      } catch {
        sessionStorage.removeItem('secretnotes_key')
      }
    }
  }

  function persistKey() {
    if (aesKey.value) {
      sessionStorage.setItem('secretnotes_key', JSON.stringify({
        key: Array.from(aesKey.value),
        passphrase: passphrase.value
      }))
    }
  }

  function clearPersistedKey() {
    sessionStorage.removeItem('secretnotes_key')
  }

  // Get key as base64 for API header
  const keyBase64 = computed(() => {
    if (!aesKey.value) return null
    return btoa(String.fromCharCode(...aesKey.value))
  })

  // Get key as hex for display
  const keyHex = computed(() => {
    if (!aesKey.value) return null
    return Array.from(aesKey.value).map(b => b.toString(16).padStart(2, '0')).join('')
  })

  return {
    aesKey,
    passphrase,
    keyDeriving,
    hasKey,
    unlock,
    lock,
    checkKeyFromMemory,
    persistKey,
    clearPersistedKey,
    keyBase64,
    keyHex
  }
})