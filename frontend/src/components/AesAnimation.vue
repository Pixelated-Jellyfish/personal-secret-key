<template>
  <div v-if="visible" class="aes-animation-overlay" @click.self="close">
    <transition name="modal">
      <div class="aes-modal" ref="modal">
        <div class="modal-header">
          <h2>{{ title }}</h2>
          <div class="progress-indicator">
            <span class="current-step">{{ currentStep + 1 }}</span>
            <span class="separator">/</span>
            <span class="total-steps">{{ totalSteps }}</span>
          </div>
        </div>

        <div class="animation-content">
          <!-- Animation Canvas Area -->
          <div class="canvas-area">
            <div 
              class="state-visualization" 
              ref="stateViz"
              :class="{ 'with-iv': showCbcFlow && props.iv }"
            >
              <!-- Input Matrix -->
              <div class="matrix-panel input-panel">
                <div class="panel-header">
                  <span class="panel-title">{{ inputPanelTitle }}</span>
                  <span class="panel-label">16 bytes → 4×4 Matrix</span>
                </div>
                <HexMatrix :matrix="inputMatrix" :highlight="highlightInput" />
              </div>

              <!-- IV Panel for CBC Mode -->
              <div v-if="showCbcFlow && props.iv" class="matrix-panel iv-panel">
                <div class="panel-header">
                  <span class="panel-title">IV (Initialization Vector)</span>
                  <span class="panel-label">16 bytes → 4×4 Matrix</span>
                </div>
                <HexMatrix :matrix="ivMatrix" :highlight="highlightInput" />
              </div>

              <!-- Animated State Transition -->
              <div class="matrix-panel animated-panel">
                <div class="panel-header">
                  <span class="panel-title">{{ currentStepInfo?.description || 'AES State' }}</span>
                  <span class="panel-label" v-if="currentStepInfo">{{ getStepLabel(currentStepInfo) }}</span>
                </div>
                <div class="state-matrix-container">
                  <HexMatrix 
                    :matrix="animatedMatrix" 
                    :compact="false"
                    :prev-matrix="prevMatrix"
                    :changed-cells="changedCells"
                    class="animated-matrix"
                  />
                </div>
                
                <!-- Step Description -->
                <div class="step-description" v-if="currentStepInfo">
                  <div class="step-icon" :class="stepIconClass">
                    <span v-if="isSubBytesStep">{{ mode === 'encrypt' ? '◐' : '◑' }}</span>
                    <span v-else-if="isShiftRowsStep">↻</span>
                    <span v-else-if="isMixColumnsStep">⊞</span>
                    <span v-else-if="isAddRoundKeyStep">⊕</span>
                    <span v-else>●</span>
                  </div>
                  <p class="step-text">{{ getStepDescription(currentStepInfo.step) }}</p>
                </div>
              </div>

              <!-- Output Matrix -->
              <div class="matrix-panel output-panel">
                <div class="panel-header">
                  <span class="panel-title">{{ outputPanelTitle }}</span>
                  <span class="panel-label">{{ outputPanelLabel }}</span>
                </div>
                <HexMatrix 
                  :matrix="outputMatrix" 
                  :highlight="highlightOutput"
                  :fade-in="animationComplete"
                />
              </div>
            </div>

            <!-- Round Keys Sidebar -->
            <div class="round-keys-sidebar" v-if="showRoundKeys && roundKeys.length > 0">
              <div class="sidebar-header">
                <h4>Round Keys (K0-K10)</h4>
                <span class="key-count">{{ roundKeys.length }} keys</span>
              </div>
              <div class="round-keys-list">
                <div 
                  v-for="(rk, idx) in roundKeys" 
                  :key="idx"
                  class="round-key-item"
                  :class="{ active: currentRoundKey === idx }"
                >
                  <span class="key-label">K{{ idx }}</span>
                  <HexMatrix :matrix="rk" :compact="true" />
                  <div class="key-badges" v-if="keyExpansionTrace[idx - 1]">
                    <span v-if="keyExpansionTrace[idx - 1].rotword" class="badge rot">RotWord</span>
                    <span v-if="keyExpansionTrace[idx - 1].subword" class="badge sub">SubWord</span>
                    <span v-if="keyExpansionTrace[idx - 1].rcon" class="badge rcon">Rcon: {{ keyExpansionTrace[idx - 1].rcon }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="progress-bar-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${progressPercent}%` }"
              ></div>
              <div 
                v-for="(step, idx) in animationSteps" 
                :key="idx"
                class="progress-marker"
                :class="{ active: idx <= currentStep, current: idx === currentStep }"
                :style="{ left: `${(idx / (animationSteps.length - 1)) * 100}%` }"
              ></div>
            </div>
            <div class="step-labels">
              <span v-for="(step, idx) in animationSteps" :key="idx" :class="{ active: idx === currentStep }">
                {{ getShortStepName(step.step) }}
              </span>
            </div>
          </div>

          <!-- Control Buttons -->
          <div class="animation-controls">
            <button 
              class="btn btn-primary" 
              @click="toggleAnimation"
              :disabled="animating && currentStep === totalSteps - 1"
            >
              <span v-if="animating && currentStep < totalSteps - 1">Berhenti</span>
              <span v-else-if="animating">Selesai</span>
              <span v-else-if="currentStep === totalSteps - 1">Ulangi</span>
              <span v-else>Mulai Animasi</span>
            </button>
          </div>

          <!-- Status Message -->
          <div class="status-message" v-if="statusMessage">
            <span class="status-icon">{{ statusIcon }}</span>
            <span>{{ statusMessage }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-ghost" @click="close">{{ closeText }}</button>
          <button v-if="onComplete" class="btn btn-primary" @click="handleComplete">Lanjutkan</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import HexMatrix from './HexMatrix.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  inputText: { type: String, default: '' },
  aesKey: { type: Object, default: null }, // Uint8Array
  iv: { type: Object, default: null }, // Uint8Array for CBC
  ciphertext: { type: Object, default: null }, // Stored ciphertext bytes
  autoPlay: { type: Boolean, default: true },
  onComplete: { type: Function, default: null },
  mode: { type: String, default: 'encrypt', validator: v => ['encrypt', 'decrypt'].includes(v) },
  traceData: { type: Array, default: () => [] }, // Pre-computed trace from API
  roundKeysData: { type: Array, default: () => [] }, // Pre-computed round keys from API
  keyExpansionTraceData: { type: Array, default: () => [] },
  showCbcFlow: { type: Boolean, default: true }, // Show IV XOR step for CBC
  closeText: { type: String, default: 'Tutup' }
})

