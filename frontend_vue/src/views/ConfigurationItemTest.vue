<template>
  <div class="configuration-item-test">
    <el-tabs v-model="activeTab" class="main-tabs">
      <el-tab-pane label="配置项测试" name="configTest">
        <div class="content-wrapper">
          <el-steps :active="activeStep" finish-status="success" simple class="custom-steps">
            <el-step title="上传需求规格文档"></el-step>
            <el-step title="AI提取需求"></el-step>
            <el-step title="查看和导出需求"></el-step>
          </el-steps>

          <div v-if="activeStep === 0" class="step-content">
            <h3 class="step-title">第一步: 上传需求规格文档</h3>
            <FileUpload 
              :uploadUrl="uploadUrl"
              :fileTypes="['doc', 'docx']"
              @upload-success="handleUploadSuccess"
              @upload-error="handleUploadError"
            />
            <div v-if="uploadError" class="error-message">{{ uploadError }}</div>
          </div>

          <div v-if="activeStep === 1" class="step-content">
            <h3 class="step-title">第二步: AI提取需求</h3>
            <CatalogUpload 
              :documentFileId="documentFileId"
              :documentFileExt="documentFileExt"
              :documentFileName="uploadedDocumentName" 
              @extraction-complete="handleExtractionComplete"
              @extraction-error="handleExtractionError"
            />
            <div v-if="extractionError" class="error-message">{{ extractionError }}</div>
          </div>

          <!-- Third step for viewing/exporting results -->
          <div v-if="activeStep === 2" class="step-content">
  <h3 class="step-title">第三步: 查看和导出需求</h3>
  <!-- Placeholder for results display and export functionality -->
  <p v-if="extractionResults.length > 0">提取到 {{ extractionResults.length }} 条需求。</p>
  <p v-else>未提取到需求或提取尚未完成。</p>
  <!-- You would typically display results here and provide download options -->
  <el-button @click="activeStep = 0">重新开始</el-button>
</div>

        </div>
      </el-tab-pane>
      <!-- Add other tabs if needed -->
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import FileUpload from '@/components/FileUpload.vue';
import CatalogUpload from '@/components/CatalogUpload.vue';
// Import other necessary components or utilities, e.g., for displaying results

const activeTab = ref('configTest');
const activeStep = ref(0); // 0: Upload, 1: Extract, 2: View/Export

const documentFileId = ref(null);
const documentFileExt = ref('');
const uploadedDocumentName = ref(''); // To store the original filename from upload
const uploadError = ref('');

const extractionResults = ref([]); // To store results from CatalogUpload
const extractionError = ref('');
const currentSessionId = ref('');

const uploadUrl = computed(() => `${import.meta.env.VITE_API_BASE_URL}/api/upload`);

const handleUploadSuccess = (response) => {
  console.log('配置项测试 - 文件上传成功:', response);
  if (response && response.file_id && response.file_name) {
    documentFileId.value = response.file_id;
    uploadedDocumentName.value = response.file_name; // Store the full original filename
    
    // Extract extension for documentFileExt
    const nameParts = response.file_name.split('.');
    if (nameParts.length > 1) {
      documentFileExt.value = '.' + nameParts[nameParts.length - 1];
    } else {
      documentFileExt.value = ''; // Or handle as no extension
    }
    
    uploadError.value = '';
    activeStep.value = 1; // Move to AI extraction step
  } else {
    console.error('配置项测试 - 文件上传响应格式不正确:', response);
    uploadError.value = '文件上传成功，但响应数据格式不正确。';
    documentFileId.value = null;
    uploadedDocumentName.value = '';
    documentFileExt.value = '';
  }
};

const handleUploadError = (error) => {
  console.error('配置项测试 - 文件上传失败:', error);
  uploadError.value = (error && error.message) ? error.message : '文件上传失败，请重试。';
  documentFileId.value = null;
  uploadedDocumentName.value = '';
  documentFileExt.value = '';
};

const handleExtractionComplete = (data) => {
  console.log('配置项测试 - 需求提取完成:', data);
  if (data && data.requirements) {
    extractionResults.value = data.requirements;
    currentSessionId.value = data.session_id;
    extractionError.value = '';
    activeStep.value = 2; // Move to view/export results step
  } else {
    console.error('配置项测试 - 提取响应格式不正确:', data);
    extractionError.value = '需求提取成功，但响应数据格式不正确。';
    extractionResults.value = [];
  }
};

const handleExtractionError = (error) => {
  console.error('配置项测试 - 需求提取失败:', error);
  extractionError.value = (error && error.message) ? error.message : '需求提取过程中发生错误。';
  extractionResults.value = [];
};

</script>

<style scoped>
.configuration-item-test {
  padding: 20px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
.main-tabs {
  margin-bottom: 20px;
}
.content-wrapper {
  background-color: #fff;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}
.custom-steps {
  margin-bottom: 30px;
}
.step-content {
  margin-top: 25px;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 6px;
}
.step-title {
  font-size: 1.3em;
  font-weight: 500;
  margin-bottom: 20px;
  color: #2c3e50;
}
.error-message {
  color: #F56C6C;
  margin-top: 15px;
  font-size: 0.9em;
  padding: 8px;
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 4px;
}
</style>
