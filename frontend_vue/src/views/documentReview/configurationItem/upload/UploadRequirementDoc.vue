<template>
  <div class="step-content">
    <FileUpload 
      :uploadUrl="uploadUrl"
      :fileTypes="['doc', 'docx']"
      @upload-success="$emit('upload-success', $event)"
      @upload-error="$emit('upload-error', $event)"
    />
    <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
  </div>
</template>
<script setup>
import FileUpload from '@/components/upload/FileUpload.vue';
import { defineProps } from 'vue';
const props = defineProps({
  uploadUrl: String,
  uploadError: String
});
</script>
<style scoped>
.step-title { font-size: 1.3em; font-weight: 500; margin-bottom: 20px; color: #2c3e50; }
.error-message { color: #F56C6C; margin-top: 15px; font-size: 0.9em; padding: 8px; background-color: #fef0f0; border: 1px solid #fde2e2; border-radius: 4px; }
</style>