const emit = defineEmits(['close', 'complete'])

const stateViz = ref(null)
const modal = ref(null)

const currentStep = ref(0)
const animating = ref(false)
const animationSteps = ref([])
const inputMatrix = ref([])
const animatedMatrix = ref([])
const prevMatrix = ref([])
const changedCells = ref([])
const outputMatrix = ref([])
const roundKeys = ref([])
const keyExpansionTrace = ref([])
const highlightInput = ref(false)
const highlightOutput = ref(false)
const animationComplete = ref(false)
const showRoundKeys = ref(true)
const currentRoundKey = ref(0)
const statusMessage = ref('')
const statusIcon = ref('')
const ivMatrix = ref([])

// Animation timing
const STEP_DELAY = 800 // ms between steps

const totalSteps = computed(() => animationSteps.value.length)
const progressPercent = computed(() => totalSteps.value > 0 ? ((currentStep.value + 1) / totalSteps.value) * 100 : 0)
const currentStepInfo = computed(() => animationSteps.value[currentStep.value] || null)

const mode = computed(() => props.mode)

const inputPanelTitle = computed(() => mode.value === 'encrypt' ? 'Plaintext Input' : 'Ciphertext Input')
const outputPanelTitle = computed(() => mode.value === 'encrypt' ? 'Ciphertext Output' : 'Plaintext Output')
const outputPanelLabel = computed(() => mode.value === 'encrypt' ? 'Encrypted 16 bytes' : 'Decrypted 16 bytes')

const defaultTitle = computed(() => mode.value === 'encrypt' ? 'Proses Enkripsi AES-128' : 'Proses Dekripsi AES-128')
const displayTitle = computed(() => props.title || defaultTitle.value)

function getStepLabel(stepInfo) {
  const round = stepInfo.round
  const stepName = getStepName(stepInfo.step)
  return `Ronde ${round}, ${stepName}`
}

