<template>
  <section class="candidates-section">
    <h2>第二步：AI提取需求</h2>
    
    <div class="ai-extract-panel">
      <div v-if="!extractStarted" class="ai-extract-intro">
        <h3>开始需求提取</h3>
        <p class="info-text">
          <span class="info-icon">ℹ️</span>
          AI将分析您上传的规格说明文档，自动提取需求目录并生成详细需求内容。点击下方按钮开始提取。
        </p>
        <div class="extraction-settings">
          <div class="requirement-level">
            <label>需求级别：</label>
            <select v-model="requirementLevel">
              <option value="3">3级 (如 3.2.1)</option>
              <option value="4">4级 (如 3.2.1.1)</option>
              <option value="5">5级 (如 3.2.1.1.1)</option>
            </select>
          </div>
          <div class="extraction-method-select">
            <label>提取方式：</label>
            <div class="radio-options">
              <div class="radio-option">
                <input type="radio" id="ai-extract" value="ai" v-model="extractionMethod" checked>
                <label for="ai-extract">AI智能提取（推荐）</label>
              </div>
            </div>
          </div>
        </div>
        <button 
          class="btn primary-btn start-extract-btn" 
          @click="startAIExtraction" 
          :disabled="loading"
        >
          {{ loading ? '正在准备AI提取...' : '开始AI需求提取' }}
        </button>
      </div>
      
      <div v-if="extracting" class="extraction-progress">
        <div class="progress-indicator">
          <div class="spinner"></div>
          <h3>正在提取需求中...</h3>
          <p>该过程可能需要几分钟时间，请耐心等待</p>
        </div>
      </div>
    </div>
    
    <div class="candidates-info">
      <p>共有 <span>{{ candidates.length }}</span> 个需求名称候选</p>
    </div>
    <div class="candidates-table-container">
      <table class="candidates-table">
        <thead>
          <tr>
            <th>需求名称</th>
            <th>章节号</th>
            <th>
              <div class="select-all-container">
                <input 
                  type="checkbox" 
                  id="select-all" 
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                />
                <label for="select-all">全选</label>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(candidate, index) in displayCandidates" :key="index">
            <td>{{ candidate.name }}</td>
            <td>{{ candidate.chapter }}</td>
            <td>
              <input 
                type="checkbox" 
                :id="'candidate-' + index" 
                :value="candidate" 
                v-model="selectedRequirements"
              >
            </td>
          </tr>
          <tr v-if="displayCandidates.length === 0">
            <td colspan="3" style="text-align: center; padding: 15px;">
              <div v-if="loading">加载中...</div>
              <div v-else>没有找到需求候选项</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <StatusMessage 
      :visible="statusVisible" 
      :message="statusMsg" 
      :type="statusType" 
    />
    
    <div class="extraction-options">
      <h3>提取方式选择</h3>
      <div class="radio-options">
        <div class="radio-option">
          <input type="radio" id="traditional-extract" value="traditional" v-model="extractionMethod">
          <label for="traditional-extract">传统算法提取（基于文本匹配）</label>
        </div>
        <div class="radio-option">
          <input type="radio" id="ai-extract" value="ai" v-model="extractionMethod">
          <label for="ai-extract">AI智能提取（基于大语言模型分析）</label>
        </div>
      </div>
      <div class="extraction-description" v-if="extractionMethod === 'ai'">
        <p class="info-text">
          <span class="info-icon">ℹ️</span>
          AI提取使用大型语言模型分析文档结构，能更准确地识别需求边界和内容。处理速度可能较慢，但提取质量更高。
        </p>
      </div>
      <div class="extraction-description" v-if="extractionMethod === 'traditional'">
        <p class="info-text">
          <span class="info-icon">ℹ️</span>
          传统算法提取基于文本匹配和结构分析，速度较快，但在复杂文档中可能会遇到边界识别问题。
        </p>
      </div>
    </div>
    
    <button 
      class="btn primary-btn" 
      @click="extractRequirements"
      :disabled="selectedRequirements.length === 0"
      :class="{ 'disabled-btn': selectedRequirements.length === 0 }"
    >
      确认并提取需求
    </button>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import StatusMessage from './StatusMessage.vue';

