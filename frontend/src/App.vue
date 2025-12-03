<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">📊</span>
          <h1>보험계리 Graph-RAG</h1>
        </div>
        <div class="stats" v-if="stats">
          <span class="stat-item">📐 {{ stats.Formula || 0 }} 공식</span>
          <span class="stat-item">📝 {{ stats.Variable || 0 }} 변수</span>
          <span class="stat-item">💡 {{ stats.Concept || 0 }} 개념</span>
        </div>
      </div>
    </header>

    <div class="main-container">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-section">
          <h3>🔮 추천 질의</h3>
          <div class="recommended-queries">
            <button 
              v-for="(rq, idx) in recommendedQueries" 
              :key="idx"
              class="query-chip"
              @click="sendQuery(rq.query)"
            >
              {{ rq.query }}
            </button>
          </div>
        </div>

        <div class="sidebar-section">
          <h3>📐 공식 목록</h3>
          <div class="formula-list">
            <div 
              v-for="formula in formulas.slice(0, 10)" 
              :key="formula.id"
              class="formula-item"
              @click="askAboutFormula(formula)"
            >
              <span class="formula-name">{{ formula.name }}</span>
              <span class="formula-page" v-if="formula.source_page">p.{{ formula.source_page }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Chat Area -->
      <main class="chat-area">
        <div class="messages" ref="messagesContainer">
          <!-- Welcome Message -->
          <div class="message assistant" v-if="messages.length === 0">
            <div class="message-content welcome">
              <h2>👋 안녕하세요!</h2>
              <p>보험계리 Graph-RAG 시스템입니다.</p>
              <p>보험료 산출, 수식 조회, 계리적 개념에 대해 질문해 주세요.</p>
              <div class="example-queries">
                <button @click="sendQuery('순보험료 공식을 LaTeX로 보여줘')">순보험료 공식</button>
                <button @click="sendQuery('I=100, N=1000, L=500000, B=10일 때 순보험료 계산')">보험료 계산</button>
                <button @click="sendQuery('이행력 공식들을 알려줘')">이행력 공식</button>
              </div>
            </div>
          </div>

          <!-- Chat Messages -->
          <div 
            v-for="(msg, idx) in messages" 
            :key="idx" 
            :class="['message', msg.role]"
          >
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content" v-html="renderMessage(msg.content)"></div>
          </div>

          <!-- Loading -->
          <div class="message assistant" v-if="loading">
            <div class="message-avatar">🤖</div>
            <div class="message-content loading">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <div class="input-container">
            <textarea 
              v-model="inputQuery"
              @keydown.enter.exact.prevent="sendCurrentQuery"
              placeholder="보험계리에 대해 질문하세요..."
              rows="1"
              ref="inputField"
            ></textarea>
            <button 
              class="send-button" 
              @click="sendCurrentQuery"
              :disabled="!inputQuery.trim() || loading"
            >
              <span>전송</span>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import katex from 'katex'
import { marked } from 'marked'

export default {
  name: 'App',
  data() {
    return {
      messages: [],
      inputQuery: '',
      loading: false,
      formulas: [],
      recommendedQueries: [],
      stats: null
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [formulasRes, queriesRes, statsRes] = await Promise.all([
          axios.get('/api/formulas'),
          axios.get('/api/recommended-queries'),
          axios.get('/api/graph-stats')
        ])
        this.formulas = formulasRes.data
        this.recommendedQueries = queriesRes.data.slice(0, 8)
        this.stats = statsRes.data
      } catch (e) {
        console.error('Failed to load data:', e)
      }
    },

    async sendQuery(query) {
      if (!query.trim()) return

      this.messages.push({ role: 'user', content: query })
      this.inputQuery = ''
      this.loading = true

      this.$nextTick(() => {
        this.scrollToBottom()
      })

      try {
        const response = await axios.post('/api/query', { query })
        this.messages.push({ role: 'assistant', content: response.data.response })
      } catch (e) {
        this.messages.push({ 
          role: 'assistant', 
          content: '⚠️ 오류가 발생했습니다: ' + (e.response?.data?.detail || e.message)
        })
      } finally {
        this.loading = false
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },

    sendCurrentQuery() {
      this.sendQuery(this.inputQuery)
    },

    askAboutFormula(formula) {
      this.sendQuery(`${formula.name}에 대해 설명해줘. LaTeX 수식도 보여줘.`)
    },

    renderMessage(content) {
      // Convert LaTeX delimiters and render
      let html = content

      // Render display math \[...\]
      html = html.replace(/\\\[([\s\S]*?)\\\]/g, (match, tex) => {
        try {
          return `<div class="math-block">${katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false })}</div>`
        } catch (e) {
          return `<code>${tex}</code>`
        }
      })

      // Render inline math \(...\)
      html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, tex) => {
        try {
          return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false })
        } catch (e) {
          return `<code>${tex}</code>`
        }
      })

      // Render $...$ inline math
      html = html.replace(/\$([^\$]+)\$/g, (match, tex) => {
        try {
          return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false })
        } catch (e) {
          return `<code>${tex}</code>`
        }
      })

      // Convert markdown
      html = marked.parse(html)

      return html
    },

    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }
  }
}
</script>