function getStepName(step) {
  const encryptNames = {
    'add_round_key_initial': 'AddRoundKey (Initial)',
    'sub_bytes': 'SubBytes',
    'shift_rows': 'ShiftRows',
    'mix_columns': 'MixColumns',
    'add_round_key': 'AddRoundKey'
  }
  const decryptNames = {
    'add_round_key_initial': 'AddRoundKey (Round 10)',
    'inv_shift_rows': 'InvShiftRows',
    'inv_sub_bytes': 'InvSubBytes',
    'add_round_key': 'AddRoundKey',
    'inv_mix_columns': 'InvMixColumns'
  }
  const names = mode.value === 'encrypt' ? encryptNames : decryptNames
  return names[step] || step
}

function getShortStepName(step) {
  const encryptNames = {
    'add_round_key_initial': 'ARK₀',
    'sub_bytes': 'SB',
    'shift_rows': 'SR',
    'mix_columns': 'MC',
    'add_round_key': 'ARK',
    'cbc_xor_iv': 'IV⊕'
  }
  const decryptNames = {
    'add_round_key_initial': 'ARK₁₀',
    'inv_shift_rows': 'ISR',
    'inv_sub_bytes': 'ISB',
    'add_round_key': 'ARK',
    'inv_mix_columns': 'IMC',
    'cbc_xor_iv': 'IV⊕'
  }
  const names = mode.value === 'encrypt' ? encryptNames : decryptNames
  return names[step] || step.slice(0, 3)
}

function getStepDescription(step) {
  const encryptDescriptions = {
    'add_round_key_initial': 'XOR plaintext dengan Round Key 0 (Initial AddRoundKey)',
    'sub_bytes': 'Substitusi setiap byte menggunakan S-Box AES',
    'shift_rows': 'Geser baris 1, 2, 3 ke kiri masing-masing 1, 2, 3 posisi',
    'mix_columns': 'Campur kolom menggunakan perkalian Galois Field (GF(2⁸))',
    'add_round_key': 'XOR state dengan Round Key ronde ini',
    'cbc_xor_iv': 'CBC Mode: XOR Plaintext dengan IV (Initialization Vector)'
  }
  const decryptDescriptions = {
    'add_round_key_initial': 'XOR ciphertext dengan Round Key 10 (Initial AddRoundKey)',
    'inv_shift_rows': 'Geser baris 1, 2, 3 ke kanan masing-masing 1, 2, 3 posisi (inverse ShiftRows)',
    'inv_sub_bytes': 'Substitusi balik setiap byte menggunakan Inverse S-Box AES',
    'add_round_key': 'XOR state dengan Round Key ronde ini',
    'inv_mix_columns': 'Campur kolom balik menggunakan matriks Inverse MixColumns (GF(2⁸))',
    'cbc_xor_iv': 'CBC Mode: XOR Hasil Dekripsi dengan IV = Plaintext Asli'
  }
  const descriptions = mode.value === 'encrypt' ? encryptDescriptions : decryptDescriptions
  return descriptions[step] || ''
}

const isSubBytesStep = computed(() => {
  if (!currentStepInfo.value) return false
  const step = currentStepInfo.value.step
  return step === 'sub_bytes' || step === 'inv_sub_bytes'
})

const isShiftRowsStep = computed(() => {
  if (!currentStepInfo.value) return false
  const step = currentStepInfo.value.step
  return step === 'shift_rows' || step === 'inv_shift_rows'
})

const isMixColumnsStep = computed(() => {
  if (!currentStepInfo.value) return false
  const step = currentStepInfo.value.step
  return step === 'mix_columns' || step === 'inv_mix_columns'
})

const isAddRoundKeyStep = computed(() => {
  if (!currentStepInfo.value) return false
  return currentStepInfo.value.step.includes('add_round_key')
})

const isCbcXorStep = computed(() => {
  if (!currentStepInfo.value) return false
  return currentStepInfo.value.step === 'cbc_xor_iv'
})

const stepIconClass = computed(() => {
  if (!currentStepInfo.value) return ''
  if (isSubBytesStep.value) return 'icon-sub'
  if (isShiftRowsStep.value) return 'icon-shift'
  if (isMixColumnsStep.value) return 'icon-mix'
  if (isAddRoundKeyStep.value) return 'icon-xor'
  if (isCbcXorStep.value) return 'icon-xor'
  return ''
})

