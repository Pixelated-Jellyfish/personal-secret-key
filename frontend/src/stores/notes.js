import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notesApi } from '@/api/client'
import { encryptCBCBase64, decryptCBCBase64 } from '@/crypto/aes-client'

export const useNotesStore = defineStore('notes', () => {
  const notes = ref([])
  const loading = ref(false)
  const error = ref(null)
  const decrypting = ref(false)

  const sortedNotes = computed(() => 
    [...notes.value].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
  )

  // Decrypt note titles for display
  const notesWithDecryptedTitles = computed(() => {
    return sortedNotes.value.map(note => ({
      ...note,
      decryptedTitle: note.decryptedTitle || note.title
    }))
  })

  async function fetchNotes(aesKey) {
    loading.value = true
    error.value = null
    try {
      const fetchedNotes = await notesApi.list(aesKey)
      notes.value = fetchedNotes
    } catch (e) {
      error.value = e.message || 'Gagal memuat catatan'
      notes.value = []
    } finally {
      loading.value = false
    }
  }

  async function createNote(aesKey, title, body) {
    try {
      // Encrypt locally
      const titleEnc = encryptCBCBase64(title, aesKey)
      const bodyEnc = encryptCBCBase64(body, aesKey)

      const newNote = await notesApi.create(aesKey, { 
        title: titleEnc.ciphertext,
        title_iv: titleEnc.iv,
        body: bodyEnc.ciphertext,
        body_iv: bodyEnc.iv,
        client_encrypted: true
      })
      
      // Add to local list with decrypted title for immediate display
      notes.value.unshift({ 
        id: newNote.id, 
        title: titleEnc.ciphertext,
        title_iv: titleEnc.iv,
        decryptedTitle: title,
        updated_at: new Date().toISOString() 
      })
      return newNote.id
    } catch (e) {
      throw new Error(e.message || 'Gagal membuat catatan')
    }
  }

  async function updateNote(aesKey, id, title, body) {
    try {
      // Encrypt locally with new IV
      const titleEnc = encryptCBCBase64(title, aesKey)
      const bodyEnc = encryptCBCBase64(body, aesKey)

      await notesApi.update(aesKey, id, { 
        title: titleEnc.ciphertext,
        title_iv: titleEnc.iv,
        body: bodyEnc.ciphertext,
        body_iv: bodyEnc.iv,
        client_encrypted: true
      })
      
      const idx = notes.value.findIndex(n => n.id === id)
      if (idx !== -1) {
        notes.value[idx] = { 
          ...notes.value[idx], 
          title: titleEnc.ciphertext,
          title_iv: titleEnc.iv,
          decryptedTitle: title,
          updated_at: new Date().toISOString() 
        }
      }
    } catch (e) {
      throw new Error(e.message || 'Gagal memperbarui catatan')
    }
  }

  async function deleteNote(aesKey, id) {
    try {
      await notesApi.delete(aesKey, id)
      notes.value = notes.value.filter(n => n.id !== id)
    } catch (e) {
      throw new Error(e.message || 'Gagal menghapus catatan')
    }
  }

  async function getNote(aesKey, id) {
    try {
      const note = await notesApi.get(aesKey, id)
      return note
    } catch (e) {
      throw new Error(e.message || 'Gagal memuat catatan')
    }
  }

  async function getNoteRaw(aesKey, id) {
    try {
      return await notesApi.getRaw(aesKey, id)
    } catch (e) {
      throw new Error(e.message || 'Gagal memuat data catatan')
    }
  }

  // Decrypt note locally using client-side crypto
  function decryptNoteLocally(note, aesKey) {
    try {
      // Check if we have the required ciphertext and IV fields
      if (!note.title_iv || !note.body_iv) {
        // Note doesn't have raw ciphertext data (e.g., from list endpoint)
        return { title: note.title || '[Tidak tersedia]', body: note.body || '[Tidak tersedia]' }
      }
      const title = decryptCBCBase64(note.title_ciphertext || note.title, aesKey, note.title_iv)
      const body = decryptCBCBase64(note.body_ciphertext || note.body, aesKey, note.body_iv)
      return { title, body }
    } catch (e) {
      console.error('Local decryption failed:', e)
      return { title: '[Gagal dekripsi]', body: '[Gagal dekripsi]' }
    }
  }

  // Encrypt note locally for saving
  function encryptNoteLocally(title, body, aesKey) {
    const titleEnc = encryptCBCBase64(title, aesKey)
    const bodyEnc = encryptCBCBase64(body, aesKey)
    return {
      title: titleEnc.ciphertext,
      title_iv: titleEnc.iv,
      body: bodyEnc.ciphertext,
      body_iv: bodyEnc.iv
    }
  }

  async function getAesLog(aesKey, id) {
    return await notesApi.getAesLog(aesKey, id)
  }

  async function getAesLogDecrypt(aesKey, id) {
    return await notesApi.getAesLogDecrypt(aesKey, id)
  }

  async function getRoundKeys(aesKey, id) {
    return await notesApi.getRoundKeys(aesKey, id)
  }

  function clear() {
    notes.value = []
    error.value = null
  }

  return {
    notes,
    sortedNotes,
    notesWithDecryptedTitles,
    loading,
    error,
    decrypting,
    fetchNotes,
    createNote,
    updateNote,
    deleteNote,
    getNote,
    getNoteRaw,
    decryptNoteLocally,
    encryptNoteLocally,
    getAesLog,
    getAesLogDecrypt,
    getRoundKeys,
    clear
  }
})