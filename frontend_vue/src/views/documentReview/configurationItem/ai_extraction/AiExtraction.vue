<template>
  <div class="step-content">
    <div class="ai-extract-panel">
  <h4>AI智能提取需求</h4>
  <el-button type="primary" @click="handleAIExtract" :loading="extracting">
    <span v-if="!extracting">开始AI提取</span>
    <span v-else>正在提取...</span>
  </el-button>
</div>
    <div v-if="extractionError" class="error-message">{{ extractionError }}</div>
    
    <!-- 调试信息 -->
    <div style="margin-top: 20px; border: 1px solid #ccc; padding: 10px; background: #f9f9f9;">
      <h4>调试信息</h4>
      <p>提取结果数量: {{ localResults.length }}</p>
      <p>提取结果类型: {{ typeof localResults }}</p>
      <p>是否数组: {{ Array.isArray(localResults) }}</p>
      <p>原始 props 类型: {{ typeof props.extractionResults }}</p>
      <p>原始 props 是否数组: {{ Array.isArray(props.extractionResults) }}</p>
    </div>
    
    <!-- 固定显示的按钮 -->
    <el-button
      type="primary"
      @click="emit('next-step')"
      style="margin-top: 16px;"
    >
      下一步：AI文档审查 (固定显示)
    </el-button>
  </div>
</template>
<script setup>

import { defineProps, defineEmits, ref } from 'vue';

console.log('CHILD AiExtraction: Setup script executing');

// 定义可以发出的事件
const emit = defineEmits(['extraction-complete', 'extraction-error', 'next-step']);

// 本地存储提取结果
const localResults = ref([]);

const props = defineProps({
  documentFileId: [String, Number],
  documentFileExt: String,
  uploadedDocumentName: String,
  extractionError: String,
  extractionResults: {
    type: Array,
    default: () => []
  }
});

// AI提取需求逻辑
const extracting = ref(false);

import axios from 'axios';

const handleAIExtract = async () => {
  extracting.value = true;
  try {
    // 根据记忆，实际可用接口为 /api/requirement_candidates
    const response = await axios.post(
      import.meta.env.VITE_API_BASE_URL + '/api/requirement_candidates',
      {
        file_id: props.documentFileId,
        file_name: props.uploadedDocumentName,
        // model: 可选参数
      }
    );
    if (response.data && response.data.requirements) {
      localResults.value = response.data.requirements;
      emit('extraction-complete', { requirements: response.data.requirements, session_id: response.data.session_id });
    } else {
      emit('extraction-error', 'AI提取失败：后端未返回requirements');
    }
  } catch (e) {
    emit('extraction-error', 'AI提取失败: ' + (e?.message || '未知错误'));
  } finally {
    extracting.value = false;
  }
};
</script>
<style scoped>
.step-title { font-size: 1.3em; font-weight: 500; margin-bottom: 20px; color: #2c3e50; }
.error-message { color: #F56C6C; margin-top: 15px; font-size: 0.9em; padding: 8px; background-color: #fef0f0; border: 1px solid #fde2e2; border-radius: 4px; }
</style>
