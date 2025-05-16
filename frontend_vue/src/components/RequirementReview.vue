<template>
  <section class="review-section">
    <h2>AI文档审查结果</h2>
    <div class="review-info">
      <p>共审查了 <span>{{ reviewResults.length }}</span> 条需求</p>
    </div>
    
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>AI正在审查需求，请稍候...</p>
    </div>
    
    <div v-else class="review-container">
      <div v-for="(item, index) in reviewResults" :key="index" class="review-item">
        <div class="review-header">
          <h3>{{ item.name }}</h3>
          <span class="chapter-badge">{{ item.chapter }}</span>
          <span 
            class="status-badge" 
            :class="hasProblems(item) ? 'status-problem' : 'status-good'"
          >
            {{ hasProblems(item) ? '存在问题' : '质量良好' }}
          </span>
        </div>
        
        <div class="review-content">
          <div v-for="(problem, pIndex) in getProblems(item)" :key="pIndex" class="problem-item">
            <div class="problem-header">
              问题 #{{ pIndex + 1 }}{{ problem.problem_title ? ': ' + problem.problem_title : '' }}
            </div>
            
            <div class="detail-row">
              <div class="detail-label">需求描述:</div>
              <div class="detail-content">{{ problem.requirement_description }}</div>
            </div>
            
            <div class="detail-row">
              <div class="detail-label">问题描述:</div>
              <div class="detail-content problem-description">{{ problem.problem_description }}</div>
            </div>
            
            <div class="detail-row">
              <div class="detail-label">问题定位:</div>
              <div class="detail-content">{{ problem.problem_location }}</div>
            </div>
            
            <div class="detail-row">
              <div class="detail-label">影响分析:</div>
              <div class="detail-content">{{ problem.impact_analysis }}</div>
            </div>
          </div>
          
          <div v-if="!hasProblems(item)" class="no-problems">
            <p>恭喜！该需求质量良好，未发现明显问题。</p>
          </div>
        </div>
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

const props = defineProps({
  requirements: {
    type: Array,
    required: true
  },
  sessionId: {
    type: String,
    required: true
  },
  showReview: {
    type: Boolean,
    default: false
  },
  apiService: {
    type: Object,
    required: true
  }
});

// 事件
const emit = defineEmits(['review-completed']);

// 状态变量
const reviewResults = ref([]);
const loading = ref(false);
const generating = ref(false);
const statusMsg = ref('');
const statusType = ref('');
const statusVisible = ref(false);

// 检查一个需求项是否有问题
function hasProblems(item) {
  if (!item || !item.review_result || !item.review_result.requirements_review) {
    return false;
  }
  
  const problems = item.review_result.requirements_review;
  if (problems.length === 0) {
    return false;
  }
  
  // 如果只有一条记录且表明质量良好，则认为没有问题
  if (problems.length === 1) {
    const problem = problems[0];
    const description = problem.problem_description || '';
    if (description.toLowerCase().includes('质量良好') || 
        description.toLowerCase().includes('未发现问题')) {
      return false;
    }
  }
  
  return true;
}

// 获取需求项的问题列表
function getProblems(item) {
  if (!item || !item.review_result || !item.review_result.requirements_review) {
    return [];
  }
  
  return item.review_result.requirements_review;
}

// 开始AI审查
async function startReview() {
  loading.value = true;
  statusMsg.value = '正在调用AI审查需求...'
  statusType.value = 'info'
  statusVisible.value = true;
  
  try {
    console.log('开始审查需求，会话ID:', props.sessionId);
    
    // 检查API服务的类型并根据不同的API结构调整参数
    let data;
    if (props.apiService.getBaseUrl().includes('/regression/api')) {
      // 回归测试API需要两个单独的参数
      console.log('使用回归测试API服务');
      data = await props.apiService.reviewRequirements(props.requirements, props.sessionId);
    } else {
      // 配置项API需要一个对象参数
      console.log('使用配置项API服务');
      data = await props.apiService.reviewRequirements({
        requirements: props.requirements,
        session_id: props.sessionId
      });
    }
    
    console.log('需求审查响应:', data);
    
    // 更新审查结果
    reviewResults.value = data.review_results || [];
    
    // 发出审查完成事件
    emit('review-completed');
    
    showStatus('需求审查完成！', 'success');
  } catch (error) {
    console.error('审查需求时出错:', error);
    showStatus(`审查需求失败: ${error.message}`, 'error');
    reviewResults.value = [];
  } finally {
    loading.value = false;
  }
}

// 生成审查文档
async function generateReviewDoc() {
  generating.value = true;
  statusMsg.value = '正在生成审查文档...'
  statusType.value = 'info'
  statusVisible.value = true;
  
  try {
    // 准备请求数据
    const requestData = {
      review_results: reviewResults.value,
      session_id: props.sessionId
    };
    
    // 发送请求
    const data = await props.apiService.generateReviewDocument(requestData);
    
    console.log('生成审查文档响应:', data);
    
    // 如果成功，提供下载链接
    if (data.success && data.file_id) {
      // 构建下载URL
      const downloadUrl = `${props.apiService.getBaseUrl()}/download/${data.file_id}`;
      
      // 创建一个隐藏的a标签来触发下载
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = downloadUrl;
      a.download = data.file_id;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      showStatus('审查文档已生成，正在下载...', 'success');
    } else {
      throw new Error('生成审查文档失败');
    }
  } catch (error) {
    console.error('生成审查文档时出错:', error);
    showStatus(`生成审查文档失败: ${error.message}`, 'error');
  } finally {
    generating.value = false;
  }
}

// 显示状态信息
function showStatus(message, type) {
  statusMsg.value = message;
  statusType.value = type;
  statusVisible.value = true;
}

// 组件挂载时，如果showReview为true则自动开始审查
onMounted(() => {
  if (props.showReview) {
    startReview();
  }
});

// 将函数暴露给父组件
defineExpose({ startReview });
</script>

<style scoped>
.review-section {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin: 20px 0;
}

.review-info {
  margin-bottom: 20px;
}

.review-info span {
  font-weight: bold;
  color: #3498db;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 30px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e0;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(52, 152, 219, 0.2);
  border-radius: 50%;
  border-top-color: #3498db;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.review-container {
  margin-bottom: 30px;
}

.review-item {
  background-color: #f8fafc;
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.review-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f0f9ff;
  border-bottom: 1px solid #e2e8f0;
}

.review-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #2c3e50;
  flex: 1;
}

.chapter-badge {
  background-color: #4299e1;
  color: white;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-right: 10px;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-good {
  background-color: #68d391;
  color: #22543d;
}

.status-problem {
  background-color: #fc8181;
  color: #742a2a;
}

.review-content {
  padding: 16px;
}

.problem-item {
  background-color: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.problem-header {
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
  color: #2d3748;
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
}

.detail-label {
  width: 100px;
  font-weight: 500;
  color: #4a5568;
  flex-shrink: 0;
}

.detail-content {
  flex: 1;
  line-height: 1.5;
}

.problem-description {
  color: #e53e3e;
  font-weight: 500;
}

.no-problems {
  padding: 20px;
  text-align: center;
  background-color: #f0fff4;
  border-radius: 6px;
  color: #276749;
}
</style>
