<template>
  <section class="catalog-section">
    <h2>第二步：选择目录方式</h2>
    
    <div class="option-selector">
      <div class="option" :class="{ active: catalogMethod === 'ai' }" @click="selectMethod('ai')">
        <h3><i class="icon">🤖</i> 使用AI自动提取目录</h3>
        <p>算法将自动分析文档结构，提取需求目录，无需手动上传目录文件</p>
      </div>
      
      <div class="option" :class="{ active: catalogMethod === 'upload' }" @click="selectMethod('upload')">
        <h3><i class="icon">📁</i> 手动上传目录文件</h3>
        <p>上传标准格式的目录文件，目录应包含章节号、需求名称和页码</p>
      </div>
    </div>
    
    <!-- 传统目录上传模式 -->
    <div v-if="catalogMethod === 'upload'" class="catalog-upload-container">
      <p><strong>注意：</strong>目录文件必须是.docx格式，且包含章节号、需求名称和页码</p>
      <div class="catalog-file-controls">
        <button class="file-input-label" @click="clickCatalogFileInput">选择目录文件</button>
        <input 
          type="file" 
          id="catalogFileInput" 
          accept=".doc,.docx" 
          style="display: none;" 
          @change="handleCatalogFileSelect"
        >
      </div>
      <div class="catalog-file-info" v-if="catalogFileInfoVisible">
        <p>已选择目录文件: <span>{{ catalogFileName }}</span></p>
        <button class="btn secondary-btn" @click="uploadCatalogFile">上传目录文件</button>
      </div>
      <StatusMessage 
        :visible="statusVisible" 
        :message="statusMsg" 
        :type="statusType || 'info'" 
      />
    </div>
    
    <!-- AI目录提取模式 -->
    <div v-if="catalogMethod === 'ai'" class="ai-catalog-container">
      <p class="ai-catalog-info">
        <i class="info-icon">ℹ️</i>
        下一步中，AI将自动分析文档并提取目录。您可以直接点击“提取需求”按钮继续。
      </p>
    </div>
    <div class="debug-info">
      <p>目录文件ID: {{ catalogFileId || '未设置' }} (类型: {{ typeof catalogFileId }})</p>
      <p>hasCatalogFile状态: {{ hasCatalogFile ? '是' : '否' }}</p>
      <p>hasValidCatalogFile计算值: {{ hasValidCatalogFile ? '是' : '否' }}</p>
      <p>目录文件扩展名: {{ catalogFileExt || '未设置' }}</p>
    </div>
    <!-- AI模式下显示AI目录提取按钮 -->
    <button
      v-if="catalogMethod === 'ai'"
      class="btn secondary-btn"
      :disabled="aiExtracting"
      @click="extractCatalogWithAI"
      style="margin-bottom: 12px;"
    >
      {{ aiExtracting ? 'AI正在提取目录...' : 'AI目录提取' }}
    </button>

    <!-- "提取需求"按钮在AI模式下，仅AI目录提取成功后可用；上传模式下上传成功后可用 -->
    <button
      id="extract-button"
      class="btn primary-btn"
      :disabled="catalogMethod === 'ai' ? !aiExtracted : !hasValidCatalogFile"
      @click="extractRequirements"
    >
      提取需求
    </button>
    <StatusMessage 
      :visible="extractStatusVisible" 
      :message="extractStatusMsg" 
      :type="extractStatusType || 'info'" 
    />

    <!-- 新增：AI目录提取结果表格 -->
    <div v-if="catalogMethod === 'ai' && aiCatalog.length > 0" class="ai-catalog-table">
      <h3>AI提取目录结果：</h3>
      <table>
        <thead>
          <tr>
            <th>章节号</th>
            <th>需求名称</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in aiCatalog" :key="item.chapter + item.name">
            <td>{{ item.chapter }}</td>
            <td>{{ item.name }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import StatusMessage from './StatusMessage.vue';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5002/api';

// 新增：AI提取的目录结果
const aiCatalog = ref([]);

const props = defineProps({
  documentFileId: {
    type: String,
    required: true
  },
  documentFileExt: {  // 新增：接收主文档文件扩展名
    type: String,
    default: '.docx'
  }
});

const emit = defineEmits(['extract-success']);

// 目录提取方式
const catalogMethod = ref('ai'); // 默认使用AI自动提取

// 目录文件状态
const catalogFile = ref(null);
const catalogFileName = ref('');
const catalogFileId = ref('');
const catalogFileExt = ref('');  // 新增：保存目录文件扩展名
const catalogFileInfoVisible = ref(false);
const statusMsg = ref('');
const statusType = ref('');
const statusVisible = ref(false);

// 简单状态变量
let hasCatalogFile = false;

// 提取状态
const extractStatusMsg = ref('');
const extractStatusType = ref('');
const extractStatusVisible = ref(false);

// 计算属性：是否有有效的目录方式
const hasValidCatalogFile = computed(() => {
  // 如果选择了AI提取目录，始终返回true
  // 如果选择了手动上传，则需要检查是否真的上传了文件
  return catalogMethod.value === 'ai' || !!catalogFileId.value || hasCatalogFile;
});

// 选择目录获取方式
function selectMethod(method) {
  catalogMethod.value = method;
  console.log(`切换目录方式为: ${method}`);
  
  // 根据选择的方式启用或禁用提取按钮
  setTimeout(() => {
    const button = document.getElementById('extract-button');
    if (button) {
      if (method === 'ai' || hasValidCatalogFile.value) {
        button.disabled = false;
        button.classList.remove('disabled-btn');
      } else {
        button.disabled = true;
        button.classList.add('disabled-btn');
      }
    }
  }, 100);
}

// AI目录提取状态
const aiExtracting = ref(false); // 正在提取
const aiExtracted = ref(false);  // 提取成功

// AI目录提取逻辑
async function extractCatalogWithAI() {
  if (!props.documentFileId) {
    showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '请先上传需求文档', 'error');
    return;
  }
  aiExtracting.value = true;
  aiExtracted.value = false;
  showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, 'AI正在提取目录，请稍候...', 'info');
  try {
    // 构造请求参数
    const requestData = {
      file_id: props.documentFileId,
      file_name: 'document' + props.documentFileExt,
      requirement_level: 3 // 可根据需要提供选择
    };
    // 实际API调用
    const response = await axios.post(`${API_BASE_URL}/catalog/extract`, requestData, {
      headers: { 'Content-Type': 'application/json' },
      withCredentials: false
    });
    const data = response.data;
    console.log('【DEBUG】AI目录接口原始响应:', data);
    // 兼容无success字段的情况，优先判断requirements，没有则兼容catalog
    const requirements = data.requirements || data.catalog || [];
    console.log('【DEBUG】AI目录接口 requirements/catalog 字段:', requirements);
    if (requirements.length > 0) {
      aiCatalog.value = requirements;
      aiExtracted.value = true;
      showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, 'AI目录提取成功，可继续提取需求', 'success');
      console.log('【DEBUG】已写入aiCatalog:', aiCatalog.value);
    } else {
      aiExtracted.value = false;
      showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, 'AI目录提取失败: 未提取到有效目录', 'error');
      console.log('【DEBUG】AI目录提取失败，无有效requirements字段:', data);
    }
  } catch (e) {
    aiExtracted.value = false;
    let msg = e && e.response && e.response.data && e.response.data.error ? e.response.data.error : (e.message || 'AI目录提取失败');
    showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, 'AI目录提取失败: ' + msg, 'error');
  } finally {
    aiExtracting.value = false;
  }
}


