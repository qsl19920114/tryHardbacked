# LangChain Game Engine Architecture

## Overview

This document describes the new LangChain-based game engine architecture for the murder mystery game backend. The new system provides advanced game orchestration, structured state management, and seamless integration with Dify AI workflows.

## Architecture Components

### 1. Core Components

```
app/langchain/
├── __init__.py                 # Package initialization
├── state/                      # Game state management
│   ├── __init__.py
│   ├── models.py              # Pydantic state models
│   └── manager.py             # State persistence layer
├── tools/                      # Dify integration tools
│   ├── __init__.py
│   └── dify_tools.py          # LangChain custom tools
├── engine/                     # Game orchestration engine
│   ├── __init__.py
│   ├── game_engine.py         # Main game engine class
│   ├── graph.py               # LangGraph state graph
│   └── nodes.py               # Game phase node utilities
└── routers/
    └── langchain_game.py       # FastAPI endpoints
```

### 2. State Management Layer

#### GameState Model

The `GameState` model provides comprehensive game state tracking:

```python
class GameState(BaseModel):
    # Core identification
    game_id: str
    script_id: str
    session_id: str

    # Game progression
    current_act: int
    current_phase: GamePhase
    max_acts: int

    # Player and character management
    players: Dict[str, PlayerState]
    characters: Dict[str, CharacterState]
    turn_order: List[str]

    # Game content and history
    public_log: List[PublicLogEntry]
    qna_history: List[QnAEntry]
    mission_submissions: List[MissionSubmission]

    # Game configuration
    max_qna_per_character_per_act: int
    qna_counts: Dict[str, Dict[str, int]]
```

#### Key Features:

- **Structured Data**: Replace generic JSON with validated Pydantic models
- **Business Logic**: Built-in methods for game operations (Q&A counting, turn management)
- **Validation**: Automatic data validation and type checking
- **Serialization**: Seamless conversion to/from database storage

### 3. Dify Integration Tools

#### DifyMonologueTool

Wraps the "简述自己的身世" Dify workflow:

```python
tool = DifyMonologueTool()
result = tool._run(
    char_id="Detective_Holmes",
    act_num=1,
    model_name="gpt-3.5-turbo",
    user_id="player_001"
)
```

#### DifyQnATool

Wraps the "查询并回答" Dify workflow:

```python
tool = DifyQnATool()
result = tool._run(
    char_id="Butler_James",
    act_num=1,
    query="How long have you worked here?",
    model_name="gpt-3.5-turbo",
    user_id="player_001"
)
```

#### Features:

- **Error Handling**: Robust error handling with fallback responses
- **Validation**: Input parameter validation using Pydantic schemas
- **Retry Logic**: Built-in retry mechanism for API failures
- **Logging**: Comprehensive logging for debugging and monitoring

### 4. Game Engine Orchestration

#### LangGraph State Machine

The game flow is managed by a LangGraph state machine with the following phases:

```
INITIALIZATION → MONOLOGUE → QNA ⇄ MISSION_SUBMIT → FINAL_CHOICE → COMPLETED
                     ↑         ↓
                     └─────────┘
```

#### Game Engine Class

The `GameEngine` class serves as the central coordinator:

```python
engine = GameEngine(db_session)

# Start new game
game_state = engine.start_new_game("script_id", "user_id")

# Add players
engine.add_player(session_id, "player_id", "character_id")

# Process actions
result = engine.process_action(session_id, {
    "action_type": "qna",
    "character_id": "Detective_Holmes",
    "question": "What did you see?",
    "questioner_id": "player_001"
})
```

## API Endpoints

### New LangChain Game Endpoints

#### Start New Game

```http
POST /api/v1/langchain-game/start
Content-Type: application/json

{
    "script_id": "mystery_mansion_001",
    "user_id": "user_123"
}
```

#### Join Game

```http
POST /api/v1/langchain-game/session/{session_id}/join
Content-Type: application/json

{
    "player_id": "player_001",
    "character_id": "Detective_Holmes"
}
```

#### Process Action

```http
POST /api/v1/langchain-game/session/{session_id}/action
Content-Type: application/json

{
    "action_type": "qna",
    "character_id": "Butler_James",
    "question": "Where were you last night?",
    "questioner_id": "player_001",
    "model_name": "gpt-3.5-turbo"
}
```

#### Get Game Status

```http
GET /api/v1/langchain-game/session/{session_id}/status?include_history=true&max_log_entries=20
```

## Configuration

### Environment Variables

Add the following environment variables for Dify workflow integration:

