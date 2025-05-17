<template>
  <div class="step-content">
    <h3 class="step-title">第四步: 导出AI文档审查问题单</h3>
    <ExtractedRequirements
      :requirements="extractionResults"
      :sessionId="currentSessionId"
      :apiService="apiService"
    />
    <el-button @click="$emit('restart')">重新开始</el-button>
  </div>
</template>
<script setup>
import ExtractedRequirements from '@/views/documentReview/configurationItem/downloadDocument/ExtractedRequirements.vue';
import { defineProps } from 'vue';
const props = defineProps({
  extractionResults: Array,
  currentSessionId: String,
  apiService: Object
});
</script>
<style scoped>
.step-title { font-size: 1.3em; font-weight: 500; margin-bottom: 20px; color: #2c3e50; }
</style>
