# 视觉小说游戏后端 API (TryHard Backend)

## 📖 项目简介

这是一个基于 FastAPI 构建的视觉小说游戏后端 API 系统，支持剧本管理、游戏会话控制和 AI 智能对话功能。该系统为前端 Vue.js 应用提供数据接口，实现了完整的视觉小说游戏体验。

## ✨ 主要功能

- **剧本管理**：支持剧本的创建、查询和详情获取
- **游戏会话**：管理用户游戏进度和状态
- **AI 对话系统**：集成 Dify AI 平台，提供智能对话交互
- **角色管理**：支持多角色剧本和角色信息展示
- **数据持久化**：使用 SQLite 数据库存储游戏数据

## 🛠️ 技术栈

- **后端框架**：FastAPI 0.104.1
- **数据库**：SQLite + SQLAlchemy 2.0.23
- **数据验证**：Pydantic 2.5.0
- **AI 服务**：Dify API 集成
- **服务器**：Uvicorn
- **跨域支持**：CORS 中间件

## 📁 项目结构

```
tryHardbacked/
├── app/                        # 主应用目录
│   ├── core/                   # 核心配置
│   │   └── config.py          # 应用配置文件
│   ├── models/                 # 数据模型
│   │   └── database_models.py # SQLAlchemy 数据库模型
│   ├── schemas/                # 数据模式
│   │   └── pydantic_schemas.py # Pydantic 数据验证模式
│   ├── routers/                # API 路由
│   │   ├── scripts.py         # 剧本相关 API
│   │   ├── game_sessions.py   # 游戏会话 API
│   │   └── ai_dialogue.py     # AI 对话 API
│   ├── services/               # 服务层
│   │   └── dify_service.py    # Dify AI 服务集成
│   ├── database.py            # 数据库连接配置
│   └── main.py                # FastAPI 应用入口
├── create_initial_data.py      # 初始化数据脚本
├── run.py                     # 服务启动脚本
├── requirements.txt           # Python 依赖包
├── game_database.db          # SQLite 数据库文件
└── README.md                 # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd tryHardbacked
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   
   创建 `.env` 文件或设置系统环境变量：
   ```bash
   DIFY_API_URL=https://api.dify.ai/v1/chat-messages
   DIFY_API_KEY=your_dify_api_key_here
   ```

4. **初始化数据库**
   ```bash
   python create_initial_data.py
   ```

5. **启动服务**
   ```bash
   python run.py
   ```

   服务将在 `http://127.0.0.1:8000` 启动

## 📚 API 文档

启动服务后，您可以访问以下地址查看 API 文档：

- **Swagger UI**：http://127.0.0.1:8000/docs
- **ReDoc**：http://127.0.0.1:8000/redoc

### 主要 API 端点

#### 剧本管理
- `GET /api/v1/scripts` - 获取所有剧本列表
- `GET /api/v1/scripts/{script_id}` - 获取特定剧本详情

#### 游戏会话
- `POST /api/v1/game/sessions` - 创建新的游戏会话

#### AI 对话
- `POST /api/v1/ai/dialogue` - 发送对话消息并获取 AI 回复

## 🎮 使用示例

### 创建游戏会话

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/game/sessions" \
     -H "Content-Type: application/json" \
     -d '{
       "script_id": "1",
       "user_id": "user123"
     }'
```

### AI 对话交互

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/dialogue" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "session_xxx",
       "question": "你好，我想了解一下这个剧本"
     }'
```

## 🔧 配置说明

### 数据库配置

项目默认使用 SQLite 数据库，配置在 `app/core/config.py` 中：

```python
DATABASE_URL = "sqlite:///./game_database.db"
```

### AI 服务配置

Dify AI 服务配置需要设置以下环境变量：

- `DIFY_API_URL`：Dify API 端点地址
- `DIFY_API_KEY`：您的 Dify 应用 API 密钥

## 🧪 开发指南

### 添加新的 API 端点

1. 在 `app/routers/` 目录下创建新的路由文件
2. 在 `app/schemas/` 中定义数据模式
3. 在 `app/models/` 中添加数据库模型（如需要）
4. 在 `app/main.py` 中注册新路由

### 数据库迁移

当修改数据库模型时：

1. 更新 `app/models/database_models.py`
2. 重新运行初始化脚本或手动处理数据库变更

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[your-email@example.com]

## 🙏 致谢

感谢 Dify AI 平台提供的智能对话服务支持。