```bash
# Dify Workflow API Configuration
DIFY_QNA_WORKFLOW_URL=https://api.dify.ai/v1/workflows/run
DIFY_QNA_WORKFLOW_API_KEY=your_qna_workflow_api_key

DIFY_MONOLOGUE_WORKFLOW_URL=https://api.dify.ai/v1/workflows/run
DIFY_MONOLOGUE_WORKFLOW_API_KEY=your_monologue_workflow_api_key

# LangChain Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=murder-mystery-game

# Game Engine Configuration
MAX_QNA_PER_CHARACTER_PER_ACT=3
MAX_ACTS=3
GAME_SESSION_TIMEOUT_MINUTES=120
```

## Integration with Existing System

### Database Compatibility

The new system maintains full compatibility with the existing database schema:

- Uses existing `GameSession` table for persistence
- Stores complex state in the `game_state` JSON field
- Maintains existing `DialogueEntry` relationships
- No migration required for existing data

### Frontend Compatibility

The new API endpoints are designed to be frontend-friendly:

- RESTful design consistent with existing endpoints
- Comprehensive response objects with all necessary data
- Error handling with clear error messages
- Optional parameters for flexible usage

### Coexistence

Both old and new systems can run simultaneously:

- Old endpoints: `/api/v1/game/*` and `/api/v1/ai/*`
- New endpoints: `/api/v1/langchain-game/*`
- Shared database and script management
- Gradual migration path available

## Benefits of New Architecture

### 1. Structured State Management

- **Before**: Generic JSON field with no validation
- **After**: Strongly-typed Pydantic models with validation

### 2. Advanced Game Logic

- **Before**: Simple dialogue tracking
- **After**: Complete game flow orchestration with phases, turns, and limits

### 3. AI Tool Integration

- **Before**: Single Dify chatflow integration
- **After**: Multiple specialized Dify workflows as LangChain tools

### 4. Scalability

- **Before**: Monolithic dialogue processing
- **After**: Modular, extensible architecture with clear separation of concerns

### 5. Testing and Reliability

- **Before**: Limited testing capabilities
- **After**: Comprehensive unit and integration tests

## Migration Guide

### For Frontend Developers

1. **Gradual Migration**: Start using new endpoints for new features
2. **Enhanced Features**: Leverage structured game state for richer UI
3. **Real-time Updates**: Use game status endpoint for live game state
4. **Error Handling**: Implement proper error handling for new response format

### For Backend Developers

1. **Extend Tools**: Add new Dify workflows as LangChain tools
2. **Custom Phases**: Implement custom game phases in the state graph
3. **Business Logic**: Add game-specific logic to state models
4. **Monitoring**: Use LangSmith for AI tool monitoring and debugging

## Performance Considerations

### State Management

- State is cached in memory during request processing
- Database writes only occur on state changes
- Efficient serialization/deserialization with Pydantic

### AI Tool Calls

- Retry logic with exponential backoff
- Timeout configuration for API calls
- Error fallbacks to maintain game flow

### Database Operations

- Minimal database queries per request
- Efficient JSON storage for complex state
- Indexed session lookups

## Security Considerations

### API Security

- Input validation with Pydantic schemas
- SQL injection prevention through ORM
- Rate limiting recommendations for AI tool calls

### Data Privacy

- User data isolation by session
- Configurable data retention policies
- Audit logging for sensitive operations

## Monitoring and Debugging

### Logging

- Structured logging with correlation IDs
- Different log levels for development and production
- Integration with external logging systems

### Metrics

- Game session metrics (duration, completion rate)
- AI tool performance metrics (latency, error rate)
- Player engagement metrics

### Debugging

- LangSmith integration for AI tool tracing
- Comprehensive error messages with context
- State inspection endpoints for debugging

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
# Test state models
pytest tests/test_state_models.py -v

# Test Dify tools
pytest tests/test_dify_tools.py -v

# Test game engine
pytest tests/test_game_engine.py -v
```

### Integration Tests

Run end-to-end integration tests:

```bash
# Full integration test suite
pytest tests/test_integration.py -v

# Specific test markers
pytest -m "langchain" -v
pytest -m "integration" -v
```

### Test Configuration

Tests use a separate SQLite database and mock Dify API calls for reliability.

## Troubleshooting

### Common Issues

1. **Dify API Connection Errors**

   - Check API keys and URLs in environment variables
   - Verify network connectivity to Dify endpoints
   - Review retry logic and timeout settings

2. **State Serialization Errors**

   - Ensure all custom objects are JSON serializable
   - Check Pydantic model validation rules
   - Review datetime handling in state manager

3. **Game Flow Issues**
   - Verify LangGraph node transitions
   - Check game phase validation logic
   - Review action processing in game engine

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Real-time Multiplayer**: WebSocket support for live game updates
2. **AI Game Master**: Automated game master using advanced AI
3. **Custom Scenarios**: Dynamic scenario generation
4. **Analytics Dashboard**: Game performance and player behavior analytics
5. **Mobile API**: Optimized endpoints for mobile applications

### Extension Points

- Custom game phases in LangGraph
- Additional Dify workflow integrations
- Custom state validation rules
- Plugin system for game mechanics
