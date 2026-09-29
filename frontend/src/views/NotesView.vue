<template>
  <div class="notes-view">
    <div class="view-header">
      <div class="header-text">
        <h1>Catatan</h1>
        <p class="header-subtitle">Kelola dan amankan catatan terenkripsi AES Anda</p>
      </div>
      <router-link to="/notes/new" class="btn-new-note">
        <span class="btn-new-note-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </span>
        <span class="btn-new-note-text">Catatan Baru</span>
      </router-link>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Memuat catatan...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="fetchNotes">Coba Lagi</button>
    </div>
    
    <div v-else-if="sortedNotes.length === 0" class="empty-state">
      <div class="empty-icon-box">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <line x1="9" y1="15" x2="15" y2="15"></line>
        </svg>
      </div>
      <h3 class="empty-title">Belum ada catatan</h3>
      <p class="empty-subtitle">Semua catatan yang Anda buat akan dienkripsi secara aman dengan AES-128-CBC.</p>
      <router-link to="/notes/new" class="btn-new-note empty-btn">
        <span class="btn-new-note-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </span>
        <span class="btn-new-note-text">Buat Catatan Pertama</span>
      </router-link>
    </div>
    
    <ul v-else class="notes-list">
      <li v-for="note in sortedNotes" :key="note.id" class="note-item">
        <router-link :to="`/notes/${note.id}`" class="note-link">
          <div class="note-title-row">
            <span class="note-lock-icon">🔒</span>
            <div class="note-title">{{ note.decryptedTitle || note.title }}</div>
          </div>
          <div class="note-meta">
            <time :datetime="note.updated_at">{{ formatDate(note.updated_at) }}</time>
          </div>
        </router-link>
        <button class="btn btn-ghost btn-delete" @click.stop="confirmDelete(note)" title="Hapus catatan">
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
import { onMounted, ref, computed } from 'vue'
import { useCryptoStore } from '@/stores/crypto'
import { useNotesStore } from '@/stores/notes'

const cryptoStore = useCryptoStore()
const notesStore = useNotesStore()

const noteToDelete = ref(null)

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

onMounted(fetchNotes)
</script>

<style scoped>
.notes-view {
  max-width: 800px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-text h1 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 30px;
  font-weight: 700;
  color: #0A0A0A;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 14px;
  color: #6B6B6B;
  margin-top: 4px;
}

/* New Note Button */
.btn-new-note {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
  user-select: none;
}

.btn-new-note:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #6D70F7 0%, #4338CA 100%);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
}

.btn-new-note:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.btn-new-note-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.25s ease;
}

.btn-new-note:hover .btn-new-note-icon {
  transform: rotate(90deg) scale(1.1);
}

.btn-new-note-text {
  letter-spacing: -0.01em;
}

/* Loading & Error States */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  color: #6B6B6B;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E8E8EC;
  border-top-color: #6366F1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  text-align: center;
  padding: 48px 24px;
  color: #EF4444;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 12px;
}

.error-state button {
  margin-top: 16px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 56px 24px;
  background: #FFFFFF;
  border: 1px dashed #D4D4D8;
  border-radius: 16px;
}

.empty-icon-box {
  width: 64px;
  height: 64px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.empty-title {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #0A0A0A;
  margin-bottom: 6px;
}

.empty-subtitle {
  font-size: 14px;
  color: #6B6B6B;
  max-width: 380px;
  margin: 0 auto 24px;
  line-height: 1.5;
}

.empty-btn {
  padding: 12px 22px;
}

/* Notes List */
.notes-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.note-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 10px;
  padding: 16px 20px;
  gap: 16px;
  transition: all 0.2s ease;
}

.note-item:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  border-color: #CBD5E1;
  transform: translateY(-2px);
}

.note-link {
  flex: 1;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.note-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-lock-icon {
  font-size: 12px;
  opacity: 0.6;
}

.note-title {
  font-size: 15px;
  font-weight: 600;
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

/* General Buttons */
.btn {
  padding: 9px 18px;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  user-select: none;
  gap: 6px;
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

.btn-ghost {
  background: transparent;
  color: #9CA3AF;
  border: 1px solid transparent;
  font-weight: 500;
}

.btn-ghost:hover {
  color: #EF4444;
  background: #FEF2F2;
  border-color: #FEE2E2;
}

.btn-delete {
  flex-shrink: 0;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 8px;
}

.btn-destructive {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  color: #FFFFFF;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
}

.btn-destructive:hover {
  background: linear-gradient(135deg, #F87171 0%, #B91C1C 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45);
}

.btn-destructive:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
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
  border-radius: 14px;
  padding: 24px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
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
  margin-bottom: 8px;
  color: #0A0A0A;
}

.modal p {
  color: #6B6B6B;
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.6;
}

.modal p strong {
  color: #0A0A0A;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 640px) {
  .view-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn-new-note {
    justify-content: center;
  }
  
  .note-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn-delete {
    align-self: flex-end;
  }
}
</style>