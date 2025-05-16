// 回归测试服务
import axios from 'axios';

// 定义API基础URL - 回归测试专用
const API_BASE_URL = 'http://localhost:5002/regression/api';

// 导出服务API
export const regressionService = {
  // 获取基础URL（用于构建完整的下载链接）
  getBaseUrl: () => {
    return 'http://localhost:5002';
  },

  // 上传文件
  uploadFile: async (formData) => {
    try {
      console.log('发送上传请求到:', `${API_BASE_URL}/upload`);
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('文件上传错误:', error);
      throw error;
    }
  },

  // 获取需求候选项
  fetchRequirementCandidates: async (fileId, fileName, catalogFileId, catalogFileName) => {
    try {
      console.log('发送获取候选项请求到:', `${API_BASE_URL}/requirement_candidates`);
      const response = await axios.post(`${API_BASE_URL}/requirement_candidates`, {
        file_id: fileId,
        file_name: fileName,
        catalog_file_id: catalogFileId,
        catalog_file_name: catalogFileName
      });
      return response.data;
    } catch (error) {
      console.error('获取需求候选项错误:', error);
      throw error;
    }
  },

  // 提取需求详情
  extractRequirements: async (fileId, fileName, requirementNames, catalogFileId, catalogFileName) => {
    try {
      console.log('发送提取需求请求到:', `${API_BASE_URL}/extract`);
      const response = await axios.post(`${API_BASE_URL}/extract`, {
        file_id: fileId,
        file_name: fileName,
        requirement_names: requirementNames,
        catalog_file_id: catalogFileId,
        catalog_file_name: catalogFileName
      });
      return response.data;
    } catch (error) {
      console.error('提取需求详情错误:', error);
      throw error;
    }
  },

  // AI提取需求详情
  aiExtractRequirements: async (fileId, fileName, requirementNames, model = 'gpt-3.5-turbo') => {
    try {
      console.log('发送AI提取需求请求到:', `${API_BASE_URL}/ai_extract`);
      const response = await axios.post(`${API_BASE_URL}/ai_extract`, {
        file_id: fileId,
        file_name: fileName,
        requirement_names: requirementNames,
        model: model
      });
      return response.data;
    } catch (error) {
      console.error('AI提取需求详情错误:', error);
      throw error;
    }
  },

  // 审查需求
  reviewRequirements: async (requirements, sessionId) => {
    try {
      console.log('发送审查需求请求到:', `${API_BASE_URL}/review_requirements`);
      // 确保requirements是一个数组
      const requirementsArray = Array.isArray(requirements) ? requirements : [requirements];
      
      const response = await axios.post(`${API_BASE_URL}/review_requirements`, {
        requirements: requirementsArray,
        session_id: sessionId || 'default'
      });
      return response.data;
    } catch (error) {
      console.error('审查需求错误:', error);
      throw error;
    }
  },

  // 生成Excel文件
  generateExcel: async (params) => {
    try {
      // 会话ID是必须的
      if (!params.session_id) {
        throw new Error('缺少会话ID参数');
      }
      
      // 使用回归测试的API端点
      const endpoint = params.excel_type === 'review' || !params.excel_type
        ? `${API_BASE_URL}/generate_review_document`
        : `${API_BASE_URL}/generate_excel`;
      
      console.log(`发送生成Excel请求到:`, endpoint);
      
      const response = await axios.post(endpoint, {
        session_id: params.session_id,
        excel_type: params.excel_type
      });
      
      console.log(`生成文件成功:`, response.data);
      return response.data;
    } catch (error) {
      console.error('生成Excel文件错误:', error);
      // 提供用户友好的错误信息
      const errorMessage = error.response && error.response.data && error.response.data.error 
        ? error.response.data.error 
        : '导出文件失败，请联系管理员';
      throw new Error(errorMessage);
    }
  },

  // 生成审查文档
  generateReviewDocument: async (params) => {
    try {
      console.log('发送生成审查文档请求到:', `${API_BASE_URL}/generate_review_document`);
      const response = await axios.post(`${API_BASE_URL}/generate_review_document`, {
        session_id: params.session_id
      });
      return response.data;
    } catch (error) {
      console.error('生成审查文档错误:', error);
      throw error;
    }
  },
  
  // 下载审查文档
  getDownloadUrl: (docId) => {
    return `${API_BASE_URL}/download_review/${docId}`;
  },
  
  // 构建Excel下载URL
  getExcelDownloadUrl: (sessionId, excelType) => {
    return `${API_BASE_URL}/download/${sessionId}/${excelType}`;
  }
};

export default regressionService;