async function initializeAnimation() {
  if (!props.aesKey || (mode.value === 'encrypt' && !props.inputText)) return

  // If traceData is provided (from API), use it directly
  if (props.traceData.length > 0) {
    animationSteps.value = props.traceData
    inputMatrix.value = props.traceData[0] ? getInputMatrixFromTrace(props.traceData) : []
    outputMatrix.value = props.traceData[props.traceData.length - 1] ? props.traceData[props.traceData.length - 1].state : []
    roundKeys.value = props.roundKeysData.length > 0 ? props.roundKeysData : []
    keyExpansionTrace.value = props.keyExpansionTraceData.length > 0 ? props.keyExpansionTraceData : []
  } else {
    // Fallback: compute locally (for backwards compatibility)
    await initializeAnimationLocal()
  }

  // Reset animation state
  currentStep.value = 0
  animating.value = false
  animationComplete.value = false
  highlightInput.value = true
  highlightOutput.value = false
  currentRoundKey.value = mode.value === 'encrypt' ? 0 : 10
  changedCells.value = []
  animatedMatrix.value = JSON.parse(JSON.stringify(inputMatrix.value))
  prevMatrix.value = JSON.parse(JSON.stringify(inputMatrix.value))

  statusMessage.value = mode.value === 'encrypt' ? 'Siap memulai animasi enkripsi...' : 'Siap memulai animasi dekripsi...'
  statusIcon.value = '▶'

  if (props.autoPlay) {
    await nextTick()
    startAnimation()
  }
}

function getInputMatrixFromTrace(trace) {
  // For encrypt: first trace step is after initial AddRoundKey, so input is before that
  // For decrypt: first trace step is after initial AddRoundKey (round 10), so input is before that
  // We need to reverse the first step to get input
  // Since we don't have the pre-initial state in trace, we'll use a different approach
  // The API should provide input_matrix separately
  return []
}

async function initializeAnimationLocal() {
  // Import AES functions
  const { 
    bytesToState, 
    stateToHex, 
    keyExpansion, 
    keyExpansionWithTrace,
    encryptBlock,
    decryptBlock,
    pkcs7Pad,
    pkcs7Unpad,
    hexToBytes
  } = await import('@/crypto/aes-client.js')

  // Generate round keys
  const rk = keyExpansion(props.aesKey)
  roundKeys.value = rk.map(k => stateToHex(k))

  // Key expansion trace
  const { traceInfo } = keyExpansionWithTrace(props.aesKey)
  keyExpansionTrace.value = traceInfo

  if (mode.value === 'encrypt') {
    await initializeEncryption(rk, bytesToState, stateToHex, encryptBlock, pkcs7Pad)
  } else {
    await initializeDecryption(rk, bytesToState, stateToHex, decryptBlock, pkcs7Unpad)
  }

  animatedMatrix.value = JSON.parse(JSON.stringify(inputMatrix.value))
  prevMatrix.value = JSON.parse(JSON.stringify(inputMatrix.value))
}

async function initializeEncryption(rk, bytesToState, stateToHex, encryptBlock, pkcs7Pad) {
  const encoder = new TextEncoder()
  let inputBytes = encoder.encode(props.inputText)
  
  if (inputBytes.length < 16) {
    inputBytes = pkcs7Pad(inputBytes)
  }
  
  // For CBC, we need IV
  const iv = props.iv || crypto.getRandomValues(new Uint8Array(16))
  
  // Store IV matrix for visualization
  ivMatrix.value = stateToHex(bytesToState(iv))
  
  // First block: plaintext XOR IV
  const firstBlock = inputBytes.slice(0, 16)
  const xorBlock = new Uint8Array(16)
  for (let j = 0; j < 16; j++) {
    xorBlock[j] = firstBlock[j] ^ iv[j]
  }
  
  // Store IV and plaintext for visualization
  inputMatrix.value = stateToHex(bytesToState(firstBlock))
  outputMatrix.value = [] // Will be set after encryption
  
  // If showing CBC flow, add IV XOR as first step
  if (props.showCbcFlow) {
    const xorMatrix = stateToHex(bytesToState(xorBlock))
    
    // Prepend CBC XOR step to animation steps
    const { trace } = encryptBlock(xorBlock, rk, true)
    animationSteps.value = [
      {
        round: 0,
        step: 'cbc_xor_iv',
        state: xorMatrix,
        description: 'CBC: Plaintext ⊕ IV (First Block)'
      },
      ...trace
    ]
    
    // Encrypt to get final ciphertext
    const { ciphertext: generatedCiphertext } = encryptBlock(xorBlock, rk, false)
    const storedFirstBlock = props.ciphertext?.slice(0, 16)
    if (storedFirstBlock && !storedFirstBlock.every((byte, index) => byte === generatedCiphertext[index])) {
      throw new Error('Ciphertext animasi tidak cocok dengan data yang disimpan')
    }
    outputMatrix.value = stateToHex(bytesToState(storedFirstBlock || generatedCiphertext))
  } else {
    // Original behavior (ECB-style for first block)
    inputMatrix.value = stateToHex(bytesToState(firstBlock))
    const { trace } = encryptBlock(firstBlock, rk, true)
    animationSteps.value = trace
    const { ciphertext } = encryptBlock(firstBlock, rk, false)
    outputMatrix.value = stateToHex(bytesToState(ciphertext))
  }
}

