<template>
  <div class="hex-matrix" :class="{ compact: compact }">
    <div class="matrix-row" v-for="(row, r) in displayMatrix" :key="r">
      <div 
        class="matrix-cell" 
        v-for="(cell, c) in row" 
        :key="c"
        :class="{
          changed: isChanged(r, c),
          'fade-in': fadeIn && isOutputCell(r, c)
        }"
        :style="cellStyle(r, c)"
      >
        {{ cell }}
      </div>
    </div>
    <div class="matrix-legend" v-if="!compact">
      <span>Baris: 0 1 2 3 (top to bottom)</span>
      <span>Kolom: 0 1 2 3 (left to right)</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  matrix: {
    type: Array,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  },
  prevMatrix: {
    type: Array,
    default: () => []
  },
  changedCells: {
    type: Array,
    default: () => []
  },
  fadeIn: {
    type: Boolean,
    default: false
  }
})

const displayMatrix = computed(() => {
  if (!props.matrix || props.matrix.length !== 4) return []
  return props.matrix.map(row => row.slice(0, 4))
})

const changedSet = computed(() => {
  const set = new Set()
  for (const { row, col } of props.changedCells) {
    set.add(`${row},${col}`)
  }
  return set
})

function isChanged(r, c) {
  return changedSet.value.has(`${r},${c}`)
}

function isOutputCell(r, c) {
  return props.fadeIn && props.matrix.length === 4
}

function cellStyle(r, c) {
  if (props.fadeIn && props.matrix.length === 4) {
    const delay = (r * 4 + c) * 30
    return { animationDelay: `${delay}ms` }
  }
  return {}
}
</script>

<style scoped>
.hex-matrix {
  display: inline-flex;
  flex-direction: column;
  gap: 2px;
  font-family: 'JetBrains Mono', monospace;
  background: #FAFAFA;
  border: 1px solid #E8E8EC;
  border-radius: 6px;
  padding: 8px;
}

.compact {
  padding: 6px;
}

.matrix-row {
  display: flex;
  gap: 2px;
}

.matrix-cell {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: #FFFFFF;
  border: 1px solid #E8E8EC;
  border-radius: 4px;
  color: #0A0A0A;
  text-transform: lowercase;
}

.compact .matrix-cell {
  width: 24px;
  height: 24px;
  font-size: 10px;
}

.matrix-legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #E8E8EC;
  font-size: 10px;
  color: #9C9C9C;
}
</style>