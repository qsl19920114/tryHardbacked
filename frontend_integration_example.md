# Frontend Integration Guide for Image Handling

This guide shows how to integrate the new image handling system in your Vue.js frontend application.

## Backend Changes Summary

The backend now automatically generates cover image paths in the format `/static/images/{script_id}.jpg` where `{script_id}` is the database ID of the script.

## Frontend Integration

### 1. API Response Structure

When you call `GET /api/v1/scripts`, the response will include the `cover` field with relative paths:

```json
{
  "scripts": [
    {
      "id": "1",
      "title": "午夜图书馆",
      "cover": "/static/images/1.jpg",
      "category": "Mystery",
      "tags": ["悬疑", "本格", "微恐"],
      "players": "6人 (3男3女)",
      "difficulty": 4,
      "duration": "约4小时",
      "description": "深夜的图书馆中...",
      "author": "神秘作者",
      "characters": [...],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": null
    }
  ],
  "total": 20,
  "page": 1,
  "page_size": 8,
  "total_pages": 3
}
```

### 2. Vue.js Component Implementation

#### Option 1: Using Computed Properties

```vue
<template>
  <div class="script-list">
    <div v-for="script in scripts" :key="script.id" class="script-card">
      <img :src="getFullImageUrl(script.cover)" :alt="script.title" />
      <h3>{{ script.title }}</h3>
      <p>{{ script.description }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScriptList',
  data() {
    return {
      scripts: [],
      backendUrl: 'http://localhost:8000' // Configure this based on your environment
    }
  },
  methods: {
    getFullImageUrl(relativePath) {
      return this.backendUrl + relativePath;
    },
    async fetchScripts() {
      try {
        const response = await fetch(`${this.backendUrl}/api/v1/scripts`);
        const data = await response.json();
        this.scripts = data.scripts;
      } catch (error) {
        console.error('Error fetching scripts:', error);
      }
    }
  },
  mounted() {
    this.fetchScripts();
  }
}
</script>
```

#### Option 2: Using a Global Mixin

Create a mixin file `mixins/imageHelper.js`:

```javascript
export const imageHelperMixin = {
  data() {
    return {
      backendUrl: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8000'
    }
  },
  methods: {
    getFullImageUrl(relativePath) {
      if (!relativePath) return '';
      return this.backendUrl + relativePath;
    }
  }
}
```

Then use it in your components:

```vue
<template>
  <div class="script-card">
    <img :src="getFullImageUrl(script.cover)" :alt="script.title" />
    <h3>{{ script.title }}</h3>
  </div>
</template>

<script>
import { imageHelperMixin } from '@/mixins/imageHelper.js';

export default {
  name: 'ScriptCard',
  mixins: [imageHelperMixin],
  props: {
    script: {
      type: Object,
      required: true
    }
  }
}
</script>
```

#### Option 3: Using Composition API (Vue 3)

```vue
<template>
  <div class="script-list">
    <div v-for="script in scripts" :key="script.id" class="script-card">
      <img :src="getFullImageUrl(script.cover)" :alt="script.title" />
      <h3>{{ script.title }}</h3>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const scripts = ref([]);
const backendUrl = ref(process.env.VUE_APP_BACKEND_URL || 'http://localhost:8000');

const getFullImageUrl = (relativePath) => {
  if (!relativePath) return '';
  return backendUrl.value + relativePath;
};

const fetchScripts = async () => {
  try {
    const response = await fetch(`${backendUrl.value}/api/v1/scripts`);
    const data = await response.json();
    scripts.value = data.scripts;
  } catch (error) {
    console.error('Error fetching scripts:', error);
  }
};

onMounted(() => {
  fetchScripts();
});
</script>
```

### 3. Environment Configuration

Create a `.env` file in your Vue.js project root:

```env
# Development
VUE_APP_BACKEND_URL=http://localhost:8000

# Production (example)
# VUE_APP_BACKEND_URL=https://your-api-domain.com
```

### 4. Error Handling for Missing Images

Add error handling for cases where images might not exist:

```vue
<template>
  <img 
    :src="getFullImageUrl(script.cover)" 
    :alt="script.title"
    @error="handleImageError"
    class="script-cover"
  />
</template>

<script>
export default {
  methods: {
    handleImageError(event) {
      // Set a default placeholder image
      event.target.src = '/placeholder-image.jpg';
      // Or hide the image
      // event.target.style.display = 'none';
    },
    getFullImageUrl(relativePath) {
      if (!relativePath) return '/placeholder-image.jpg';
      return this.backendUrl + relativePath;
    }
  }
}
</script>
```

### 5. Axios Integration (if using Axios)

If you're using Axios for API calls, you can set up a base URL:

```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.VUE_APP_BACKEND_URL || 'http://localhost:8000',
  timeout: 10000,
});

export default apiClient;
```

Then in your component:

```javascript
import apiClient from '@/api/client.js';

export default {
  data() {
    return {
      scripts: []
    }
  },
  methods: {
    getFullImageUrl(relativePath) {
      return apiClient.defaults.baseURL + relativePath;
    },
    async fetchScripts() {
      try {
        const response = await apiClient.get('/api/v1/scripts');
        this.scripts = response.data.scripts;
      } catch (error) {
        console.error('Error fetching scripts:', error);
      }
    }
  }
}
```

## Testing the Integration

1. Start your backend server: `python run.py`
2. Ensure images exist in `app/static/images/` directory (1.jpg, 2.jpg, etc.)
3. Test the API endpoint: `http://localhost:8000/api/v1/scripts`
4. Verify image URLs work: `http://localhost:8000/static/images/1.jpg`
5. Integrate the frontend code and test image display

## Notes

- The backend automatically generates cover paths based on script IDs
- Images should be placed in `app/static/images/` directory with names matching script IDs
- The frontend constructs full URLs by concatenating backend URL + relative path
- Always handle image loading errors gracefully
- Consider using environment variables for different deployment environments
