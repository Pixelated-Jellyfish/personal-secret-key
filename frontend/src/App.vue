<template>
  <div class="app">
    <header class="nav" role="banner">
      <div class="nav-container">
        <h1 class="nav-title">SecretNotes</h1>
        <nav class="nav-links" aria-label="Main navigation">
          <router-link v-if="isUnlocked" to="/notes" class="nav-link" active-class="active">
            Catatan
          </router-link>
          <button v-if="isUnlocked" type="button" class="nav-link lock-link" @click="lockApp">
            Kunci
          </button>
        </nav>
      </div>
    </header>
    
    <main class="main-content" role="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useCryptoStore } from './stores/crypto'
import { useNotesStore } from './stores/notes'
import { useRouter } from 'vue-router'

const cryptoStore = useCryptoStore()
const notesStore = useNotesStore()
const router = useRouter()

const isUnlocked = computed(() => cryptoStore.hasKey)

function lockApp() {
  notesStore.clear()
  cryptoStore.lock()
  router.push({ name: 'passphrase' })
}

cryptoStore.checkKeyFromMemory()
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav {
  background: #FFFFFF;
  border-bottom: 1px solid #E8E8EC;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.nav-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-title {
  font-family: 'General Sans', 'DM Sans', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #0A0A0A;
  letter-spacing: -0.03em;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #6B6B6B;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.lock-link {
  border: 1px solid #E8E8EC;
  background: #FFFFFF;
  font-family: inherit;
  cursor: pointer;
  color: #4B5563;
}

.lock-link:hover {
  color: #EF4444;
  background: #FEF2F2;
  border-color: #FECACA;
  transform: translateY(-1px);
}

.nav-link:hover:not(.lock-link) {
  color: #0A0A0A;
  background: #F5F5F5;
}

.nav-link.active {
  color: #6366F1;
  background: rgba(99, 102, 241, 0.1);
  font-weight: 600;
}

.main-content {
  flex: 1;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 24px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .nav-container {
    padding: 0 16px;
  }
  
  .main-content {
    padding: 24px 16px;
  }
}
</style>