async function initializeDecryption(rk, bytesToState, stateToHex, decryptBlock, pkcs7Unpad) {
  // For decryption, we need ciphertext and IV
  let ciphertext = props.ciphertext
  const iv = props.iv
  
  if (!ciphertext || !iv) {
    // Fallback: encrypt first then decrypt
    const encoder = new TextEncoder()
    let inputBytes = encoder.encode(props.inputText)
    if (inputBytes.length < 16) {
      inputBytes = pkcs7Pad(inputBytes)
    }
    const firstBlock = inputBytes.slice(0, 16)
    const { ciphertext: ct } = encryptBlock(firstBlock, rk, false)
    ciphertext = ct
  }
  
  // Store IV matrix for visualization
  ivMatrix.value = stateToHex(bytesToState(iv))
  
  const firstCipherBlock = ciphertext.slice(0, 16)
  
  // Input matrix = ciphertext
  inputMatrix.value = stateToHex(bytesToState(firstCipherBlock))
  
  // Decrypt with trace
  const { trace, plaintext } = decryptBlock(firstCipherBlock, rk, true)
  animationSteps.value = trace
  
  // Output matrix = decrypted block (before CBC XOR)
  const decryptedBlock = plaintext.slice(0, 16)
  outputMatrix.value = stateToHex(bytesToState(decryptedBlock))
  
  // If showing CBC flow, add IV XOR step at the end
  if (props.showCbcFlow) {
    const plaintextXor = new Uint8Array(16)
    for (let j = 0; j < 16; j++) {
      plaintextXor[j] = decryptedBlock[j] ^ iv[j]
    }
    const finalMatrix = stateToHex(bytesToState(plaintextXor))
    
    // Add CBC XOR step at the end
    animationSteps.value = [
      ...trace,
      {
        round: 0,
        step: 'cbc_xor_iv',
        state: finalMatrix,
        description: 'CBC: Decrypted Block ⊕ IV = Plaintext'
      }
    ]
    outputMatrix.value = finalMatrix
  }
}

function startAnimation() {
  if (animating.value) return
  animating.value = true
  highlightInput.value = false
  animateStep()
}

async function animateStep() {
  if (!animating.value || currentStep.value >= totalSteps.value) {
    finishAnimation()
    return
  }

  const step = animationSteps.value[currentStep.value]
  
  // Update status
  statusMessage.value = `Menjalankan: ${getStepName(step.step)} (Ronde ${step.round})`
  statusIcon.value = '⟳'

  // Update current round key highlight
  if (step.step.includes('add_round_key')) {
    currentRoundKey.value = step.round
  }

  // Animate matrix transition
  await animateMatrixTransition(step.state)

  // Move to next step
  currentStep.value++
  
  if (currentStep.value < totalSteps.value) {
    setTimeout(animateStep, STEP_DELAY)
  } else {
    finishAnimation()
  }
}

async function animateMatrixTransition(newStateHex) {
  // Calculate changed cells
  const changes = []
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      if (prevMatrix.value[r]?.[c] !== newStateHex[r]?.[c]) {
        changes.push({ row: r, col: c })
      }
    }
  }
  changedCells.value = changes

  // Store previous matrix
  prevMatrix.value = JSON.parse(JSON.stringify(animatedMatrix.value))
  
  // Trigger re-render with new matrix
  animatedMatrix.value = newStateHex
  
  // Wait for animation
  await new Promise(resolve => setTimeout(resolve, 300))
  
  // Clear changed cells highlight
  changedCells.value = []
}

