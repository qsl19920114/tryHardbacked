# 剧本杀游戏核心功能实现指南

## 概述

本文档描述了为中文剧本杀角色扮演游戏实现的两个核心功能：

1. **场景推进（故事模式）** - 视觉小说式的故事推进系统
2. **异步广播对话（调查模式）** - 自由问答系统，支持AI角色记忆同步

## 🏗️ 架构设计

### 数据模型扩展

#### 1. ScriptScene 模型
```python
class ScriptScene(Base):
    __tablename__ = "script_scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=False)
    scene_index = Column(Integer, nullable=False)
    scene_type = Column(Enum(SceneType), nullable=False)  # story | investigation
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    dify_workflow_id = Column(String, nullable=True)
    scene_config = Column(JSON, nullable=True)
```

#### 2. 场景类型枚举
```python
class SceneType(enum.Enum):
    STORY = "story"          # 故事模式 - 视觉小说式推进
    INVESTIGATION = "investigation"  # 调查模式 - 自由问答
```

### 剧本清单系统

#### JSON 配置文件结构
```
data/scripts/{script_id}/scenes.json
```

示例配置：
```json
{
  "script_id": "1",
  "script_title": "午夜图书馆",
  "scenes": [
    {
      "scene_index": 0,
      "scene_type": "story",
      "title": "深夜的图书馆",
      "dify_workflow_id": "story_intro_workflow",
      "scene_config": {
        "characters_present": ["图书管理员"],
        "mood": "mysterious"
      }
    },
    {
      "scene_index": 2,
      "scene_type": "investigation",
      "title": "自由调查阶段",
      "dify_workflow_id": "investigation_workflow",
      "scene_config": {
        "available_characters": [
          {
            "character_id": "librarian_ai",
            "name": "图书管理员AI",
            "dify_workflow_id": "librarian_character_workflow"
          }
        ]
      }
    }
  ]
}
```

## 🎮 功能实现

### 1. 故事模式（Scene Progression）

#### API 端点
```
POST /api/v1/game/sessions/{session_id}/advance
```

#### 请求格式
```json
{
  "session_id": "session_xxx",
  "action": "next"
}
```

#### 响应格式
```json
{
  "session_id": "session_xxx",
  "current_scene_index": 1,
  "scene_content": {
    "scene_id": 1,
    "scene_type": "story",
    "title": "神秘的失踪",
    "content": "AI生成的故事内容...",
    "characters": ["文学教授", "神秘访客"],
    "is_final": false
  },
  "response_time": 0.02,
  "created_at": "2025-07-16T10:30:00Z"
}
```

#### 实现特点
- 自动从剧本清单加载场景配置
- 调用对应的Dify工作流生成动态内容
- 支持故事模式和调查模式的无缝切换
- 将生成内容存储到dialogue_entries表

### 2. 调查模式（Investigation Mode）

#### API 端点
```
POST /api/v1/ai/dialogue
```

#### 请求格式
```json
{
  "session_id": "session_xxx",
  "question": "你知道管理员最后出现在哪里吗？",
  "character_id": "librarian_ai"
}
```

#### 响应格式
```json
{
  "response_id": "resp_xxx",
  "session_id": "session_xxx",
  "question": "你知道管理员最后出现在哪里吗？",
  "answer": "管理员...他昨晚确实表现得很奇怪...",
  "response_time": 0.01,
  "created_at": "2025-07-16T10:30:00Z"
}
```

#### 核心特性

##### 同步响应
- 立即返回目标角色的回答
- 使用唯一conversation_id格式：`{session_id}_{character_id}`
- 支持角色专用的Dify工作流

##### 异步广播
- 使用FastAPI BackgroundTasks
- 将对话内容广播给其他AI角色
- 更新所有角色的记忆状态
- 确保角色间信息同步

## 🔧 服务层架构

### 1. ScriptManifestService
```python
class ScriptManifestService:
    def load_script_manifest(self, script_id: str) -> Dict
    def get_scene_config(self, script_id: str, scene_index: int) -> Dict
    def get_character_workflow_id(self, script_id: str, scene_index: int, character_id: str) -> str
    def get_available_characters(self, script_id: str, scene_index: int) -> List[Dict]
```

### 2. Enhanced DifyService
```python
def call_dify_workflow(workflow_id: str, inputs: Dict, user_id: str, conversation_id: str) -> str
def generate_story_content(workflow_id: str, scene_config: Dict, session_id: str) -> str
def generate_character_response(character_id: str, question: str, scene_context: str) -> str
```

## 🧪 测试系统

### 完整流程测试
```bash
python test_game_flow.py
```

### 调查模式专项测试
```bash
python test_investigation_mode.py
```

### 数据库初始化
```bash
python create_scene_data.py
```

## 📊 技术规格

### 性能指标
- 故事推进响应时间：< 0.1秒
- 角色对话响应时间：< 0.1秒
- 异步广播处理：后台执行，不影响用户体验

### 数据存储
- 所有AI生成内容存储在dialogue_entries表
- 支持完整的对话历史记录
- 角色记忆通过Dify conversation_id维护

### 错误处理
- Dify服务不可用时自动回退到模拟内容
- 完整的异常捕获和日志记录
- 优雅的错误响应

## 🚀 部署说明

### 环境要求
- Python 3.9+
- FastAPI
- SQLAlchemy
- Dify API访问权限

### 启动步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 初始化数据：`python create_initial_data.py && python create_scene_data.py`
3. 启动服务：`python run.py`
4. 运行测试：`python test_game_flow.py`

### 配置说明
- 剧本清单文件：`data/scripts/{script_id}/scenes.json`
- Dify API配置：环境变量 `DIFY_API_URL` 和 `DIFY_API_KEY`
- 数据库：SQLite（可扩展到PostgreSQL）

## 🔮 未来扩展

### Dify集成
- 当前使用模拟数据，可直接替换为真实Dify工作流
- 支持多种工作流类型：故事生成、角色对话、记忆更新

### 功能增强
- 支持更复杂的场景分支逻辑
- 添加角色情感状态跟踪
- 实现多人协作调查模式

### 性能优化
- 实现对话内容缓存
- 优化异步广播性能
- 添加实时通知系统
