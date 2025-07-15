import os

# Dify API 配置
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1/chat-messages")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "YOUR_DIFY_APP_API_KEY")

# 数据库配置
DATABASE_URL = "sqlite:///./game_database.db"