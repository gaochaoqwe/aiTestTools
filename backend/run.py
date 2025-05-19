"""
后端应用入口文件
"""
import logging
import json
from flask import Flask, Response, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request
from app.documentReview.ConfigurationItem.configurationItem import app as config_app
from app.documentReview.Regression.api import app as regression_app
from app.projectManagement import pm_app
from a2wsgi import ASGIMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CORS中间件，添加必要的跨域头部
class CORSMiddleware:
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        # 获取当前请求信息用于日志
        request = Request(environ)
        
        
        def cors_start_response(status, headers, exc_info=None):
            # 添加CORS头
            cors_headers = [
                ('Access-Control-Allow-Origin', '*'),  # 允许所有来源
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept'),
                ('Access-Control-Allow-Credentials', 'true'),  # 允许携带凭证
                ('Access-Control-Max-Age', '3600'),  # 预检请求的缓存时间
            ]
            
            # 删除可能存在的CORS头以避免重复
            filtered_headers = [h for h in headers if not h[0].startswith('Access-Control-')]
            # 将CORS头添加到过滤后的headers中
            filtered_headers.extend(cors_headers)
            
            
            return start_response(status, filtered_headers, exc_info)
            
        # 处理OPTIONS预检请求
        if environ['REQUEST_METHOD'] == 'OPTIONS':
            
            response = Response('', status=200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response(environ, start_response)
            
        # 处理其他请求
        return self.app(environ, cors_start_response)

# 打印应用依赖关系


# 创建应用调度中间件
# 将config_app设置为空白路径，确保/api路径正确路由
root_app = Flask('root')

@root_app.route('/')
def welcome():
    return jsonify({
        "message": "AI测试工具后端服务器",
        "status": "running",
        "apis": {
            "configItem": "/api",
            "regression": "/regression/api",
            "projectManagement": "/pm_api"
        }
    })

base_application = DispatcherMiddleware(root_app, {
    '/api': config_app,  # 将config_app映射到/api前缀
    '/regression': regression_app,
    '/pm_api': ASGIMiddleware(pm_app)
})

# 定义一个简单的测试中间件，返回请求路径信息
class RequestDebugMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # 首先处理测试路径
        path_info = environ.get('PATH_INFO', '')
        
        
        # 如果是请求测试路径，返回调试信息
        if path_info == '/debug':
            response = Response(
                json.dumps({
                    'path': path_info,
                    'method': environ.get('REQUEST_METHOD', ''),
                    'environ': {k: str(v) for k, v in environ.items() if isinstance(v, (str, int, float, bool, type(None)))}
                }), 
                mimetype='application/json'
            )
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response(environ, start_response)
            
        # 如果路径以/api/开头，打印详细日志
        if path_info.startswith('/api/'):
            logging.warning(f"请求API路径: {path_info}")
            logging.warning(f"请求方法: {environ.get('REQUEST_METHOD', '')}")
        
        # 其他情况，交给原应用处理
        return self.app(environ, start_response)

# 应用CORS中间件

app_with_cors = CORSMiddleware(base_application)

# 添加调试中间件
application = RequestDebugMiddleware(app_with_cors)

# 打印所有注册的路由
def print_routes():
    import logging
    logging.warning("=== [config_app] 已注册的路由 ===")
    try:
        for rule in config_app.url_map.iter_rules():
            logging.warning(f"  * {rule}")
    except Exception as e:
        logging.warning(f"[config_app] 路由打印失败: {e}")
    logging.warning("=== [regression_app] 已注册的路由 ===")
    try:
        for rule in regression_app.url_map.iter_rules():
            logging.warning(f"  * {rule}")
    except Exception as e:
        logging.warning(f"[regression_app] 路由打印失败: {e}")

    logging.warning("=== DispatcherMiddleware 挂载路径 ===")
    logging.warning("  * /api (config_app)")
    logging.warning("  * /regression (regression_app)")
    logging.warning("  * /pm_api (projectManagement FastAPI app)")


if __name__ == '__main__':
    print_routes()
    # 启动服务
    run_simple('0.0.0.0', 5002, application, use_reloader=True, use_debugger=True)
