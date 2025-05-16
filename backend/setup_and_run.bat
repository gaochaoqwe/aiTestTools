@echo off
chcp 65001
echo AI测试工具 - 后端服务安装和启动脚本

echo 正在安装依赖...
pip install flask==2.0.1 python-docx==0.8.11 openpyxl==3.0.9 flask-cors==3.0.10 Werkzeug==2.0.3

echo 创建上传和输出目录...
if not exist uploads mkdir uploads
if not exist outputs mkdir outputs

echo 启动后端服务...
python run.py

pause
