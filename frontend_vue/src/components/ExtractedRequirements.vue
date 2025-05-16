<template>
  <section class="requirements-section">
    <h2>第四步：查看和导出需求</h2>
    <div class="requirements-info">
      <p>共提取到 <span>{{ requirements.length }}</span> 条需求</p>
    </div>
    
    <!-- 需求列表 -->
    <div v-if="!showReview" class="requirements-table-container">
      <table class="requirements-table">
        <thead>
          <tr>
            <th>需求名称</th>
            <th>章节号</th>
            <th>需求描述</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(req, index) in requirements" :key="index">
            <td>{{ req.name }}</td>
            <td>{{ req.chapter }}</td>
            <td class="content-cell">
              <pre>{{ req.content }}</pre>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 审查结果组件 -->
    <RequirementReview
      v-if="showReview"
      :requirements="requirements"
      :sessionId="getSessionId()"
      :showReview="showReview"
      :apiService="props.apiService"
      ref="reviewComponent"
      @review-completed="handleReviewCompleted"
    />
    
    <div class="export-options">
      <h3>操作选项</h3>
      <div class="export-buttons">
        <button v-if="!showReview" class="btn primary-btn" @click="startReview">AI文档审查</button>
        <button v-if="!showReview" class="btn primary-btn" @click="rematchRequirements" :disabled="rematchLoading">
          {{ rematchLoading ? '匹配中...' : '一键重新匹配' }}
        </button>
        <button v-if="reviewCompleted" class="btn secondary-btn" @click="generateExcel('review')">导出文档审查单</button>
      </div>
    </div>
    
    <StatusMessage 
      :visible="statusVisible" 
      :message="statusMsg" 
      :type="statusType" 
    />
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import StatusMessage from './StatusMessage.vue';
import RequirementReview from './RequirementReview.vue';

const props = defineProps({
  requirements: {
    type: Array,
    required: true
  },
  sessionId: {
    type: String,
    default: ''
  },
  fileId: {
    type: String,
    default: ''
  },
  fileName: {
    type: String,
    default: ''
  },
  apiService: {
    type: Object,
    required: true
  }
});

// 生成一个组件级别的会话ID，用于在未提供sessionId的情况下
const internalSessionId = ref('');

// 获取有效的会话ID（优先使用props中的，如果没有则使用内部生成的）
const getSessionId = () => {
  return props.sessionId || internalSessionId.value;
};

// 调试查看接收到的内容
onMounted(() => {
  console.log('ExtractedRequirements组件接收到需求：', props.requirements);
  if (props.requirements && props.requirements.length > 0) {
    console.log('第一个需求内容：', props.requirements[0]);
    console.log('内容类型：', typeof props.requirements[0].content);
    console.log('内容长度：', props.requirements[0].content.length);
    console.log('内容前50个字符：', props.requirements[0].content.substring(0, 50));
  }
  
  // 如果没有提供sessionId，生成一个内部使用的ID
  if (!props.sessionId) {
    internalSessionId.value = 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 10);
    console.log('未提供sessionId，已生成内部会话ID:', internalSessionId.value);
  }
});

// 状态变量
const statusMsg = ref('');
const statusType = ref('');
const statusVisible = ref(false);

// 审查状态变量
const showReview = ref(false);
const reviewCompleted = ref(false);
const reviewComponent = ref(null);

// 重新匹配状态
const rematchLoading = ref(false);

// 开始审查
function startReview() {
  showReview.value = true;
  
  // 延迟一下，确保组件已渲染
  setTimeout(() => {
    // 如果引用存在，调用审查组件的startReview方法
    if (reviewComponent.value) {
      reviewComponent.value.startReview();
    }
  }, 100);
}

// 处理审查完成事件
function handleReviewCompleted() {
  reviewCompleted.value = true;
}

