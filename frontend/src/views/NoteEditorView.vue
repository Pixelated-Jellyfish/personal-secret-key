<template>
  <div class="editor-view">
    <div v-if="loading" class="loading">Memuat...</div>
    
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
        <router-link :to="`/notes/${noteId}`" class="btn btn-secondary" v-if="isEditing">
          Batal
        </router-link>
        <router-link to="/notes" class="btn btn-secondary" v-else>
          Batal
        </router-link>
        
        <button type="submit" class="btn btn-primary" :disabled="saving">
          <span v-if="saving">Menyimpan...</span>
          <span v-else>{{ isEditing ? 'Perbarui' : 'Simpan' }}</span>
        </button>
      </div>
    </form>
    
    <!-- Encryption Animation Overlay -->
    <EncryptionAnimation
      v-if="showAnimation"
      :visible="showAnimation"
      :title="isEditing ? 'Memperbarui Catatan (Enkripsi)' : 'Menyimpan Catatan Baru (Enkripsi)'"
      :input-text="form.title + '\n' + form.body"
      :aes-key="cryptoStore.aesKey"
      :auto-play="true"
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
import EncryptionAnimation from '@/components/EncryptionAnimation.vue'

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
const pendingSave = ref(null) // 'create' or 'update'

const loadNote = async () => {
  if (!isEditing.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    const note = await notesStore.getNote(cryptoStore.aesKey, noteId.value)
    if (note) {
      form.value.title = note.title
      form.value.body = note.body
    } else {
      error.value = 'Catatan tidak ditemukan'
    }
  } catch (e) {
    error.value = e.message || 'Gagal memuat catatan'
  } finally {
    loading.value = false
  }
}

const save = async () => {
  if (!form.value.title.trim()) {
    error.value = 'Judul tidak boleh kosong'
    return
  }
  
  error.value = ''
  saving.value = true
  
  try {
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
        form.value.body
      )
    } else if (pendingSave.value === 'create') {
      const newId = await notesStore.createNote(
        cryptoStore.aesKey, 
        form.value.title, 
        form.value.body
      )
      router.push({ name: 'note-edit', params: { id: newId } })
      return
    }
    router.push({ name: 'notes' })
  } catch (e) {
    error.value = e.message || 'Gagal menyimpan catatan'
  } finally {
    saving.value = false
    pendingSave.value = null
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
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: #6366F1;
  color: #FFFFFF;
}

.btn-primary:hover:not(:disabled) {
  background: #4F46E5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: transparent;
  color: #6366F1;
  border: 1px solid #6366F1;
}

.btn-secondary:hover {
  background: rgba(99, 102, 241, 0.1);
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