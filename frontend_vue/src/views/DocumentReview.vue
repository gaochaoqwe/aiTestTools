<template>
  <div class="document-review">
    <h2>文档审查</h2>
    <div class="section-container">
      <!-- 步骤导航 -->
      <div class="steps-navigator">
        <div class="step" :class="{ active: uploadSectionVisible, completed: extractSectionVisible || candidatesSectionVisible || requirementsSectionVisible }">
          <div class="step-number">1</div>
          <div class="step-label">上传需求规格文档</div>
        </div>
        <div class="step" :class="{ active: extractSectionVisible, completed: candidatesSectionVisible || requirementsSectionVisible }">
          <div class="step-number">2</div>
          <div class="step-label">上传目录文件(可选)</div>
        </div>
        <div class="step" :class="{ active: candidatesSectionVisible, completed: requirementsSectionVisible }">
          <div class="step-number">3</div>
          <div class="step-label">选择需求候选项</div>
        </div>
        <div class="step" :class="{ active: requirementsSectionVisible }">
          <div class="step-number">4</div>
          <div class="step-label">查看和导出需求</div>
        </div>
      </div>

      <!-- 第一步：文件上传 -->
      <FileUpload 
        v-if="uploadSectionVisible" 
        @upload-success="handleFileUploadSuccess" 
      />
      
      <!-- 第二步：目录文件上传 -->
      <CatalogUpload 
        v-if="extractSectionVisible" 
        :documentFileId="currentFileId"
        :documentFileExt="currentFileExt"
        @extract-success="handleExtractSuccess" 
      />
      
      <!-- 第四步：查看和导出需求 -->
      <ExtractedRequirements 
        v-if="requirementsSectionVisible" 
        :requirements="extractedRequirements"
        :sessionId="currentSessionId" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import FileUpload from '../components/FileUpload.vue';
import CatalogUpload from '../components/CatalogUpload.vue';

import ExtractedRequirements from '../components/ExtractedRequirements.vue';

// 文件状态
const currentFileId = ref('');
const currentFileName = ref('');
const currentFileExt = ref('');  // 保存文件扩展名

// 文档文件和目录文件状态
const documentFileId = ref('');
const documentFileName = ref('document.docx');


// 需求处理状态

const extractedRequirements = ref([]);
const currentSessionId = ref('');

// 页面区域可见性
const uploadSectionVisible = ref(true);
const extractSectionVisible = ref(false);

const requirementsSectionVisible = ref(false);

// 处理文件上传成功事件
function handleFileUploadSuccess(data) {
  currentFileId.value = data.fileId;
  currentFileName.value = data.fileName;
  currentFileExt.value = data.fileExt || '.docx';
  console.log(`文件上传成功, ID: ${data.fileId}, 扩展名: ${data.fileExt}`);
  extractSectionVisible.value = true;
}

// 处理需求提取成功事件
function handleExtractSuccess(data) {
  // 假设 data.extractedRequirements, data.sessionId
  extractedRequirements.value = data.extractedRequirements || [];
  if (data.sessionId) {
    currentSessionId.value = data.sessionId;
  }
  extractSectionVisible.value = false;
  requirementsSectionVisible.value = true;
}

// 处理需求详情提取完成事件
function handleExtractComplete(data) {
  console.log('文档审查视图收到提取完成事件:', data);
  extractedRequirements.value = data.extractedRequirements;
  requirementsSectionVisible.value = true;
}
</script>

<style scoped>
.document-review {
  width: 100%;
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 25px;
  font-size: 1.8rem;
  position: relative;
  padding-bottom: 10px;
}

h2::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 50px;
  height: 3px;
  background-color: #3498db;
  border-radius: 3px;
}

.section-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 30px;
  transition: all 0.3s ease;
}

/* 步骤导航样式 */
.steps-navigator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  position: relative;
}

.steps-navigator::before {
  content: '';
  position: absolute;
  top: 25px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #e0e0e0;
  z-index: 1;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  flex: 1;
  max-width: 150px;
}

.step-number {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #e0e0e0;
  color: #7f8c8d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  margin-bottom: 10px;
  transition: all 0.3s ease;
  position: relative;
  border: 3px solid white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.step-label {
  color: #7f8c8d;
  font-size: 0.9rem;
  text-align: center;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background-color: #3498db;
  color: white;
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

.step.active .step-label {
  color: #2c3e50;
  font-weight: bold;
}

.step.completed .step-number {
  background-color: #2ecc71;
  color: white;
}

.step.completed .step-label {
  color: #2ecc71;
}
</style>
