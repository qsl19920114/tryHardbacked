# Frontend Integration Guide

## Overview

This guide provides examples and best practices for integrating the Vue.js frontend with the new LangChain-based game engine API endpoints.

## API Integration Examples

### 1. Starting a New Game

```javascript
// GameService.js
class GameService {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async startNewGame(scriptId, userId) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/langchain-game/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script_id: scriptId,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        return {
          sessionId: data.data.session_id,
          gameState: data.game_state,
          availableCharacters: data.data.available_characters
        };
      } else {
        throw new Error(data.error || 'Failed to start game');
      }
    } catch (error) {
      console.error('Error starting game:', error);
      throw error;
    }
  }
}
```

### 2. Vue Component for Game Creation

```vue
<!-- GameCreation.vue -->
<template>
  <div class="game-creation">
    <h2>创建新游戏</h2>
    
    <form @submit.prevent="createGame">
      <div class="form-group">
        <label for="script-select">选择剧本:</label>
        <select 
          id="script-select" 
          v-model="selectedScript" 
          required
        >
          <option value="">请选择剧本</option>
          <option 
            v-for="script in scripts" 
            :key="script.id" 
            :value="script.id"
          >
            {{ script.title }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="user-id">用户ID:</label>
        <input 
          id="user-id"
          v-model="userId" 
          type="text" 
          placeholder="输入用户ID"
          required
        />
      </div>

      <button 
        type="submit" 
        :disabled="loading"
        class="create-btn"
      >
        {{ loading ? '创建中...' : '创建游戏' }}
      </button>
    </form>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script>
import { GameService } from '@/services/GameService';

export default {
  name: 'GameCreation',
  data() {
    return {
      selectedScript: '',
      userId: '',
      loading: false,
      error: null,
      scripts: []
    };
  },
  async mounted() {
    await this.loadScripts();
  },
  methods: {
    async loadScripts() {
      try {
        // Use existing script API
        const response = await fetch('/api/v1/scripts');
        const data = await response.json();
        this.scripts = data.scripts;
      } catch (error) {
        console.error('Error loading scripts:', error);
        this.error = '加载剧本失败';
      }
    },

    async createGame() {
      this.loading = true;
      this.error = null;

      try {
        const gameService = new GameService();
        const result = await gameService.startNewGame(
          this.selectedScript, 
          this.userId
        );

        // Navigate to game lobby with session ID
        this.$router.push({
          name: 'GameLobby',
          params: { sessionId: result.sessionId },
          query: { 
            gameId: result.gameState.game_id,
            scriptId: result.gameState.script_id
          }
        });

      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### 3. Player Management

```javascript
// PlayerService.js
class PlayerService {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async joinGame(sessionId, playerId, characterId = null) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/v1/langchain-game/session/${sessionId}/join`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            player_id: playerId,
            character_id: characterId
          })
        }
      );

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to join game');
      }

      return data;
    } catch (error) {
      console.error('Error joining game:', error);
      throw error;
    }
  }

  async getGameStatus(sessionId, includeHistory = true) {
    try {
      const params = new URLSearchParams({
        include_history: includeHistory,
        max_log_entries: 20
      });

      const response = await fetch(
        `${this.baseURL}/api/v1/langchain-game/session/${sessionId}/status?${params}`
      );

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get game status');
      }

      return data;
    } catch (error) {
      console.error('Error getting game status:', error);
      throw error;
    }
  }
}
```

### 4. Game Action Processing

```javascript
// ActionService.js
class ActionService {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async processAction(sessionId, action) {
    try {
      const response = await fetch(
        `${this.baseURL}/api/v1/langchain-game/session/${sessionId}/action`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(action)
        }
      );

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process action');
      }

      return data;
    } catch (error) {
      console.error('Error processing action:', error);
      throw error;
    }
  }

  // Specific action methods
  async askQuestion(sessionId, characterId, question, questionerId) {
    return this.processAction(sessionId, {
      action_type: 'qna',
      character_id: characterId,
      question: question,
      questioner_id: questionerId,
      model_name: 'gpt-3.5-turbo',
      user_id: questionerId
    });
  }

  async requestMonologue(sessionId, characterId, userId) {
    return this.processAction(sessionId, {
      action_type: 'monologue',
      character_id: characterId,
      model_name: 'gpt-3.5-turbo',
      user_id: userId
    });
  }

  async submitMission(sessionId, playerId, missionType, content) {
    return this.processAction(sessionId, {
      action_type: 'mission_submit',
      player_id: playerId,
      mission_type: missionType,
      content: content
    });
  }

  async advancePhase(sessionId, targetPhase) {
    return this.processAction(sessionId, {
      action_type: 'advance_phase',
      target_phase: targetPhase
    });
  }
}
```

### 5. Vue Component for Game Interface

```vue
<!-- GameInterface.vue -->
<template>
  <div class="game-interface">
    <!-- Game Status Header -->
    <div class="game-header">
      <h2>{{ gameState.script_id }}</h2>
      <div class="game-info">
        <span>第{{ gameState.current_act }}幕</span>
        <span>{{ gameState.current_phase }}</span>
        <span>进度: {{ progress.overall_progress }}%</span>
      </div>
    </div>

    <!-- Character Selection -->
    <div class="character-section" v-if="gameState.current_phase === 'monologue'">
      <h3>角色介绍</h3>
      <div class="character-grid">
        <div 
          v-for="character in availableCharacters" 
          :key="character.id"
          class="character-card"
          @click="requestMonologue(character.id)"
        >
          <img :src="character.avatar" :alt="character.name" />
          <h4>{{ character.name }}</h4>
          <p>{{ character.description }}</p>
        </div>
      </div>
    </div>

    <!-- Q&A Section -->
    <div class="qna-section" v-if="gameState.current_phase === 'qna'">
      <h3>问答环节</h3>
      
      <!-- Question Form -->
      <form @submit.prevent="askQuestion" class="question-form">
        <select v-model="selectedCharacter" required>
          <option value="">选择角色</option>
          <option 
            v-for="character in availableCharacters" 
            :key="character.id"
            :value="character.id"
          >
            {{ character.name }}
          </option>
        </select>
        
        <textarea 
          v-model="currentQuestion" 
          placeholder="输入你的问题..."
          required
        ></textarea>
        
        <button type="submit" :disabled="loading">
          {{ loading ? '提问中...' : '提问' }}
        </button>
      </form>

      <!-- Q&A History -->
      <div class="qna-history">
        <div 
          v-for="entry in qnaHistory" 
          :key="entry.id"
          class="qna-entry"
        >
          <div class="question">
            <strong>问:</strong> {{ entry.question }}
          </div>
          <div class="answer">
            <strong>{{ entry.target_character_id }}:</strong> {{ entry.answer }}
          </div>
        </div>
      </div>
    </div>

    <!-- Mission Section -->
    <div class="mission-section">
      <h3>任务提交</h3>
      <form @submit.prevent="submitMission" class="mission-form">
        <select v-model="missionType">
          <option value="evidence">证据</option>
          <option value="accusation">指控</option>
          <option value="theory">推理</option>
        </select>
        
        <textarea 
          v-model="missionContent" 
          placeholder="描述你的发现或推理..."
          required
        ></textarea>
        
        <button type="submit">提交</button>
      </form>
    </div>

    <!-- Public Log -->
    <div class="public-log">
      <h3>游戏日志</h3>
      <div class="log-entries">
        <div 
          v-for="entry in publicLog" 
          :key="entry.id"
          class="log-entry"
        >
          <span class="timestamp">{{ formatTime(entry.timestamp) }}</span>
          <span class="content">{{ entry.content }}</span>
        </div>
      </div>
    </div>

    <!-- Available Actions -->
    <div class="actions-panel">
      <h3>可用操作</h3>
      <button 
        v-for="action in availableActions" 
        :key="action.action_type"
        @click="executeAction(action)"
        class="action-btn"
      >
        {{ action.description }}
      </button>
    </div>
  </div>
</template>

<script>
import { ActionService } from '@/services/ActionService';
import { PlayerService } from '@/services/PlayerService';

export default {
  name: 'GameInterface',
  props: {
    sessionId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      gameState: {},
      progress: {},
      availableActions: [],
      qnaHistory: [],
      publicLog: [],
      availableCharacters: [],
      selectedCharacter: '',
      currentQuestion: '',
      missionType: 'evidence',
      missionContent: '',
      loading: false,
      playerId: 'current_player' // Should come from auth
    };
  },
  async mounted() {
    await this.loadGameStatus();
    // Set up polling for real-time updates
    this.pollInterval = setInterval(this.loadGameStatus, 5000);
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  },
  methods: {
    async loadGameStatus() {
      try {
        const playerService = new PlayerService();
        const status = await playerService.getGameStatus(this.sessionId);
        
        this.gameState = status.game_state;
        this.progress = status.progress;
        this.availableActions = status.available_actions;
        this.qnaHistory = status.qna_history;
        this.publicLog = status.recent_log_entries;
        
        // Extract available characters from game state
        this.availableCharacters = Object.values(this.gameState.characters || {});
        
      } catch (error) {
        console.error('Error loading game status:', error);
      }
    },

    async requestMonologue(characterId) {
      try {
        this.loading = true;
        const actionService = new ActionService();
        
        const result = await actionService.requestMonologue(
          this.sessionId, 
          characterId, 
          this.playerId
        );
        
        if (result.success) {
          await this.loadGameStatus(); // Refresh game state
        }
      } catch (error) {
        console.error('Error requesting monologue:', error);
      } finally {
        this.loading = false;
      }
    },

    async askQuestion() {
      try {
        this.loading = true;
        const actionService = new ActionService();
        
        const result = await actionService.askQuestion(
          this.sessionId,
          this.selectedCharacter,
          this.currentQuestion,
          this.playerId
        );
        
        if (result.success) {
          this.currentQuestion = '';
          this.selectedCharacter = '';
          await this.loadGameStatus(); // Refresh game state
        }
      } catch (error) {
        console.error('Error asking question:', error);
        alert(error.message);
      } finally {
        this.loading = false;
      }
    },

    async submitMission() {
      try {
        const actionService = new ActionService();
        
        const result = await actionService.submitMission(
          this.sessionId,
          this.playerId,
          this.missionType,
          this.missionContent
        );
        
        if (result.success) {
          this.missionContent = '';
          await this.loadGameStatus(); // Refresh game state
        }
      } catch (error) {
        console.error('Error submitting mission:', error);
      }
    },

    async executeAction(action) {
      try {
        const actionService = new ActionService();
        
        if (action.action_type === 'advance_phase') {
          await actionService.advancePhase(this.sessionId, action.target_phase);
        }
        // Add other action types as needed
        
        await this.loadGameStatus(); // Refresh game state
      } catch (error) {
        console.error('Error executing action:', error);
      }
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    }
  }
};
</script>
```

## State Management with Vuex

```javascript
// store/modules/game.js
const state = {
  currentSession: null,
  gameState: {},
  players: [],
  isLoading: false,
  error: null
};

const mutations = {
  SET_CURRENT_SESSION(state, sessionId) {
    state.currentSession = sessionId;
  },
  SET_GAME_STATE(state, gameState) {
    state.gameState = gameState;
  },
  SET_PLAYERS(state, players) {
    state.players = players;
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  }
};

const actions = {
  async startGame({ commit }, { scriptId, userId }) {
    commit('SET_LOADING', true);
    try {
      const gameService = new GameService();
      const result = await gameService.startNewGame(scriptId, userId);
      
      commit('SET_CURRENT_SESSION', result.sessionId);
      commit('SET_GAME_STATE', result.gameState);
      
      return result;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async joinGame({ commit, state }, { playerId, characterId }) {
    if (!state.currentSession) {
      throw new Error('No active game session');
    }

    try {
      const playerService = new PlayerService();
      await playerService.joinGame(state.currentSession, playerId, characterId);
      
      // Refresh game state
      await this.dispatch('game/refreshGameState');
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  async refreshGameState({ commit, state }) {
    if (!state.currentSession) return;

    try {
      const playerService = new PlayerService();
      const status = await playerService.getGameStatus(state.currentSession);
      
      commit('SET_GAME_STATE', status.game_state);
    } catch (error) {
      commit('SET_ERROR', error.message);
    }
  }
};

export default {
  namespaced: true,
  state,
  mutations,
  actions
};
```

## Error Handling Best Practices

```javascript
// utils/errorHandler.js
export class GameError extends Error {
  constructor(message, code, details = {}) {
    super(message);
    this.name = 'GameError';
    this.code = code;
    this.details = details;
  }
}

export function handleApiError(error, context = '') {
  console.error(`API Error in ${context}:`, error);
  
  if (error.response) {
    // HTTP error response
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        throw new GameError(data.detail || 'Invalid request', 'INVALID_REQUEST', data);
      case 404:
        throw new GameError('Game session not found', 'SESSION_NOT_FOUND');
      case 500:
        throw new GameError('Server error occurred', 'SERVER_ERROR');
      default:
        throw new GameError(`HTTP ${status}: ${data.detail || 'Unknown error'}`, 'HTTP_ERROR');
    }
  } else if (error.request) {
    // Network error
    throw new GameError('Network connection failed', 'NETWORK_ERROR');
  } else {
    // Other error
    throw new GameError(error.message || 'Unknown error occurred', 'UNKNOWN_ERROR');
  }
}
```

## Real-time Updates

```javascript
// services/RealtimeService.js
class RealtimeService {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.listeners = new Map();
    this.pollInterval = null;
  }

  startPolling(interval = 3000) {
    if (this.pollInterval) {
      this.stopPolling();
    }

    this.pollInterval = setInterval(async () => {
      try {
        const playerService = new PlayerService();
        const status = await playerService.getGameStatus(this.sessionId);
        
        this.notifyListeners('gameStateUpdate', status);
      } catch (error) {
        this.notifyListeners('error', error);
      }
    }, interval);
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  addEventListener(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  removeEventListener(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  notifyListeners(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in event listener:', error);
        }
      });
    }
  }
}

export default RealtimeService;
```

This integration guide provides comprehensive examples for connecting your Vue.js frontend with the new LangChain game engine, including proper error handling, state management, and real-time updates.
