<template>
  <div 
    class="status-message" 
    v-if="visible" 
    :class="{ 
      'status-success': type === 'success',
      'status-error': type === 'error',
      'status-info': type === 'info'
    }"
  >
    {{ message }}
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'info'].includes(value)
  }
})
</script>

<style scoped>
.status-message {
  padding: 10px;
  margin-top: 15px;
  border-radius: 5px;
  text-align: left;
}

.status-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}
</style>