const props = defineProps({
  fileId: {
    type: String,
    required: true
  },
  fileName: {
    type: String,
    required: true
  },
  fileExt: {
    type: String,
    default: '.docx'
  },
  apiService: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['extract-complete']);

// 需求数据
const candidates = ref([]);
const selectedRequirements = ref([]);

// 状态相关
const statusMsg = ref('');
const statusType = ref('info');
const statusVisible = ref(false);
const loading = ref(false);
const extracting = ref(false);
const extractStarted = ref(false);
const extractionMethod = ref('ai'); // 默认使用AI算法
const requirementLevel = ref('3'); // 需求级别，默认为3级

// 用于显示的需求候选项列表
const displayCandidates = computed(() => {
  console.log('计算displayCandidates，数据源长度:', candidates.value.length);
  return candidates.value;
});

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return displayCandidates.value.length > 0 && selectedRequirements.value.length === displayCandidates.value.length;
});

// 全选/取消全选功能
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    // 如果已经全选，则取消全选
    selectedRequirements.value = [];
  } else {
    // 如果还没全选，则全选
    selectedRequirements.value = [...displayCandidates.value];
    console.log('用户点击全选，选中了', selectedRequirements.value.length, '项');
  }
};

// 处理提取按钮事件
const extractRequirements = async () => {
  loading.value = true;
  statusMsg.value = '正在提取需求内容...'
  statusType.value = 'info'
  statusVisible.value = true;
  
  try {
    // 获取选中的需求名称
    const selectedNames = selectedRequirements.value.map(req => req.name);
    
    // 确保所有必需参数存在
    console.log('参数检查:', {
      fileId: props.fileId,
      fileName: props.fileName,
      extractionMethod: extractionMethod.value
    });
    
    let missingParams = [];
    if (!props.fileId) missingParams.push('文件ID');
    
    if (missingParams.length > 0) {
      throw new Error(`缺少必要参数: ${missingParams.join(', ')}，无法执行提取操作`);
    }
    
    console.log('使用文件ID:', props.fileId);
    console.log('使用提取方法:', extractionMethod.value);
    
    try {
      let data;
      
      if (extractionMethod.value === 'ai') {
        // 使用AI提取
        statusMsg.value = 'AI正在分析文档并提取需求，这可能需要一些时间...'
        
        // 调用AI提取接口
        data = await props.apiService.aiExtractRequirements(
          props.fileId, 
          props.fileName, 
          selectedNames
        );
      } else {
        // 使用传统算法提取
        data = await props.apiService.extractRequirements(
          props.fileId, 
          props.fileName, 
          selectedNames
        );
      }
      
      console.log('提取需求响应:', data);
      
      if (!data.requirements || data.requirements.length === 0) {
        throw new Error('未能提取到需求内容');
      }
      
      // 检查第一个需求的内容格式
      if (data.requirements.length > 0) {
        const firstReq = data.requirements[0];
        console.log('第一个需求内容示例:', {
          name: firstReq.name,
          chapter: firstReq.chapter,
          content: typeof firstReq.content === 'string' 
            ? (firstReq.content.length > 100 
               ? firstReq.content.substring(0, 100) + '...' 
               : firstReq.content)
            : '非文本内容'
        });
      }
      
      // 通知父组件提取完成
      const processedRequirements = data.requirements.map(req => {
        // 记录原始内容信息
        console.log(`需求「${req.name}」内容类型: ${typeof req.content}`);
        console.log(`需求「${req.name}」内容长度: ${req.content ? req.content.length : 0}`);
        if (req.content && req.content.length > 0) {
          console.log(`需求「${req.name}」内容前50字符: ${req.content.substring(0, 50)}`);
        }
        
        return {
          name: req.name,
          chapter: req.chapter,
          content: req.content || "未提供内容" // 确保内容不为空
        };
      });

      console.log('处理后的需求数据示例:', JSON.stringify(processedRequirements[0]));
      
      emit('extract-complete', {
        extractedRequirements: processedRequirements
      });
      
      statusMsg.value = `成功提取${processedRequirements.length}个需求内容`
      statusType.value = 'success'
    } catch (error) {
      console.error('提取需求时出错:', error);
      statusMsg.value = `提取需求失败: ${error.message}`
      statusType.value = 'error'
    }
  } catch (error) {
    console.error('提取需求时出错:', error);
    statusMsg.value = `提取需求失败: ${error.message}`
    statusType.value = 'error'
  } finally {
    loading.value = false;
  }
};