// 监听目录文件上传（上传模式），自动设置hasCatalogFile
watch(catalogFileId, (newValue) => {
  hasCatalogFile = !!newValue;
});

// 点击目录文件输入按钮
function clickCatalogFileInput() {
  document.getElementById('catalogFileInput').click();
}

// 处理目录文件选择
function handleCatalogFileSelect(e) {
  if (e.target.files.length > 0) {
    catalogFile.value = e.target.files[0];
    catalogFileName.value = e.target.files[0].name;
    catalogFileInfoVisible.value = true;
  }
}

// 显示状态消息
function showStatus(msgRef, typeRef, visibleRef, message, type) {
  msgRef.value = message;
  const validTypes = ['success', 'error', 'info'];
  typeRef.value = validTypes.includes(type) ? type : 'info';
  visibleRef.value = true;
}

// 上传目录文件
async function uploadCatalogFile() {
  if (!catalogFile.value) {
    showStatus(statusMsg, statusType, statusVisible, '请先选择目录文件', 'error');
    return;
  }
  
  const formData = new FormData();
  formData.append('file', catalogFile.value);
  
  showStatus(statusMsg, statusType, statusVisible, '正在上传目录文件...', 'info');
  
  try {
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      withCredentials: false // 不发送cookies，避免CORS预检请求问题
    });
    
    const data = response.data;
    console.log('目录文件上传成功，响应数据:', data);
    
    // 明确地将响应数据设置为字符串类型
    catalogFileId.value = String(data.file_id || '');
    catalogFileName.value = String(data.file_name || '');
    catalogFileExt.value = String(data.ext || '.docx');  // 新增：保存文件扩展名
    hasCatalogFile = true;
    
    console.log(`catalogFileId设置为: ${catalogFileId.value}`);
    console.log(`catalogFileName设置为: ${catalogFileName.value}`);
    console.log(`catalogFileExt设置为: ${catalogFileExt.value}`);
    console.log(`hasCatalogFile设置为: ${hasCatalogFile}`);
    
    showStatus(statusMsg, statusType, statusVisible, '目录文件上传成功', 'success');
    
    // 直接操作DOM启用按钮
    setTimeout(() => {
      const button = document.getElementById('extract-button');
      if (button) {
        button.disabled = false;
        button.classList.remove('disabled-btn');
        console.log('目录文件上传成功，手动启用按钮');
      }
    }, 100);
  } catch (error) {
    console.error('上传出错: ', error);
    let errorMessage = '文件上传失败';
    
    if (error.response) {
      // 服务器返回了错误响应
      console.error('服务器错误:', error.response.data);
      errorMessage = error.response.data.error || `服务器错误 (${error.response.status})`;
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('没有收到响应:', error.request);
      errorMessage = '服务器没有响应，请检查网络连接';
    } else {
      // 设置请求时发生错误
      console.error('请求错误:', error.message);
      errorMessage = `请求错误: ${error.message}`;
    }
    
    showStatus(statusMsg, statusType, statusVisible, '错误: ' + errorMessage, 'error');
  }
}

