<template>
  <div class="configuration-item-test">
    <DocumentReviewBase :apiService="configurationItemService" @step-changed="handleStepChanged" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import DocumentReviewBase from '../components/DocumentReviewBase.vue';
import { configurationItemService } from '../services/configurationItemService';

// 跟踪当前步骤
const currentStep = ref('upload');

function handleStepChanged(step) {
  currentStep.value = step;
  console.log(`配置项测试：当前步骤变更为: ${step}`);
}
</script>

<style scoped>
.configuration-item-test {
  width: 100%;
}
</style>