// 一键重新匹配
async function rematchRequirements() {
  try {
    // 设置加载状态
    rematchLoading.value = true;
    showStatus('正在重新匹配未识别到的需求...', 'info');
    
    // 需要发送的数据
    const requestData = {
      file_id: props.fileId,
      file_name: props.fileName,
      session_id: getSessionId()
    };
    
    // 调用API
    const response = await props.apiService.post('/api/rematch_requirements', requestData);
    
    if (response && response.data && response.data.success) {
      // 更新需求列表
      const newRequirements = [];
      for (const [name, content] of Object.entries(response.data.requirements)) {
        newRequirements.push({
          name: name,
          content: content,
          // 从内容中提取章节号或使用默认值
          chapter: content.match(/\d+\.\d+\.\d+/) ? content.match(/\d+\.\d+\.\d+/)[0] : ''
        });
      }
      
      // 清除之前的数据并更新
      requirements.splice(0, requirements.length, ...newRequirements);
      
      // 显示成功消息
      showStatus(`重新匹配成功，共找到 ${newRequirements.length} 条需求`, 'success');
    } else {
      showStatus('重新匹配失败：' + (response.data ? response.data.error : '未知错误'), 'error');
    }
  } catch (error) {
    console.error('重新匹配需求时出错：', error);
    showStatus(`重新匹配失败：${error.message || '网络错误'}`, 'error');
  } finally {
    rematchLoading.value = false;
  }
}

// 生成Excel文件
async function generateExcel(excelType) {
  const typeText = excelType === 'requirement' ? '需求分析表' : excelType === 'test_case' ? '测试用例表' : '文档审查单';
  
  showStatus(`正在生成${typeText}...`, 'info');
  
  try {
    // 首先尝试常规导出API
    try {
      // 使用generate_excel端点
      const data = await props.apiService.generateExcel({
        session_id: getSessionId(),
        excel_type: excelType
      });
      
      console.log(`${typeText}生成成功:`, data);
      
      // 根据响应格式处理下载
      if (data.download_url) {
        showStatus(`${typeText}生成成功，准备下载...`, 'success');
        window.location.href = `${props.apiService.getBaseUrl()}${data.download_url}`;
        return;
      } else if (excelType !== 'review') {
        showStatus(`${typeText}生成成功，准备下载...`, 'success');
        window.location.href = props.apiService.getExcelDownloadUrl(getSessionId(), excelType);
        return;
      }
    } catch (error) {
      console.log("尝试常规导出API失败，将尝试审查文档导出API:", error);
    }
    
    // 如果常规导出失败，尝试使用审查文档API
    const reviewData = await props.apiService.generateReviewDocument({
      session_id: getSessionId(),
      excel_type: excelType
    });
    
    console.log(`${typeText}生成成功(使用审查文档API):`, reviewData);
    
    if (reviewData.success && reviewData.file_id) {
      showStatus(`${typeText}生成成功，准备下载...`, 'success');
      
      // 创建一个隐藏的a标签来触发下载
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = props.apiService.getDownloadUrl(reviewData.file_id);
      a.download = `${typeText}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      throw new Error(`生成${typeText}失败: 未返回有效的文件信息`);
    }
  } catch (error) {
    console.error(`生成${typeText}出错: `, error);
    showStatus('错误：' + error.message, 'error');
  }
}

// 显示状态消息
function showStatus(message, type) {
  statusMsg.value = message;
  statusType.value = type;
  statusVisible.value = true;
}
</script>

<style scoped>
.requirements-section {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.requirements-info {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.requirements-info p {
  margin: 0;
  font-size: 16px;
}

.requirements-info span {
  font-weight: bold;
  color: #3498db;
}

.requirements-table-container {
  width: 100%;
  overflow-x: auto;
  margin-bottom: 20px;
}

.requirements-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.requirements-table th, 
.requirements-table td {
  padding: 10px;
  text-align: left;
  border: 1px solid #ddd;
  word-break: break-word;
}

.requirements-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.requirements-table th:nth-child(1) {
  width: 25%;
}

.requirements-table th:nth-child(2) {
  width: 15%;
}

.requirements-table th:nth-child(3) {
  width: 60%;
}

.content-cell {
  white-space: pre-wrap;
  font-family: monospace;
  overflow-wrap: break-word;
  word-wrap: break-word;
  max-width: 500px;
}

pre {
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

.export-options {
  margin-top: 20px;
}

.export-options h3 {
  margin-bottom: 10px;
}

.export-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.primary-btn {
  background-color: #4CAF50;
  color: white;
}

.primary-btn:hover {
  background-color: #3e8e41;
}

.secondary-btn {
  background-color: #2ecc71;
  color: white;
}

.secondary-btn:hover {
  background-color: #27ae60;
}
</style>
