# AI测试工具

这个系统用于从需求规格说明文档中提取需求项，并生成相应的需求分析表和测试用例表。

## 系统架构

系统分为两部分：
- **后端**：基于Flask的API服务，负责处理文档解析和Excel生成
- **前端**：基于HTML/CSS/JavaScript的Web界面，负责用户交互

## 环境要求

- Windows 7 或更高版本
- Python 3.6 或更高版本
- 现代浏览器（IE11、Chrome、Firefox等）

## 安装说明

### 后端安装

1. 确保已安装Python 3.6或更高版本
2. 打开命令提示符，进入后端目录：
   ```
   cd e:\code\requirement_extractor\backend
   ```
3. 安装所需依赖：
   ```
   pip install -r requirements.txt
   ```

### 前端安装

前端是纯静态网页，无需特殊安装。

## 运行说明

### 启动后端服务

1. 打开命令提示符，进入后端目录：
   ```
   cd e:\code\requirement_extractor\backend
   ```
2. 运行后端服务：
   ```
   python run.py
   ```
3. 服务将在 http://localhost:5001 上运行

### 启动前端界面

1. 直接双击打开 `e:\code\requirement_extractor\frontend\index.html` 文件
2. 或者通过浏览器打开该文件

## 使用说明

1. 在前端界面上传需求规格说明文档（支持.doc和.docx格式）
2. 点击"提取需求"按钮，系统将自动提取文档中的需求项
3. 查看提取的需求列表
4. 点击"导出需求分析表"或"导出测试用例表"按钮生成相应的Excel文件

## 目录结构

```
requirement_extractor/
├── backend/                # 后端代码
│   ├── app/                # 应用代码
│   │   ├── __init__.py     # 包初始化文件
│   │   ├── api.py          # API接口定义
│   │   ├── document_reader.py  # 文档读取模块
│   │   └── requirement_extractor.py  # 需求提取模块
│   ├── uploads/            # 上传文件存储目录
│   ├── outputs/            # 输出文件存储目录
│   ├── requirements.txt    # 依赖列表
│   └── run.py              # 启动脚本
└── frontend/               # 前端代码
    ├── src/                # 源代码
    │   ├── script.js       # JavaScript脚本
    │   └── styles.css      # CSS样式
    └── index.html          # 主页面
```

## 注意事项

1. 确保后端服务在使用前端之前已经启动
2. 文档必须是Word格式（.doc或.docx）
3. 需求规格说明文档中的章节号应当有明确的格式（如3.1.2）
4. 如果遇到问题，请检查后端服务日志

## 扩展功能

如需扩展系统功能，可以：
1. 修改 `document_reader.py` 以支持更多文档格式或提取方式
2. 修改 `requirement_extractor.py` 以改进需求处理逻辑
3. 在 `api.py` 中添加新的API端点
4. 更新前端界面以支持新功能
