<template>
  <section class="catalog-section">
    <h2>第二步：AI提取需求</h2>
    <div class="extract-description">
      <p>
        <span class="info-icon">ℹ</span>
        AI将分析你上传的规格说明文档，自动提取并生成结构化的需求列表，点击下方按钮开始提取。
      </p>
      <div class="extract-btn-area">
        <button class="btn primary-btn" :disabled="extracting || !props.documentFileId" @click="extractRequirements">
          <span class="btn-icon">🔍</span>
          {{ extracting ? '正在AI提取需求...' : '开始AI提取需求' }}
        </button>
        <StatusMessage 
          :visible="statusVisible" 
          :message="statusMsg" 
          :type="statusType || 'info'" 
        />
      </div>
      <div v-if="requirements.length > 0" class="requirements-list">
        <h3 style="margin-top:24px;">提取结果</h3>
        <ul>
          <li v-for="(req, idx) in requirements" :key="idx">
            <strong v-if="req.chapter">[{{ req.chapter }}]</strong> {{ req.content }}
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import StatusMessage from './StatusMessage.vue';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5002/api';

const props = defineProps({
  documentFileId: {
    type: String,
    required: true
  },
  documentFileExt: {
    type: String,
    default: '.docx'
  },
  documentFileName: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['extract-success']);

const extracting = ref(false);
const statusMsg = ref('');
const statusType = ref('info');
const statusVisible = ref(false);

// 新增：用于本地显示提取结果
const requirements = ref([]);

// 显示状态消息
function showStatus(message, type = 'info') {
  statusMsg.value = message;
  statusType.value = type;
  statusVisible.value = true;
}

// 提取需求
async function extractRequirements() {
  // 检查文档是否已上传
  if (!props.documentFileId) {
    showStatus('请先上传需求文档', 'error');
    return;
  }
  
  extracting.value = true;
  showStatus('正在提取需求...', 'info');
  
  try {
    // 构造请求数据
    const requestData = {
      file_id: props.documentFileId,
      file_name: props.documentFileName, // Send the original filename received from upload
      use_ai_catalog: true // 直接使用AI提取模式
    };
    
    console.log('发送AI提取请求:', requestData);
    
    // 直接使用ai_extract接口
    const response = await axios.post(`${API_BASE_URL}/ai_extract`, requestData, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: false
    });
    
    // 解析响应
    const data = response.data;
    console.log('AI提取需求响应:', data);
    
    // 获取提取的需求
    const extracted = data.requirements || [];
    requirements.value = extracted; // 保存到本地用于页面展示
    
    if (extracted.length === 0) {
      showStatus('未找到需求，请检查文档格式', 'warning');
      extracting.value = false;
      return;
    }
    
    // 显示需求数量
    showStatus(`成功提取到 ${extracted.length} 个需求`, 'success');
    
    // 发送给父组件
    emit('extract-success', {
      extractedRequirements: extracted,
      sessionId: data.session_id || '',
      file_id: props.documentFileId,
      file_name: props.documentFileName
    });
    
    console.log('需求提取成功，共 ' + extracted.length + ' 个需求项');
    
  } catch (error) {
    console.error('提取需求时发生错误:', error);
    let errorMessage = '需求提取失败';
    
    if (error.response) {
      console.error('服务器错误:', error.response.data);
      errorMessage = error.response.data.error || `服务器错误 (${error.response.status})`;
    } else if (error.request) {
      console.error('没有收到响应:', error.request);
      errorMessage = '服务器没有响应，请检查网络连接';
    } else {
      console.error('请求错误:', error.message);
      errorMessage = `请求错误: ${error.message}`;
    }
    
    showStatus('错误: ' + errorMessage, 'error');
  } finally {
    extracting.value = false;
  }
}
</script>

<style scoped>
.catalog-section {
  margin-bottom: 30px;
  padding: 25px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.extract-description {
  margin-bottom: 20px;
}

.extract-description p {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
  display: flex;
  align-items: center;
}

.info-icon {
  margin-right: 10px;
  font-size: 1.2rem;
  color: #3498db;
}

.extract-btn-area {
  margin-top: 20px;
}

.btn {
  padding: 12px 25px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary-btn {
  background-color: #2ecc71;
  color: white;
}

.primary-btn:hover:not(:disabled) {
  background-color: #27ae60;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(46, 204, 113, 0.2);
}

.btn-icon {
  margin-right: 8px;
}
</style>