// 提取需求
async function extractRequirements() {
  // 检查文档是否已上传
  if (!props.documentFileId) {
    showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '请先上传需求文档', 'error');
    return;
  }
  
  // 检查目录方式是否有效
  if (!hasValidCatalogFile.value) {
    if (catalogMethod.value === 'upload') {
      showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '请先上传目录文件', 'error');
    } else {
      showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '无法使用AI提取目录', 'error');
    }
    return;
  }
  
  showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '正在提取需求候选项...', 'info');
  
  try {
    // 构造请求数据
    const requestData = {
      file_id: props.documentFileId,
      file_name: 'document' + props.documentFileExt
    };
    
    // 根据所选方式添加相应参数
    if (catalogMethod.value === 'upload') {
      // 手动上传模式
      requestData.catalog_file_id = catalogFileId.value;
      requestData.catalog_file_name = catalogFileName.value || 'catalog.docx';
    } else {
      // AI自动提取模式
      requestData.use_ai_catalog = true;
    }
    
    console.log('发送请求数据:', requestData);
    
    // 发送请求
    const response = await axios.post(`${API_BASE_URL}/requirement_candidates`, requestData, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: false // 不发送cookies，避免CORS预检请求问题
    });
    
    // 解析成功响应
    const data = response.data;
    console.log('【DEBUG】AI目录接口原始响应:', data);
    console.log('【DEBUG】AI目录接口 requirements 字段:', data.requirements);
    
    // 获取需求列表，同时适配不同的API响应格式
    const requirements = data.requirements || [];
    console.log('【DEBUG】requirements 变量:', requirements);
    
    if (requirements.length === 0) {
      showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '未找到需求候选项，请检查文档格式', 'warning');
      return;
    }
    
    // 显示需求数量
    showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, `成功提取到 ${requirements.length} 个需求候选项`, 'success');
    
    // 给每个需求添加必要的字段（如果缺失）
    const formattedRequirements = requirements.map(req => {
      // 检查并补充level字段
      if (req.level === undefined && req.chapter) {
        req.level = req.chapter.split('.').length;
      }
      return req;
    });
    
    // 新增：保存AI目录到本地变量
    aiCatalog.value = formattedRequirements;
    
    console.log('【DEBUG】格式化后的需求列表 formattedRequirements:', formattedRequirements);
    
    // 直接将原始 API 响应传给父组件
    console.log('直接传递API原始响应给父组件:', data);
    
    // 类型安全检查
    const safeData = data || {};
    
    // 发送原始数据和额外的文件信息
    emit('extract-success', {
      ...safeData,  // 包含all原始字段
      file_id: props.documentFileId,
      file_name: 'document' + props.documentFileExt,
      catalog_file_id: catalogMethod.value === 'upload' ? catalogFileId.value : '',
      catalog_file_name: catalogMethod.value === 'upload' ? (catalogFileName.value || 'catalog.docx') : '',
      use_ai_catalog: catalogMethod.value === 'ai'
    });
    
    console.log('已发送提取成功事件，包含 ' + formattedRequirements.length + ' 个需求项');
    
  } catch (error) {
    console.error('提取需求时发生错误:', error);
    let errorMessage = '需求提取失败';
    
    if (error.response) {
      // 服务器返回了错误响应
      console.error('服务器错误:', error.response.data);
      errorMessage = error.response.data.error || `服务器错误 (${error.response.status})`;
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('没有收到响应:', error.request);
      errorMessage = '服务器没有响应，请检查网络连接';
    } else {
      // 设置请求时发生错误
      console.error('请求错误:', error.message);
      errorMessage = `请求错误: ${error.message}`;
    }
    
    showStatus(extractStatusMsg, extractStatusType, extractStatusVisible, '错误: ' + errorMessage, 'error');
  }
}
</script>