<style>
:root {
  --bg-dark: #0f1419;
  --bg-secondary: #1a1f26;
  --bg-tertiary: #242c37;
  --accent: #00d4aa;
  --accent-dim: #00a888;
  --text-primary: #e8eaed;
  --text-secondary: #9aa0a6;
  --border: #2d3640;
  --user-bubble: #1e4a5f;
  --assistant-bubble: #1f2937;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Header */
.header {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
  border-bottom: 1px solid var(--border);
  padding: 1rem 2rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1600px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  font-size: 1.75rem;
}

.logo h1 {
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(90deg, var(--accent), #00ffcc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* Main Container */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 300px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  padding: 1.5rem;
  overflow-y: auto;
}

.sidebar-section {
  margin-bottom: 2rem;
}

.sidebar-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.recommended-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.query-chip {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.5rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.query-chip:hover {
  background: var(--accent);
  color: var(--bg-dark);
  border-color: var(--accent);
}

.formula-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.formula-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.formula-item:hover {
  background: var(--border);
}

.formula-name {
  font-size: 0.85rem;
  color: var(--text-primary);
}

.formula-page {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg-dark);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  display: flex;
  gap: 1rem;
  max-width: 900px;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.message-content {
  padding: 1rem 1.25rem;
  border-radius: 1rem;
  line-height: 1.6;
}

.message.user .message-content {
  background: var(--user-bubble);
  border-bottom-right-radius: 0.25rem;
}

.message.assistant .message-content {
  background: var(--assistant-bubble);
  border-bottom-left-radius: 0.25rem;
}

.message-content.welcome {
  text-align: center;
  max-width: 500px;
  margin: 2rem auto;
}

.message-content.welcome h2 {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}

.message-content.welcome p {
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.example-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1.5rem;
}

.example-queries button {
  background: var(--accent);
  color: var(--bg-dark);
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.875rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.example-queries button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
}

/* Loading Animation */
.message-content.loading {
  display: flex;
  gap: 0.3rem;
  padding: 1.25rem 1.5rem;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Math Rendering */
.math-block {
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  overflow-x: auto;
  text-align: center;
}

.message-content code {
  background: rgba(0, 0, 0, 0.3);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
}

.message-content pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.message-content pre code {
  background: transparent;
  padding: 0;
}

.message-content ul, .message-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message-content li {
  margin: 0.25rem 0;
}

.message-content strong {
  color: var(--accent);
}

/* Input Area */
.input-area {
  padding: 1.5rem 2rem;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
}

.input-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.input-container textarea {
  flex: 1;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 1.5rem;
  padding: 1rem 1.5rem;
  color: var(--text-primary);
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
}

.input-container textarea:focus {
  border-color: var(--accent);
}

.input-container textarea::placeholder {
  color: var(--text-secondary);
}

.send-button {
  background: var(--accent);
  color: var(--bg-dark);
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.send-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 212, 170, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-button span {
  display: none;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-dark);
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .header-content {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .stats {
    font-size: 0.75rem;
  }
}
</style>