function finishAnimation() {
  animating.value = false
  animationComplete.value = true
  highlightOutput.value = true
  statusMessage.value = mode.value === 'encrypt' ? 'Enkripsi selesai! Ciphertext telah dihasilkan.' : 'Dekripsi selesai! Plaintext telah dipulihkan.'
  statusIcon.value = '✓'
  
  setTimeout(() => {
    if (!props.visible || !animationComplete.value) return
    props.onComplete?.()
    emit('complete')
  }, 1500)
}

function toggleAnimation() {
  if (animating.value) {
    animating.value = false
    statusMessage.value = 'Animasi dihentikan'
    statusIcon.value = '⏸'
  } else if (currentStep.value >= totalSteps.value - 1) {
    // Restart
    resetAnimation()
    startAnimation()
  } else {
    startAnimation()
  }
}

function resetAnimation() {
  animating.value = false
  currentStep.value = 0
  animationComplete.value = false
  highlightInput.value = true
  highlightOutput.value = false
  currentRoundKey.value = mode.value === 'encrypt' ? 0 : 10
  changedCells.value = []
  animatedMatrix.value = JSON.parse(JSON.stringify(inputMatrix.value))
  prevMatrix.value = JSON.parse(JSON.parse(JSON.stringify(inputMatrix.value)))
  statusMessage.value = 'Animasi direset. Siap memulai lagi.'
  statusIcon.value = '↺'
}

function nextStep() {
  if (currentStep.value < totalSteps.value - 1 && !animating.value) {
    const step = animationSteps.value[currentStep.value]
    animateMatrixTransition(step.state).then(() => {
      if (step.step.includes('add_round_key')) {
        currentRoundKey.value = step.round
      }
      currentStep.value++
    })
  }
}

function previousStep() {
  if (currentStep.value > 0 && !animating.value) {
    currentStep.value--
    const step = animationSteps.value[currentStep.value]
    animatedMatrix.value = step.state
    prevMatrix.value = currentStep.value > 0 ? animationSteps.value[currentStep.value - 1].state : inputMatrix.value
    if (step.step.includes('add_round_key')) {
      currentRoundKey.value = step.round
    }
  }
}

function close() {
  animating.value = false
  emit('close')
}

function handleComplete() {
  emit('complete')
  close()
}

watch(() => props.visible, (val) => {
  if (val) {
    initializeAnimation()
  } else {
    animating.value = false
  }
})

onMounted(() => {
  if (props.visible) initializeAnimation()
})

watch(() => props.inputText, () => {
  if (props.visible) {
    initializeAnimation()
  }
})

watch(() => props.aesKey, () => {
  if (props.visible && props.aesKey) {
    initializeAnimation()
  }
})

watch(() => props.mode, () => {
  if (props.visible && props.aesKey) {
    initializeAnimation()
  }
})

watch(() => props.traceData, () => {
  if (props.visible && props.aesKey && props.traceData.length > 0) {
    initializeAnimation()
  }
})

onUnmounted(() => {
  animating.value = false
})
</script>

<style scoped>
.aes-animation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 24px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.aes-modal {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 16px;
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E8E8EC;
  background: #FAFAFA;
  border-radius: 16px 16px 0 0;
}

.modal-header h2 {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #0A0A0A;
  margin: 0;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: #6366F1;
  font-weight: 600;
}

.current-step {
  color: #0A0A0A;
}

.separator {
  color: #9C9C9C;
}

.total-steps {
  color: #6B6B6B;
}

.animation-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.canvas-area {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  height: calc(90vh - 280px);
  min-height: 500px;
}

