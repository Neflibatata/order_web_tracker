# gunicorn.conf.py

# 绑定的IP和端口
bind = "0.0.0.0:5000"

# 工作进程数 - 针对低性能VPS优化
workers = 1  # 使用单进程以减少资源消耗

# 工作模式
worker_class = "gevent"

# 每个工作进程的并发连接数
worker_connections = 50

# 超时设置
timeout = 300  # 5分钟超时
graceful_timeout = 30
keepalive = 2

# 最大请求数
max_requests = 200
max_requests_jitter = 50

# 日志设置
accesslog = "-"  # 输出到stdout
errorlog = "-"   # 输出到stderr
loglevel = "warning"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 进程名称
proc_name = "coach_tracker"

# 预加载应用
preload_app = True

# 工作进程启动前的延迟
worker_ready_ttl = 5

# 限制请求大小（16MB）
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 0

# 优化选项
forwarded_allow_ips = "*"
proxy_allow_ips = "*"

# 错误处理
capture_output = True
enable_stdio_inheritance = True

def on_starting(server):
    """服务启动时的钩子"""
    print("Starting Coach Tracker service...")

def on_exit(server):
    """服务退出时的钩子"""
    print("Shutting down Coach Tracker service...") 