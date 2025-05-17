<template>
  <div v-if="visible" :class="['status-message', type]">
    {{ message }}
  </div>
</template>

<script setup>
const props = defineProps({
  visible: Boolean,
  message: String,
  type: {
    type: String,
    default: 'info' // 可选: 'info', 'success', 'error'
  }
});
</script>

<style scoped>
.status-message {
  padding: 12px 20px;
  border-radius: 6px;
  margin: 16px 0;
  font-size: 1em;
  text-align: center;
}
.status-message.info {
  background: #e3f2fd;
  color: #1976d2;
}
.status-message.success {
  background: #e6fffa;
  color: #38a169;
}
.status-message.error {
  background: #fff5f5;
  color: #e53e3e;
}
</style>