@media (max-width: 1024px) {
  .canvas-area {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .round-keys-sidebar {
    max-height: 300px;
    overflow: auto;
  }
}

.state-visualization {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  height: 100%;
}

.state-visualization.with-iv {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 900px) {
  .state-visualization,
  .state-visualization.with-iv {
    grid-template-columns: 1fr;
  }
}

.matrix-panel {
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.input-panel {
  border-color: #A5D6A7;
}

.iv-panel {
  border-color: #FFAB91;
}

.output-panel {
  border-color: #FFAB91;
}

.animated-panel {
  border-color: #6366F1;
  flex: 1;
  min-width: 0;
}

.panel-header {
  padding: 12px 16px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8E8EC;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.panel-title {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #0A0A0A;
}

.panel-label {
  font-size: 11px;
  color: #9C9C9C;
  font-family: 'JetBrains Mono', monospace;
}

.state-matrix-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow: auto;
}

.animated-matrix {
  transition: all 0.3s ease;
}

.step-description {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #F5F0FF;
  border-top: 1px solid #E8E8EC;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.step-icon.icon-sub { background: #E0E7FF; color: #4F46E5; }
.step-icon.icon-shift { background: #D1FAE5; color: #059669; }
.step-icon.icon-mix { background: #FEF3C7; color: #D97706; }
.step-icon.icon-xor { background: #FCE7F3; color: #DB2777; }

.step-text {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  margin: 0;
  font-family: 'DM Sans', sans-serif;
}

.round-keys-sidebar {
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8E8EC;
}

.sidebar-header h4 {
  margin: 0;
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #0A0A0A;
}

.key-count {
  font-size: 11px;
  color: #9C9C9C;
  font-family: 'JetBrains Mono', monospace;
}

.round-keys-list {
  flex: 1;
  overflow: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.round-key-item {
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 8px;
  padding: 10px;
  transition: all 0.2s ease;
}

.round-key-item.active {
  border-color: #6366F1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

.key-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: #6366F1;
  display: block;
  margin-bottom: 8px;
}

.key-badges {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.badge {
  font-size: 8px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
}

.badge.rot { background: #E0E7FF; color: #4F46E5; }
.badge.sub { background: #D1FAE5; color: #059669; }
.badge.rcon { background: #FEF3C7; color: #D97706; }

.progress-bar-container {
  margin-top: 24px;
  padding: 16px;
  background: #FAFAFA;
  border-radius: 12px;
  border: 1px solid #E8E8EC;
}

.progress-bar {
  height: 8px;
  background: #E8E8EC;
  border-radius: 4px;
  position: relative;
  overflow: visible;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366F1, #8B5CF6);
  border-radius: 4px;
  transition: width 0.5s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 20px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4));
  border-radius: 0 4px 4px 0;
}

.progress-marker {
  position: absolute;
  top: -4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #E8E8EC;
  border: 2px solid #FFFFFF;
  transform: translateX(-50%);
  transition: all 0.3s ease;
  z-index: 2;
}

.progress-marker.active {
  background: #6366F1;
  border-color: #6366F1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
}

.progress-marker.current {
  transform: translateX(-50%) scale(1.3);
  box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.3);
}

.step-labels {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #9C9C9C;
}

.step-labels span.active {
  color: #6366F1;
  font-weight: 600;
}

.animation-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #E8E8EC;
  flex-wrap: wrap
}

.status-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  margin-top: 16px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.status-message:has(.status-icon:contains("✓")) {
  background: #ECFDF5;
  color: #059669;
  border: 1px solid #A7F3D0;
}

.status-message:has(.status-icon:contains("⟳")) {
  background: #EEF2FF;
  color: #4F46E5;
  border: 1px solid #C7D2FE;
}

.status-message:has(.status-icon:contains("⏸")) {
  background: #FEF3C7;
  color: #D97706;
  border: 1px solid #FDE68A;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #E8E8EC;
  background: #FAFAFA;
  border-radius: 0 0 16px 16px;
}

.btn {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  font-family: 'DM Sans', sans-serif;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.btn-secondary {
  background: #FFFFFF;
  color: #6366F1;
  border: 1px solid #6366F1;
}

.btn-secondary:hover:not(:disabled) {
  background: #EEF2FF;
}

.btn-ghost {
  background: transparent;
  color: #6B6B6B;
}

.btn-ghost:hover {
  background: #F5F5F5;
  color: #0A0A0A;
}

.btn-destructive {
  background: #FFFFFF;
  color: #EF4444;
  border: 1px solid #EF4444;
}

.btn-destructive:hover {
  background: #FEF2F2;
}

/* HexMatrix overrides for animation */
.matrix-cell.changed {
  animation: cellChange 0.5s ease;
  background: #FEF3C7 !important;
  border-color: #F59E0B !important;
  transform: scale(1.1);
}

@keyframes cellChange {
  0% { transform: scale(1); background: #FEF3C7; }
  50% { transform: scale(1.15); background: #FDE68A; }
  100% { transform: scale(1); background: #FEF3C7; }
}

.matrix-cell.fade-in {
  animation: fadeInCell 0.6s ease forwards;
  opacity: 0;
}

@keyframes fadeInCell {
  from { opacity: 0; transform: translateY(10px) scale(0.9); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>