<style scoped>
.catalog-section {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.catalog-upload-container {
  border: 2px dashed #bdc3c7;
  padding: 20px;
  border-radius: 5px;
  margin-bottom: 20px;
}

.catalog-file-controls {
  margin: 15px 0;
}

.file-input-label {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  cursor: pointer;
  border: none;
  border-radius: 5px;
  font-size: 16px;
}

.catalog-file-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f8ff;
  border-radius: 5px;
}

.catalog-file-info p {
  margin: 5px 0;
}

.catalog-file-info span {
  font-weight: bold;
}

.debug-info {
  margin: 10px 0;
  font-size: 14px;
  color: #666;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 10px;
}

.primary-btn {
  background-color: #3498db;
  color: white;
}

.primary-btn:hover {
  background-color: #2980b9;
}

.secondary-btn {
  background-color: #2ecc71;
  color: white;
}

.secondary-btn:hover {
  background-color: #27ae60;
}

.btn:disabled,
.disabled-btn {
  background-color: #cccccc !important;
  cursor: not-allowed;
  opacity: 0.7;
}

/* 新增：AI目录表格样式 */
.ai-catalog-table {
  margin-top: 20px;
}
.ai-catalog-table table {
  width: 100%;
  border-collapse: collapse;
}
.ai-catalog-table th, .ai-catalog-table td {
  border: 1px solid #ddd;
  padding: 8px;
}
.ai-catalog-table th {
  background: #f6f6f6;
}
</style>
