<template>
  <div class="regression-test">
    <div class="notification">
      <div class="notification-content">
        <h3>回归测试功能</h3>
        <p>回归测试功能正在开发中，目前使用与配置项测试相同的界面但连接不同的API端点。</p>
      </div>
    </div>
    <DocumentReviewBase :apiService="regressionService" @step-changed="handleStepChanged" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import DocumentReviewBase from '../components/DocumentReviewBase.vue';
import { regressionService } from '../services/regressionService';

// 跟踪当前步骤
const currentStep = ref('upload');

function handleStepChanged(step) {
  currentStep.value = step;
  console.log(`回归测试：当前步骤变更为: ${step}`);
}
</script>

<style scoped>
.regression-test {
  width: 100%;
}

.notification {
  background-color: #f8f9fa;
  border-left: 4px solid #4299e1;
  margin-bottom: 20px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.notification-content {
  padding: 15px 20px;
}

.notification h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2b6cb0;
}

.notification p {
  margin: 0;
  color: #4a5568;
}
</style>
