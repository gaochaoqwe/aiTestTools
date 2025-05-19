<template>
  <div class="step-content">
    <RequirementReview
      :requirements="extractionResults"
      :sessionId="currentSessionId"
      :apiService="apiService"
      @review-completed="$emit('review-completed', $event)"
    />
  </div>
</template>
<script setup>
import RequirementReview from './RequirementReview.vue';
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
