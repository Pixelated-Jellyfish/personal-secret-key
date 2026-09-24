import { createRouter, createWebHistory } from 'vue-router'
import { useCryptoStore } from '@/stores/crypto'

const routes = [
  {
    path: '/',
    name: 'passphrase',
    component: () => import('@/views/PassphraseView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/notes',
    name: 'notes',
    component: () => import('@/views/NotesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/new',
    name: 'note-new',
    component: () => import('@/views/NoteEditorView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/notes/:id',
    name: 'note-edit',
    component: () => import('@/views/NoteEditorView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/aes-lab',
    name: 'aes-lab',
    component: () => import('@/views/AesLabView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const cryptoStore = useCryptoStore()
  
  if (to.meta.requiresAuth && !cryptoStore.hasKey) {
    next({ name: 'passphrase' })
  } else if (to.name === 'passphrase' && cryptoStore.hasKey) {
    next({ name: 'notes' })
  } else {
    next()
  }
})

export default router