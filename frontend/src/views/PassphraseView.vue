<template>
  <div class="passphrase-view">
    <div class="card" v-if="!showKeyAnimation">
      <div class="card-header">
        <h2>Buka SecretNotes</h2>
        <p class="subtitle">Masukkan passphrase untuk mengakses catatan terenkripsi</p>
      </div>
      
      <form @submit.prevent="submit" class="form">
        <div class="form-group">
          <label for="passphrase" class="label">Passphrase (min. 8 karakter)</label>
          <input
            id="passphrase"
            v-model="form.passphrase"
            type="password"
            class="input"
            :class="{ 'input-error': error }"
            placeholder="Masukkan passphrase"
            autocomplete="off"
            @keydown.enter="submit"
            required
            minlength="8"
          />
          <p v-if="error" class="error-message">{{ error }}</p>
        </div>
        
        <button type="submit" class="btn btn-primary" :disabled="loading || keyDeriving">
          <span v-if="keyDeriving">Mederivasi Kunci...</span>
          <span v-else-if="loading">Memproses...</span>
          <span v-else>Buka</span>
        </button>
      </form>
      
      <p class="hint">Passphrase minimal 8 karakter. Kunci AES di-derive menggunakan PBKDF2 (100.000 iterasi).</p>
    </div>
    
    <!-- Key Derivation Animation -->
    <div v-else class="key-animation-card">
      <div class="animation-header">
        <h2>Mederivasi Kunci AES</h2>
        <p class="subtitle">PBKDF2-HMAC-SHA256 (100.000 iterasi)</p>
      </div>
      
      <div class="key-derivation-steps">
        <div 
          v-for="(step, index) in derivationSteps" 
          :key="index"
          class="derivation-step"
          :class="{ active: currentStep >= index, completed: currentStep > index }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-description">{{ step.description }}</div>
            <div class="step-progress" v-if="currentStep === index">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${derivationProgress}%` }"></div>
              </div>
              <div class="progress-text">{{ derivationProgress }}%</div>
            </div>
            <div class="step-output" v-if="currentStep > index && step.output">
              <code>{{ step.output }}</code>
            </div>
          </div>
          <div class="step-icon" :class="{ active: currentStep === index, done: currentStep > index }">
            <span v-if="currentStep > index">✓</span>
            <span v-else-if="currentStep === index">◐</span>
            <span v-else>○</span>
          </div>
        </div>
      </div>
      
      <div class="key-result" v-if="keyDerived">
        <div class="result-header">
          <span class="result-icon">🔐</span>
          <h3>Kunci AES-128 Siap Digunakan</h3>
        </div>
        <div class="key-display">
          <div class="key-label">Kunci (Hex)</div>
          <code class="key-hex">{{ keyHex }}</code>
          <div class="key-label">Kunci (Base64)</div>
          <code class="key-b64">{{ keyBase64 }}</code>
        </div>
        <button class="btn btn-primary btn-continue" @click="completeUnlock">
          Lanjutkan ke Catatan
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCryptoStore } from '@/stores/crypto'

const router = useRouter()
const cryptoStore = useCryptoStore()

const form = ref({ passphrase: '' })
const error = ref('')
const loading = ref(false)
const showKeyAnimation = ref(false)
const currentStep = ref(0)
const derivationProgress = ref(0)
const keyDerived = ref(false)
const keyHex = ref('')
const keyBase64 = ref('')

const keyDeriving = computed(() => cryptoStore.keyDeriving)

const derivationSteps = [
  {
    title: 'Validasi Passphrase',
    description: 'Memeriksa panjang minimal 8 karakter',
    output: null
  },
  {
    title: 'Persiapan Salt',
    description: 'Menggunakan salt tetap: "secretnotes-salt-123456789012" (32 bytes)',
    output: '7365637265746e6f7465732d73616c742d313233343536373839303132'
  },
  {
    title: 'PBKDF2-HMAC-SHA256',
    description: 'Menjalankan 100.000 iterasi key derivation',
    output: null // Will be filled when complete
  },
  {
    title: 'Ekstraksi Kunci 16 Byte',
    description: 'Mengambil 16 byte pertama (128 bit) untuk AES-128',
    output: null // Will be filled when complete
  }
]

const submit = async () => {
  if (form.value.passphrase.length < 8) {
    error.value = 'Passphrase minimal 8 karakter'
    return
  }
  
  error.value = ''
  loading.value = true
  showKeyAnimation.value = true
  currentStep.value = 0
  derivationProgress.value = 0
  keyDerived.value = false
  
  // Step 1: Validate passphrase
  currentStep.value = 1
  await sleep(300)
  
  // Step 2: Salt
  currentStep.value = 2
  await sleep(300)
  
  // Step 3: PBKDF2
  currentStep.value = 3
  derivationProgress.value = 0
  
  // Simulate progress
  const progressInterval = setInterval(() => {
    if (derivationProgress.value < 90) {
      derivationProgress.value += Math.random() * 15 + 5
    }
  }, 100)
  
  try {
    const success = await cryptoStore.unlock(form.value.passphrase)
    
    clearInterval(progressInterval)
    derivationProgress.value = 100
    
    // Step 4: Extract key
    currentStep.value = 4
    await sleep(200)
    
    if (success) {
      keyHex.value = cryptoStore.keyHex
      keyBase64.value = cryptoStore.keyBase64
      derivationSteps[2].output = keyHex.value
      derivationSteps[3].output = keyBase64.value
      keyDerived.value = true
      // Wait for user to click "Lanjutkan ke Catatan"
    } else {
      error.value = 'Passphrase salah atau gagal derive kunci'
      showKeyAnimation.value = false
    }
  } catch (e) {
    clearInterval(progressInterval)
    error.value = 'Terjadi kesalahan saat derive kunci'
    showKeyAnimation.value = false
  } finally {
    loading.value = false
  }
}

const completeUnlock = () => {
  cryptoStore.persistKey()
  router.push({ name: 'notes' })
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

onMounted(() => {
  cryptoStore.checkKeyFromMemory()
  if (cryptoStore.hasKey) {
    router.push({ name: 'notes' })
  }
})
</script>

<style scoped>
.passphrase-view {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 24px;
}

.card {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  padding: 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.key-animation-card {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  padding: 32px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.card-header,
.animation-header {
  text-align: center;
  margin-bottom: 24px;
}

.card-header h2,
.animation-header h2 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #0A0A0A;
  margin-bottom: 8px;
  letter-spacing: -0.03em;
}

.subtitle {
  color: #6B6B6B;
  font-size: 14px;
  margin: 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
}

.input:focus {
  outline: none;
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.input-error {
  border-color: #EF4444;
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12);
}

.error-message {
  font-size: 12px;
  color: #EF4444;
  margin: 0;
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
  width: 100%;
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

.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #9C9C9C;
  text-align: center;
}

/* Key Derivation Animation Styles */
.key-derivation-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.derivation-step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.derivation-step.active {
  border-color: #6366F1;
  background: #EEF2FF;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.derivation-step.completed {
  border-color: #A5D6A7;
  background: #F0FDF4;
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #E8E8EC;
  color: #9C9C9C;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 2px;
}

.derivation-step.active .step-number {
  background: #6366F1;
  color: #FFFFFF;
}

.derivation-step.completed .step-number {
  background: #10B981;
  color: #FFFFFF;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #0A0A0A;
  margin-bottom: 4px;
}

.step-description {
  font-size: 13px;
  color: #6B6B6B;
  margin-bottom: 8px;
}

.step-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #E8E8EC;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366F1, #8B5CF6);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #6366F1;
  font-weight: 600;
  min-width: 45px;
}

.step-output {
  margin-top: 8px;
  padding: 8px 12px;
  background: #0A0A0A;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #A5D6A7;
  word-break: break-all;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  background: #E8E8EC;
  color: #9C9C9C;
  transition: all 0.3s ease;
}

.derivation-step.active .step-icon {
  background: #6366F1;
  color: #FFFFFF;
  animation: pulse 1s infinite;
}

.derivation-step.completed .step-icon {
  background: #10B981;
  color: #FFFFFF;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.key-result {
  background: #F0FDF4;
  border: 1px solid #A5D6A7;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.result-icon {
  font-size: 24px;
}

.result-header h3 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #059669;
  margin: 0;
}

.key-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.key-label {
  font-size: 12px;
  color: #6B6B6B;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.key-hex,
.key-b64 {
  background: #0A0A0A;
  color: #A5D6A7;
  padding: 12px 16px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  word-break: break-all;
  display: block;
}

.btn-continue {
  width: 100%;
  padding: 12px 24px;
  font-size: 15px;
}

@media (max-width: 480px) {
  .card,
  .key-animation-card {
    padding: 24px 16px;
  }
  
  .derivation-step {
    flex-direction: column;
    gap: 12px;
  }
  
  .step-icon {
    align-self: flex-start;
  }
}
</style>