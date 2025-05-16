// 配置项测试服务
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5002/api';

export const configurationItemService = {
  // 获取API基础URL
  getBaseUrl: () => {
    return API_BASE_URL;
  },

  // 上传文件
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('上传文件错误:', error);
      throw error;
    }
  },

  // 提取需求候选项
  fetchRequirementCandidates: async (fileId, fileName, catalogFileId, catalogFileName) => {
    try {
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

  // 审查需求
  reviewRequirements: async (data) => {
    try {
      // 确保传递的需求是对象数组格式，每个对象包含name、chapter和content属性
      const requirementsData = Array.isArray(data.requirements) 
        ? data.requirements.map(req => {
            // 确保每个需求是正确的对象格式
            if (typeof req === 'string') {
              // 如果是字符串，尝试解析为JSON
              try {
                return JSON.parse(req);
              } catch (e) {
                // 如果无法解析，则创建一个默认结构
                return { content: req, name: '未命名需求', chapter: '未知章节' };
              }
            }
            return req;
          })
        : [];

      console.log('格式化后的需求数据:', requirementsData);

      const response = await axios.post(`${API_BASE_URL}/review_requirements`, {
        requirements: requirementsData,
        session_id: data.session_id
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
      
      // 根据日志分析，我们确定以下端点是可工作的:
      // - /api/generate_review_document (针对review类型)
      // - /api/generate_excel (针对其他类型，但可能不一致)
      
      // 由于后端API的一致性问题，我们使用更可靠的generate_review_document端点
      console.log(`使用可靠的审查文档API: /api/generate_review_document`);
      const response = await axios.post(`${API_BASE_URL}/generate_review_document`, {
        session_id: params.session_id,
        excel_type: params.excel_type
      });
      
      console.log(`生成文件成功:`, response.data);
      
      // 如果响应包含download_url，直接使用
      if (response.data.download_url) {
        return response.data;
      }
      
      // 否则，对于需求分析表和测试用例表，构建标准的下载URL
      if (params.excel_type === 'requirement' || params.excel_type === 'test_case') {
        return {
          ...response.data,
          download_url: `/api/download/${params.session_id}/${params.excel_type}`
        };
      }
      
      // 如果没有明确的下载URL，返回原始响应
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
  },
  
  // AI提取需求详情
  aiExtractRequirements: async (fileId, fileName, requirementNames, model = null) => {
    try {
      console.log('调用AI提取需求详情:', fileId, fileName, requirementNames?.length || 0);
      const response = await axios.post(`${API_BASE_URL}/ai_extract`, {
        file_id: fileId,
        file_name: fileName,
        requirement_names: requirementNames || [],
        model: model
      });
      return response.data;
    } catch (error) {
      console.error('AI提取需求详情错误:', error);
      throw error;
    }
  },

  // 一键重新匹配
  rematchRequirements: async (fileId, fileName, sessionId, model = null) => {
    try {
      console.log('调用一键重新匹配:', fileId, sessionId);
      const response = await axios.post(`${API_BASE_URL}/rematch_requirements`, {
        file_id: fileId,
        file_name: fileName,
        session_id: sessionId,
        model: model
      });
      return response.data;
    } catch (error) {
      console.error('需求重新匹配错误:', error);
      throw error;
    }
  },
  
  // AI自动提取目录
  extractCatalogWithAI: async (fileId, fileName, requirementLevel = 3, model = null) => {
    try {
      console.log('调用AI自动提取目录:', fileId, fileName, '需求级别:', requirementLevel);
      const response = await axios.post(`${API_BASE_URL}/ai_catalog`, {
        file_id: fileId,
        file_name: fileName,
        requirement_level: requirementLevel,
        model: model
      });
      return response.data;
    } catch (error) {
      console.error('AI目录提取错误:', error);
      throw error;
    }
  }
};

export default configurationItemService;
