<template>
  <div class="editor-view">
    <div v-if="loading" class="loading">Memuat...</div>
    
    <!-- Decryption Animation Overlay (when loading existing note) -->
    <AesAnimation
      v-if="showDecryptAnimation"
      :visible="showDecryptAnimation"
      :title="'Membuka Catatan (Dekripsi)'"
      :aes-key="cryptoStore.aesKey"
      :ciphertext="decryptData.ciphertext"
      :iv="decryptData.iv"
      :auto-play="true"
      :mode="'decrypt'"
      :show-cbc-flow="true"
      close-text="Batal"
      @close="cancelDecryptAnimation"
      @complete="onDecryptComplete"
    />
    
    <form v-else-if="!showAnimation" @submit.prevent="save" class="editor-form">
      <div class="form-group">
        <label for="title" class="label">Judul</label>
        <input
          id="title"
          v-model="form.title"
          type="text"
          class="input"
          placeholder="Judul catatan"
          required
          maxlength="200"
        />
      </div>
      
      <div class="form-group">
        <label for="body" class="label">Isi</label>
        <textarea
          id="body"
          v-model="form.body"
          class="input textarea"
          placeholder="Tulis catatan Anda di sini..."
          rows="15"
          maxlength="10000"
        ></textarea>
      </div>
      
      <div class="form-actions">
        <router-link to="/notes" class="btn btn-secondary">
          Batal
        </router-link>
        
        <button type="submit" class="btn btn-primary" :disabled="saving">
          <span v-if="saving">Menyimpan...</span>
          <span v-else>{{ isEditing ? 'Perbarui' : 'Simpan' }}</span>
        </button>
      </div>
    </form>
    
    <!-- Encryption Animation Overlay (when saving) -->
    <AesAnimation
      v-if="showAnimation"
      :visible="showAnimation"
      :title="isEditing ? 'Memperbarui Catatan (Enkripsi)' : 'Menyimpan Catatan Baru (Enkripsi)'"
      :input-text="encryptionData.inputText"
      :aes-key="cryptoStore.aesKey"
      :iv="encryptionData.iv"
      :ciphertext="encryptionData.ciphertext"
      :auto-play="true"
      :mode="'encrypt'"
      :show-cbc-flow="true"
      close-text="Batal"
      @close="closeAnimation"
      @complete="finishSave"
    />
    
    <div v-if="error" class="error-banner">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCryptoStore } from '@/stores/crypto'
import { useNotesStore } from '@/stores/notes'
import AesAnimation from '@/components/AesAnimation.vue'

const route = useRoute()
const router = useRouter()
const cryptoStore = useCryptoStore()
const notesStore = useNotesStore()

const isEditing = computed(() => route.params.id !== undefined)
const noteId = computed(() => route.params.id)

const form = ref({ title: '', body: '' })
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const showAnimation = ref(false)
const showDecryptAnimation = ref(false)
const pendingSave = ref(null) // 'create' or 'update'
const pendingEncryptedPayload = ref(null)
const encryptionData = ref({ inputText: '', ciphertext: null, iv: null })
const decryptData = ref({ ciphertext: null, iv: null, rawNote: null })