// 开始AI提取需求
async function startAIExtraction() {
  if (!props.fileId) {
    showStatus('请先上传文档文件', 'error');
    return;
  }
  
  loading.value = true;
  extractStarted.value = true;
  extracting.value = true;
  showStatus('正在使用AI提取需求，这可能需要几分钟时间...', 'info');
  
  try {
    console.log('开始AI提取，文件ID:', props.fileId);
    
    // 先清空之前的数据
    candidates.value = [];
    selectedRequirements.value = [];
    
    // 调用AI提取需求接口
    const response = await props.apiService.extractRequirementsWithAI({
      file_id: props.fileId,
      file_name: props.fileName,
      requirement_level: parseInt(requirementLevel.value)
    });
    
    console.log('AI需求提取响应:', response);
    
    if (response.success || response.requirements) {
      // 如果返回了需求数据
      const requirements = response.requirements || [];
      
      if (requirements.length > 0) {
        // 将提取到的需求添加到候选列表
        requirements.forEach(req => {
          // 确保level字段存在
          if (req.level === undefined && req.chapter) {
            req.level = req.chapter.split('.').length;
          }
          candidates.value.push(req);
          
          // 默认选中所有需求
          selectedRequirements.value.push(req);
        });
        
        showStatus(`AI成功提取到 ${requirements.length} 个需求`, 'success');
      } else {
        showStatus('未能提取到需求，请检查文档格式', 'warning');
      }
    } else {
      showStatus('AI提取需求失败: ' + (response.error || '未知错误'), 'error');
    }
  } catch (error) {
    console.error('AI需求提取错误:', error);
    showStatus(`AI需求提取失败: ${error.message || '未知错误'}`, 'error');
  } finally {
    loading.value = false;
    extracting.value = false;
  }
};

// 组件挂载后自动开始提取
onMounted(() => {
  console.log('RequirementCandidates组件挂载，文件ID:', props.fileId);
});

// 显示状态消息
const showStatus = (message, type = 'info') => {
  statusMsg.value = message;
  statusType.value = type;
  statusVisible.value = true;
};
</script>

<style scoped>
.candidates-section {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.candidates-info {
  margin-bottom: 15px;
}

.candidates-info span {
  font-weight: bold;
}

.candidates-table-container {
  overflow-x: auto;
  margin-bottom: 20px;
}

.candidates-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.candidates-table th,
.candidates-table td {
  padding: 12px;
  text-align: left;
  border: 1px solid #ddd;
}

.candidates-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.candidates-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.candidates-table tr:hover {
  background-color: #f5f5f5;
}

.select-all-container {
  display: flex;
  align-items: center;
}

.select-all-container label {
  margin-left: 5px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 15px;
}

.primary-btn {
  background-color: #3498db;
  color: white;
}

.primary-btn:hover {
  background-color: #2980b9;
}

.btn:disabled,
.disabled-btn {
  background-color: #cccccc !important;
  cursor: not-allowed;
  opacity: 0.7;
}

.extraction-options {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.extraction-options h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
  font-size: 1.1rem;
}

.radio-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 15px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-option label {
  cursor: pointer;
  font-weight: 500;
}

.extraction-description {
  margin-top: 10px;
  background-color: #ebf5fb;
  border-radius: 6px;
  padding: 10px;
  border-left: 4px solid #3498db;
}

.info-text {
  margin: 0;
  font-size: 0.9rem;
  color: #2c3e50;
  line-height: 1.4;
}

.info-icon {
  margin-right: 8px;
}

/* 新增的AI目录功能样式 */
.catalog-actions {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.ai-catalog-option {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-catalog-option h3 {
  margin-top: 0;
  color: #2c3e50;
  font-size: 16px;
}

.requirement-level {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.requirement-level label {
  font-weight: 600;
}

.requirement-level select {
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background-color: white;
  font-size: 14px;
}

.secondary-btn {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  align-self: flex-start;
}

.secondary-btn:hover {
  background-color: #3aa876;
}

.secondary-btn:disabled {
  background-color: #a8d5c3;
  cursor: not-allowed;
}
</style>
