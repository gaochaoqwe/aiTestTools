"""
配置项相关API的主注册中心
只负责创建Flask实例和注册各业务Blueprint
"""
from flask import Flask
from app.documentReview.ConfigurationItem.upload.upload_api import upload_bp
from app.documentReview.ConfigurationItem.ai_extraction.ai_extraction_api import ai_extraction_bp
from app.documentReview.ConfigurationItem.review.review_api import review_bp
from app.documentReview.ConfigurationItem.downloadDocument.download_review import download_review_bp
from app.documentReview.ConfigurationItem.review.validate_api import validate_bp

app = Flask(__name__)

# 全局配置（如有需要，可自行添加）
# app.config['UPLOAD_FOLDER'] = ...
# app.config['OUTPUT_FOLDER'] = ...

# 注册核心API
app.register_blueprint(upload_bp)
app.register_blueprint(ai_extraction_bp)
app.register_blueprint(review_bp)
app.register_blueprint(download_review_bp)
app.register_blueprint(validate_bp)