// Helper to convert base64 to Uint8Array
const base64ToBytes = (b64) => {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

const loadNote = async () => {
  if (!isEditing.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    // First, fetch raw ciphertext and IV for decryption animation
    const rawNote = await notesStore.getNoteRaw(cryptoStore.aesKey, noteId.value)
    
    if (rawNote) {
      // Store ciphertext and IV for decryption animation (convert base64 to Uint8Array)
      decryptData.value = {
        ciphertext: base64ToBytes(rawNote.body_ciphertext || rawNote.body),
        iv: base64ToBytes(rawNote.body_iv),
        rawNote
      }
      showDecryptAnimation.value = true
    } else {
      error.value = 'Catatan tidak ditemukan'
      loading.value = false
    }
  } catch (e) {
    error.value = e.message || 'Gagal memuat catatan'
    loading.value = false
  }
}

const onDecryptComplete = async () => {
  showDecryptAnimation.value = false
  
  try {
    const note = notesStore.decryptNoteLocally(decryptData.value.rawNote, cryptoStore.aesKey)
    if (note.title === '[Gagal dekripsi]' || note.body === '[Gagal dekripsi]') {
      error.value = 'Gagal dekripsi: passphrase salah atau data rusak'
      return
    }
    form.value.title = note.title
    form.value.body = note.body
  } catch (e) {
    error.value = e.message || 'Gagal memuat catatan'
  } finally {
    loading.value = false
  }
}

const cancelDecryptAnimation = () => {
  showDecryptAnimation.value = false
  loading.value = false
  router.push({ name: 'notes' })
}

const save = async () => {
  if (!form.value.title.trim()) {
    error.value = 'Judul tidak boleh kosong'
    return
  }
  
  error.value = ''
  saving.value = true
  
  try {
    pendingEncryptedPayload.value = notesStore.encryptNoteLocally(
      form.value.title,
      form.value.body,
      cryptoStore.aesKey
    )
    const animationField = form.value.body.length > 0 ? 'body' : 'title'
    const animationIvField = `${animationField}_iv`
    encryptionData.value = {
      inputText: form.value[animationField],
      ciphertext: base64ToBytes(pendingEncryptedPayload.value[animationField]),
      iv: base64ToBytes(pendingEncryptedPayload.value[animationIvField])
    }
    if (isEditing.value) {
      // Show encryption animation for update
      pendingSave.value = 'update'
      showAnimation.value = true
    } else {
      // Show encryption animation for create
      pendingSave.value = 'create'
      showAnimation.value = true
    }
  } catch (e) {
    error.value = e.message || 'Gagal memulai enkripsi'
    saving.value = false
  }
}

const closeAnimation = () => {
  showAnimation.value = false
  pendingSave.value = null
  pendingEncryptedPayload.value = null
  encryptionData.value = { inputText: '', ciphertext: null, iv: null }
  saving.value = false
}

const finishSave = async () => {
  showAnimation.value = false
  
  try {
    if (pendingSave.value === 'update') {
      await notesStore.updateNote(
        cryptoStore.aesKey, 
        noteId.value, 
        form.value.title, 
        form.value.body,
        pendingEncryptedPayload.value
      )
    } else if (pendingSave.value === 'create') {
      await notesStore.createNote(
        cryptoStore.aesKey, 
        form.value.title, 
        form.value.body,
        pendingEncryptedPayload.value
      )
    }
    router.push({ name: 'notes' })
  } catch (e) {
    error.value = e.message || 'Gagal menyimpan catatan'
  } finally {
    saving.value = false
    pendingSave.value = null
    pendingEncryptedPayload.value = null
    encryptionData.value = { inputText: '', ciphertext: null, iv: null }
  }
}

onMounted(() => {
  loadNote()
})
</script>

<style scoped>
.editor-view {
  max-width: 800px;
}

.loading {
  text-align: center;
  padding: 48px;
  color: #6B6B6B;
}

.editor-form {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-size: 13px;
  font-weight: 500;
  color: #0A0A0A;
}

.input {
  padding: 10px 14px;
  font-size: 14px;
  font-family: 'DM Sans', sans-serif;
  border: 1px solid #E8E8EC;
  border-radius: 6px;
  background: #FFFFFF;
  color: #0A0A0A;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  width: 100%;
}

.input:focus {
  outline: none;
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.textarea {
  resize: vertical;
  min-height: 200px;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.6;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid #E8E8EC;
}

.error-banner {
  margin-top: 16px;
  padding: 12px 16px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 8px;
  color: #EF4444;
  font-size: 14px;
}

.btn {
  padding: 10px 18px;
  font-size: 14px;
  font-family: 'DM Sans', sans-serif;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  user-select: none;
}

.btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #6D70F7 0%, #4338CA 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: #FFFFFF;
  color: #4B5563;
  font-weight: 500;
  border: 1px solid #E5E7EB;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.btn-secondary:hover {
  background: #F9FAFB;
  color: #111827;
  border-color: #D1D5DB;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.btn-secondary:active {
  transform: translateY(0);
  background: #F3F4F6;
}

@media (max-width: 640px) {
  .editor-form {
    padding: 16px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
</style>