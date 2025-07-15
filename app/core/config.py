import os

# Dify AI API 配置
# Dify API 接口地址，用于调用 AI 对话服务
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/chat-messages")
# Dify API 密钥，需要从环境变量中获取
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "YOUR_DIFY_APP_API_KEY")

# 数据库配置
# SQLite 数据库连接字符串，数据库文件存储在项目根目录
DATABASE_URL = "sqlite:///./game_database.db"