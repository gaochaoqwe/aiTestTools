<template>
  <div class="document-review-base">
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
      
      <!-- 第三步：选择需求候选项 -->
      <RequirementCandidates 
        v-if="candidatesSectionVisible" 
        :candidates="requirementCandidates"
        :sessionId="currentSessionId"
        :fileId="documentFileId"
        :fileName="documentFileName"
        :catalogFileId="catalogFileId"
        :catalogFileName="catalogFileName"
        :apiService="props.apiService"
        @extract-complete="handleExtractComplete"
        :key="'candidates-' + requirementCandidates.length" 
      />
      
      <!-- 第四步：查看和导出需求 -->
      <ExtractedRequirements 
        v-if="requirementsSectionVisible" 
        :requirements="extractedRequirements"
        :sessionId="currentSessionId"
        :apiService="props.apiService" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import FileUpload from './FileUpload.vue';
import CatalogUpload from './CatalogUpload.vue';
import RequirementCandidates from './RequirementCandidates.vue';
import ExtractedRequirements from './ExtractedRequirements.vue';

// 接收API服务作为props
const props = defineProps({
  apiService: {
    type: Object,
    required: true
  }
});

// 向父组件发出事件
const emit = defineEmits(['step-changed']);

// 文件状态
const currentFileId = ref('');
const currentFileName = ref('');
const currentFileExt = ref('');  // 保存文件扩展名

// 文档文件和目录文件状态
const documentFileId = ref('');
const documentFileName = ref('document.docx');
const catalogFileId = ref('');
const catalogFileName = ref('docx');

// 需求处理状态
const requirementCandidates = ref([]);
const extractedRequirements = ref([]);
const currentSessionId = ref('');

// 页面区域可见性
const uploadSectionVisible = ref(true);
const extractSectionVisible = ref(false);
const candidatesSectionVisible = ref(false);
const requirementsSectionVisible = ref(false);

// 处理文件上传成功事件
function handleFileUploadSuccess(data) {
  currentFileId.value = data.fileId;
  currentFileName.value = data.fileName;
  currentFileExt.value = data.fileExt || '.docx';
  console.log(`文件上传成功, ID: ${data.fileId}, 扩展名: ${data.fileExt}`);
  
  extractSectionVisible.value = true;
  emit('step-changed', 'extract');
}

// 处理需求候选项提取成功事件
function handleExtractSuccess(data) {
  console.log('配置项测试: 接收到需求候选项数据:', data);
  
  // 将需求列表清空
  requirementCandidates.value = [];
  
  // 先检查API直接返回的requirements字段
  if (data.requirements && Array.isArray(data.requirements)) {
    console.log('API返回了requirements字段，包含', data.requirements.length, '项');
    // 循环压入每一项
    for (const req of data.requirements) {
      // 确保level字段存在
      if (req.level === undefined && req.chapter) {
        req.level = req.chapter.split('.').length;
      }
      requirementCandidates.value.push(req);
    }
  } 
  // 如果数据在data.candidates中
  else if (data.candidates && Array.isArray(data.candidates)) {
    console.log('API返回了candidates字段，包含', data.candidates.length, '项');
    for (const req of data.candidates) {
      if (req.level === undefined && req.chapter) {
        req.level = req.chapter.split('.').length;
      }
      requirementCandidates.value.push(req);
    }
  }
  
  console.log('需求候选项列表更新完成，共', requirementCandidates.value.length, '项');
  console.log('更新后的数据:', requirementCandidates.value);
  
  // 保存会话ID
  if (data.session_id) {
    currentSessionId.value = data.session_id;
    console.log('设置会话ID:', data.session_id);
  }
  
  // 使用当前文件ID来设置文档文件ID
  documentFileId.value = currentFileId.value;
  documentFileName.value = currentFileName.value || 'document.docx';
  
  // 保存目录文件ID和文件名
  if (data.catalog_file_id) {
    catalogFileId.value = data.catalog_file_id;
    console.log(`设置目录文件ID: ${data.catalog_file_id}`);
  } else if (data.catalogFileId) {
    catalogFileId.value = data.catalogFileId;
    console.log(`设置目录文件ID: ${data.catalogFileId}`);
  }
  
  if (data.catalogFileName) {
    catalogFileName.value = data.catalogFileName;
  } else {
    catalogFileName.value = 'docx';
  }
  
  candidatesSectionVisible.value = true;
  emit('step-changed', 'candidates');
}

// 处理需求详情提取完成事件
function handleExtractComplete(data) {
  console.log('文档审查基础组件收到提取完成事件:', data);
  extractedRequirements.value = data.extractedRequirements;
  requirementsSectionVisible.value = true;
  emit('step-changed', 'requirements');
}
</script>

<style scoped>
.document-review-base {
  width: 100%;
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
