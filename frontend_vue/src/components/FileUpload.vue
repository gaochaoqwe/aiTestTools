<template>
  <section class="upload-section">
    <h3>第一步：上传需求规格文档</h3>
    <div 
      class="upload-container" 
      @dragover="handleDragOver" 
      @dragleave="handleDragLeave"
      @dragenter="handleDragEnter"
      @drop="handleDrop"
      :class="{ 'drag-active': isDragging }"
    >
      <div class="upload-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
      </div>
      <p class="upload-text">拖放文件到此处或</p>
      <div class="file-controls">
        <button class="file-input-label" @click="clickFileInput">选择文件</button>
        <input 
          type="file" 
          id="fileInput" 
          accept=".doc,.docx" 
          style="display: none;" 
          @change="handleFileInputChange"
        >
      </div>
      <div class="file-info" v-if="fileInfoVisible">
        <div class="selected-file">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <p>已选择文件: <span class="file-name">{{ fileName }}</span></p>
        </div>
        <button class="btn upload-btn" @click="uploadFile">上传文件</button>
      </div>
      <StatusMessage 
        :visible="statusVisible" 
        :message="statusMsg" 
        :type="statusType || 'info'" 
      />
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import StatusMessage from './StatusMessage.vue';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5002/api';

const emit = defineEmits(['upload-success']);

// 文件上传状态
const file = ref(null);
const fileName = ref('');
const fileInfoVisible = ref(false);
const statusMsg = ref('');
const statusType = ref('');
const statusVisible = ref(false);
const isDragging = ref(false);

// 处理拖拽事件
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDragEnter(e) {
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = true;
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = false;
}

// 处理文件拖放
function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = false;
  
  if (e.dataTransfer.files.length) {
    handleFileSelect(e.dataTransfer.files);
  }
}

// 处理文件选择
function handleFileSelect(files) {
  if (files.length > 0) {
    file.value = files[0];
    fileName.value = files[0].name;
    fileInfoVisible.value = true;
  }
}

// 点击文件输入按钮
function clickFileInput() {
  document.getElementById('fileInput').click();
}

// 打开文件选择对话框
function handleFileInputChange(e) {
  handleFileSelect(e.target.files);
}

// 显示状态消息
function showStatus(message, type) {
  statusMsg.value = message;
  const validTypes = ['success', 'error', 'info'];
  statusType.value = validTypes.includes(type) ? type : 'info';
  statusVisible.value = true;
}

// 上传文件
async function uploadFile() {
  if (!file.value) {
    showStatus('请先选择文件', 'error');
    return;
  }
  
  const formData = new FormData();
  formData.append('file', file.value);
  
  showStatus('正在上传文件...', 'info');
  
  try {
    console.log('开始上传文件到', `${API_BASE_URL}/upload`);
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      withCredentials: false // 不发送cookies，避免CORS预检请求问题
    });
    
    console.log('上传文件成功，响应数据:', response.data);
    fileName.value = response.data.file_name;
    
    showStatus('文件上传成功', 'success');
    
    // 通知父组件上传成功
    emit('upload-success', response.data);
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
    
    showStatus('错误：' + errorMessage, 'error');
  }
}
</script>

<style scoped>
.upload-section {
  background-color: #ffffff;
  border-radius: 8px;
  margin-top: 20px;
}

h3 {
  font-size: 1.4rem;
  color: #2c3e50;
  margin-bottom: 20px;
  position: relative;
  padding-bottom: 10px;
}

h3::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 40px;
  height: 3px;
  background-color: #3498db;
  border-radius: 3px;
}

.upload-container {
  border: 2px dashed #cbd5e0;
  border-radius: 10px;
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s ease;
  background-color: #f8fafc;
  position: relative;
  overflow: hidden;
}

.upload-container:hover {
  border-color: #3498db;
  background-color: #eef6fd;
}

.upload-container.drag-active {
  border-color: #3498db;
  background-color: #eef6fd;
  transform: scale(1.02);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.upload-icon {
  margin-bottom: 15px;
  color: #94a3b8;
  transition: all 0.3s ease;
}

.upload-container:hover .upload-icon,
.upload-container.drag-active .upload-icon {
  color: #3498db;
  transform: translateY(-5px);
}

.upload-text {
  color: #64748b;
  margin-bottom: 20px;
  font-size: 1.1rem;
}

.file-controls {
  margin-bottom: 15px;
}

.file-input-label {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  font-size: 1rem;
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 6px rgba(52, 152, 219, 0.2);
}

.file-input-label:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

.file-info {
  margin-top: 25px;
  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.selected-file {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  color: #64748b;
}

.selected-file svg {
  margin-right: 10px;
  color: #3498db;
}

.file-name {
  color: #3498db;
  font-weight: 500;
}

.upload-btn {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 10px 20px;
  font-size: 1rem;
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 3px 6px rgba(46, 204, 113, 0.2);
}

.upload-btn:hover {
  background-color: #27ae60;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(46, 204, 113, 0.3);
}
</style>
