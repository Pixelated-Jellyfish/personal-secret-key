<template>
  <div class="aes-lab-view">
    <div class="view-header">
      <h1>AES Lab</h1>
      <p class="subtitle">Visualisasi proses enkripsi AES-128 untuk catatan terpilih</p>
    </div>
    
    <div v-if="!selectedNoteId" class="note-selector">
      <label for="note-select" class="label">Pilih Catatan</label>
      <select
        id="note-select"
        v-model="selectedNoteId"
        class="input"
        @change="loadData"
      >
        <option value="">-- Pilih catatan --</option>
        <option v-for="note in notes" :key="note.id" :value="note.id">
          {{ note.title }}
        </option>
      </select>
    </div>
    
    <div v-else class="lab-content">
      <div class="note-info">
        <h3>{{ currentNote?.title }}</h3>
        <router-link :to="`/notes/${selectedNoteId}`" class="link">Buka catatan</router-link>
      </div>
      
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      
      <div class="tab-panel">
        <!-- Blok Pertama Tab -->
        <div v-if="activeTab === 'block' && aesLog" class="panel-content">
          <div class="matrix-section">
            <h4>Blok Pertama Plaintext (Input Matrix)</h4>
            <HexMatrix :matrix="aesLog.input_matrix" />
          </div>
          
          <div class="trace-section">
            <h4>Trace Per Ronde</h4>
            <div class="trace-grid">
              <div
                v-for="step in aesLog.trace"
                :key="`${step.round}-${step.step}`"
                class="trace-step"
              >
                <div class="step-header">
                  <span class="step-round">Ronde {{ step.round }}</span>
                  <span class="step-name">{{ formatStepName(step.step) }}</span>
                </div>
                <HexMatrix :matrix="step.state" :compact="true" />
              </div>
            </div>
          </div>
        </div>
        
        <!-- Round Keys Tab -->
        <div v-else-if="activeTab === 'keys' && roundKeys" class="panel-content">
          <div class="round-keys-grid">
            <div
              v-for="(rk, index) in roundKeys.round_keys"
              :key="index"
              class="round-key-card"
            >
              <div class="round-key-header">
                <span class="round-key-label">Round Key {{ index }}</span>
                <span v-if="index < roundKeys.key_expansion_trace.length" class="key-info">
                  <span v-if="roundKeys.key_expansion_trace[index].rotword" class="badge badge-rot">RotWord</span>
                  <span v-if="roundKeys.key_expansion_trace[index].subword" class="badge badge-sub">SubWord</span>
                  <span v-if="roundKeys.key_expansion_trace[index].rcon" class="badge badge-rcon">Rcon: {{ roundKeys.key_expansion_trace[index].rcon }}</span>
                </span>
              </div>
              <HexMatrix :matrix="rk" :compact="true" />
            </div>
          </div>
        </div>
        
        <div v-else class="loading">Memuat data visualisasi...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCryptoStore } from '@/stores/crypto'
import { useNotesStore } from '@/stores/notes'
import HexMatrix from '@/components/HexMatrix.vue'

const cryptoStore = useCryptoStore()
const notesStore = useNotesStore()

const notes = ref([])
const selectedNoteId = ref('')
const currentNote = ref(null)
const aesLog = ref(null)
const roundKeys = ref(null)
const activeTab = ref('block')
const loading = ref(false)

const tabs = [
  { id: 'block', label: 'Blok Pertama' },
  { id: 'keys', label: 'Round Keys' }
]

const loadNotes = async () => {
  notes.value = notesStore.sortedNotes
}

const loadData = async () => {
  if (!selectedNoteId.value) return
  
  loading.value = true
  try {
    currentNote.value = await notesStore.getNote(cryptoStore.aesKey, selectedNoteId.value)
    aesLog.value = await notesStore.getAesLog(cryptoStore.aesKey, selectedNoteId.value)
    roundKeys.value = await notesStore.getRoundKeys(cryptoStore.aesKey, selectedNoteId.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatStepName = (step) => {
  const names = {
    'add_round_key_initial': 'AddRoundKey (Initial)',
    'sub_bytes': 'SubBytes',
    'shift_rows': 'ShiftRows',
    'mix_columns': 'MixColumns',
    'add_round_key': 'AddRoundKey'
  }
  return names[step] || step
}

onMounted(() => {
  loadNotes()
})

// Watch for notes changes
const unwatch = computed(() => notesStore.sortedNotes)
onMounted(() => {
  const stop = notesStore.$subscribe(() => {
    notes.value = notesStore.sortedNotes
  })
})
</script>

<style scoped>
.aes-lab-view {
  max-width: 1000px;
}

.view-header {
  margin-bottom: 24px;
}

.view-header h1 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 32px;
  font-weight: 700;
  color: #0A0A0A;
  letter-spacing: -0.03em;
  margin-bottom: 4px;
}

.subtitle {
  color: #6B6B6B;
  font-size: 14px;
}

.note-selector {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
}

.lab-content {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  overflow: hidden;
}

.note-info {
  padding: 20px 24px;
  border-bottom: 1px solid #E8E8EC;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.note-info h3 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #0A0A0A;
}

.link {
  font-size: 13px;
  color: #6366F1;
  text-decoration: none;
  font-weight: 500;
}

.link:hover {
  text-decoration: underline;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #E8E8EC;
  background: #FAFAFA;
  padding: 0 24px;
}

.tab {
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6B6B6B;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: -1px;
}

.tab:hover {
  color: #0A0A0A;
}

.tab.active {
  color: #6366F1;
  border-bottom-color: #6366F1;
}

.tab-panel {
  padding: 24px;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.matrix-section h4,
.trace-section h4,
.round-key-header {
  font-size: 14px;
  font-weight: 600;
  color: #0A0A0A;
  margin-bottom: 12px;
}

.trace-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.trace-step {
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 8px;
  padding: 16px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 13px;
}

.step-round {
  font-weight: 600;
  color: #6366F1;
  font-family: 'JetBrains Mono', monospace;
}

.step-name {
  color: #6B6B6B;
}

.round-keys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.round-key-card {
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 8px;
  padding: 16px;
}

.round-key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.round-key-label {
  font-weight: 600;
  color: #0A0A0A;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}

.key-info {
  display: flex;
  gap: 6px;
}

.badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.badge-rot {
  background: #E0E7FF;
  color: #4F46E5;
}

.badge-sub {
  background: #D1FAE5;
  color: #059669;
}

.badge-rcon {
  background: #FEF3C7;
  color: #D97706;
}

.loading {
  text-align: center;
  padding: 48px;
  color: #6B6B6B;
}

@media (max-width: 768px) {
  .round-keys-grid {
    grid-template-columns: 1fr;
  }
  
  .note-info {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>