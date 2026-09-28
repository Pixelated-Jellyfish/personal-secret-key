<template>
  <div class="notes-view">
    <div class="view-header">
      <h1>Catatan</h1>
      <router-link to="/notes/new" class="btn btn-primary">
        <span class="btn-icon">+</span> Catatan Baru
      </router-link>
    </div>
    
    <!-- Encryption Recap Animation (after saving note) -->
    <AesAnimation
      v-if="showEncryptionRecap"
      :visible="showEncryptionRecap"
      :title="'Catatan Tersimpan (Enkripsi)'"
      :input-text="recapData.title + '\n' + recapData.body"
      :aes-key="cryptoStore.aesKey"
      :auto-play="true"
      :mode="'encrypt'"
      :show-cbc-flow="true"
      @close="onRecapComplete"
      @complete="onRecapComplete"
    />
    
    <div v-else-if="loading" class="loading">Memuat...</div>
    
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="fetchNotes">Coba Lagi</button>
    </div>
    
    <div v-else-if="sortedNotes.length === 0" class="empty-state">
      <p>Belum ada catatan</p>
      <router-link to="/notes/new" class="btn btn-primary">Buat Catatan Pertama</router-link>
    </div>
    
    <ul v-else class="notes-list">
      <li v-for="note in sortedNotes" :key="note.id" class="note-item">
        <router-link :to="`/notes/${note.id}`" class="note-link">
          <div class="note-title">{{ note.decryptedTitle || note.title }}</div>
          <div class="note-meta">
            <time :datetime="note.updated_at">{{ formatDate(note.updated_at) }}</time>
          </div>
        </router-link>
        <button class="btn btn-ghost btn-delete" @click.stop="confirmDelete(note)">
          Hapus
        </button>
      </li>
    </ul>
    
    <!-- Delete confirmation modal -->
    <div v-if="noteToDelete" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal">
        <h3>Hapus Catatan</h3>
        <p>Yakin ingin menghapus "<strong>{{ noteToDelete.decryptedTitle || noteToDelete.title }}</strong>"? Tindakan ini tidak bisa dibatalkan.</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="cancelDelete">Batal</button>
          <button class="btn btn-destructive" @click="executeDelete">Hapus</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCryptoStore } from '@/stores/crypto'
import { useNotesStore } from '@/stores/notes'
import AesAnimation from '@/components/AesAnimation.vue'

const route = useRoute()
const router = useRouter()
const cryptoStore = useCryptoStore()
const notesStore = useNotesStore()

const noteToDelete = ref(null)
const showEncryptionRecap = ref(false)
const recapData = ref({ title: '', body: '' })

const sortedNotes = computed(() => notesStore.sortedNotes)
const loading = computed(() => notesStore.loading)
const error = computed(() => notesStore.error)

const fetchNotes = async () => {
  await notesStore.fetchNotes(cryptoStore.aesKey)
}

const confirmDelete = (note) => {
  noteToDelete.value = note
}

const cancelDelete = () => {
  noteToDelete.value = null
}

const executeDelete = async () => {
  if (noteToDelete.value) {
    await notesStore.deleteNote(cryptoStore.aesKey, noteToDelete.value.id)
    noteToDelete.value = null
  }
}

const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('id-ID', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Check for saved note data in query params on mount
onMounted(() => {
  checkForSavedNote()
  fetchNotes()
})

// Also check when route changes (e.g., returning from editor)
watch(() => route.fullPath, () => {
  checkForSavedNote()
})

const checkForSavedNote = () => {
  // Check for query params from editor after save
  if (route.query.saved && route.query.title && route.query.body) {
    recapData.value = {
      title: route.query.title,
      body: route.query.body
    }
    showEncryptionRecap.value = true
    // Clean up URL
    router.replace({ name: 'notes' })
  }
}

const onRecapComplete = () => {
  showEncryptionRecap.value = false
  recapData.value = { title: '', body: '' }
  fetchNotes()
}
</script>

<style scoped>
.notes-view {
  max-width: 800px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.view-header h1 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 32px;
  font-weight: 700;
  color: #0A0A0A;
  letter-spacing: -0.03em;
}

.loading,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #6B6B6B;
}

.error-state button,
.empty-state button {
  margin-top: 16px;
}

.notes-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 8px;
  padding: 16px;
  gap: 16px;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.note-item:hover {
  box-shadow: 0 8px 30px rgba(0,0,0,0.08);
  border-color: #D0D0D0;
  transform: translateY(-2px);
}

.note-link {
  flex: 1;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.note-title {
  font-size: 15px;
  font-weight: 500;
  color: #0A0A0A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note-meta {
  font-size: 12px;
  color: #9C9C9C;
}

.note-meta time {
  font-family: 'JetBrains Mono', monospace;
}

.btn-delete {
  flex-shrink: 0;
  padding: 6px 12px;
  font-size: 12px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal h3 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #0A0A0A;
}

.modal p {
  color: #6B6B6B;
  margin-bottom: 20px;
  line-height: 1.6;
}

.modal p strong {
  color: #0A0A0A;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 640px) {
  .view-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .view-header h1 {
    font-size: 24px;
  }
  
  .note-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .btn-delete {
    width: 100%;
    text-align: center;
  }
}
</style>