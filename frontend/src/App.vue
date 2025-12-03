<template>
  <div class="app">
    <div class="bg-gradient"></div>
    
    <!-- Header -->
    <header class="header glass">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon-wrapper">
            <span class="logo-icon">📊</span>
          </div>
          <div class="logo-text">
            <h1>InsuMath</h1>
            <span class="subtitle">Actuarial AI Agent</span>
          </div>
        </div>
        <div class="stats glass-panel" v-if="stats">
          <div class="stat-item" title="수식">
            <span class="stat-icon">📐</span>
            <span class="stat-value">{{ stats.Formula || 0 }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item" title="변수">
            <span class="stat-icon">📝</span>
            <span class="stat-value">{{ stats.Variable || 0 }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item" title="개념">
            <span class="stat-icon">💡</span>
            <span class="stat-value">{{ stats.Concept || 0 }}</span>
          </div>
        </div>
      </div>
    </header>

    <div class="main-container">
      <!-- Sidebar -->
      <aside class="sidebar glass">
        <div class="sidebar-content">
          <div class="section-header">
            <h3>🔮 추천 질의</h3>
            <span class="badge">Auto</span>
          </div>
          <div class="recommended-queries">
            <button 
              v-for="(rq, idx) in recommendedQueries" 
              :key="idx"
              class="query-chip"
              @click="sendQuery(rq.query)"
            >
              <span class="chip-icon">✨</span>
              {{ rq.query }}
            </button>
          </div>

          <div class="divider"></div>

          <div class="section-header">
            <h3>📐 공식 목록</h3>
            <span class="badge">{{ formulas.length }}</span>
          </div>
          <div class="formula-list">
            <div 
              v-for="formula in formulas.slice(0, 15)" 
              :key="formula.id"
              class="formula-item"
              @click="askAboutFormula(formula)"
            >
              <div class="formula-icon">ƒ</div>
              <div class="formula-info">
                <span class="formula-name">{{ formula.name }}</span>
                <span class="formula-meta" v-if="formula.source_page">Page {{ formula.source_page }}</span>
              </div>
              <div class="formula-arrow">→</div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Chat Area -->
      <main class="chat-area">
        <div class="messages" ref="messagesContainer">
          <!-- Welcome Message -->
          <div class="welcome-container" v-if="messages.length === 0">
            <div class="welcome-card glass-panel">
              <div class="welcome-icon">👋</div>
              <h2>보험계리 AI 어시스턴트</h2>
              <p>Neo4j 그래프 지식과 VLM 기술이 결합된<br>지능형 계리 분석 시스템입니다.</p>
              
              <div class="quick-actions">
                <button @click="sendQuery('순보험료 공식을 LaTeX로 보여줘')" class="action-btn">
                  <span class="btn-icon">📐</span> 순보험료 공식
                </button>
                <button @click="sendQuery('I=100, N=1000, L=500000, B=10일 때 순보험료 계산')" class="action-btn">
                  <span class="btn-icon">🧮</span> 예제 계산
                </button>
                <button @click="sendQuery('이행력(Transition Intensity)이란?')" class="action-btn">
                  <span class="btn-icon">📚</span> 개념 설명
                </button>
              </div>
            </div>
          </div>

          <!-- Chat Messages -->
          <transition-group name="message-fade">
            <div 
              v-for="(msg, idx) in messages" 
              :key="idx" 
              :class="['message-wrapper', msg.role]"
            >
              <div class="message-avatar">
                {{ msg.role === 'user' ? '👤' : '🤖' }}
              </div>
              <div class="message-bubble glass-panel" v-html="renderMessage(msg.content)"></div>
            </div>
          </transition-group>

          <!-- Loading -->
          <div class="message-wrapper assistant" v-if="loading">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble glass-panel loading">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area glass">
          <div class="input-wrapper">
            <textarea 
              v-model="inputQuery"
              @keydown.enter.exact.prevent="sendCurrentQuery"
              placeholder="보험계리에 대해 질문하세요... (Enter로 전송)"
              rows="1"
              ref="inputField"
              @input="adjustHeight"
            ></textarea>
            <button 
              class="send-button" 
              @click="sendCurrentQuery"
              :disabled="!inputQuery.trim() || loading"
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import katex from 'katex';
import { marked } from 'marked';

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
        this.recommendedQueries = queriesRes.data.sort(() => 0.5 - Math.random()).slice(0, 6)
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
      this.adjustHeight()

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

    adjustHeight() {
      const el = this.$refs.inputField
      if (el) {
        el.style.height = 'auto'
        el.style.height = Math.min(el.scrollHeight, 120) + 'px'
      }
    },

    renderMessage(content) {
      let html = content

      // Math block
      html = html.replace(/\\\[([\s\S]*?)\\\]/g, (match, tex) => {
        try {
          return `<div class="math-block glass-inner">${katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false })}</div>`
        } catch (e) {
          return `<code>${tex}</code>`
        }
      })

      // Inline math
      html = html.replace(/\\\(([\s\S]*?)\\\)/g, (match, tex) => {
        try {
          return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false })
        } catch (e) {
          return `<code>${tex}</code>`
        }
      })

      // Markdown
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

:root {
  --bg-dark: #09090b;
  --bg-gradient-start: #0f172a;
  --bg-gradient-end: #020617;
  
  --glass-bg: rgba(20, 20, 30, 0.7);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-shine: rgba(255, 255, 255, 0.03);
  
  --primary: #3b82f6;
  --primary-glow: rgba(59, 130, 246, 0.5);
  --accent: #06b6d4;
  
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  
  --success: #10b981;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans KR', 'Inter', sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

.bg-gradient {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 50% -20%, var(--bg-gradient-start), var(--bg-gradient-end));
  z-index: -1;
}

.bg-gradient::after {
  content: '';
  position: absolute;
  top: -20%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.08), transparent 60%);
  border-radius: 50%;
  pointer-events: none;
}

/* Glassmorphism Utilities */
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
}

.glass-panel {
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid var(--glass-border);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.glass-inner {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.5rem;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Header */
.header {
  height: 70px;
  z-index: 100;
  border-bottom: 1px solid var(--glass-border);
}

.header-content {
  max-width: 1800px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon-wrapper {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 15px var(--primary-glow);
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-text h1 {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(to right, #fff, #cbd5e1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.stats {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 99px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.stat-value {
  color: var(--text-primary);
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.stat-divider {
  width: 1px;
  height: 12px;
  background: var(--glass-border);
}

/* Layout */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 340px;
  border-right: 1px solid var(--glass-border);
  display: flex;
  flex-direction: column;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.badge {
  background: rgba(6, 182, 212, 0.1);
  color: var(--accent);
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-weight: 600;
}

.recommended-queries {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.query-chip {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.85rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1.4;
}

.query-chip:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--primary);
  color: var(--text-primary);
  transform: translateX(4px);
}

.chip-icon {
  opacity: 0.7;
}

.divider {
  height: 1px;
  background: var(--glass-border);
  margin: 2rem 0;
}

.formula-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.formula-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.formula-item:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: var(--glass-border);
}

.formula-icon {
  width: 32px;
  height: 32px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Times New Roman', serif;
  font-style: italic;
  font-weight: bold;
}

.formula-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.formula-name {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.formula-meta {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.formula-arrow {
  color: var(--text-tertiary);
  font-size: 0.8rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.formula-item:hover .formula-arrow {
  opacity: 1;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 15%;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  scroll-behavior: smooth;
}

/* Welcome Card */
.welcome-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding-bottom: 4rem;
}

.welcome-card {
  text-align: center;
  padding: 3rem;
  border-radius: 1.5rem;
  max-width: 600px;
  width: 100%;
}

.welcome-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: wave 2s infinite;
  display: inline-block;
  transform-origin: 70% 70%;
}

@keyframes wave {
  0% { transform: rotate( 0.0deg) }
  10% { transform: rotate(14.0deg) }
  20% { transform: rotate(-8.0deg) }
  30% { transform: rotate(14.0deg) }
  40% { transform: rotate(-4.0deg) }
  50% { transform: rotate(10.0deg) }
  60% { transform: rotate( 0.0deg) }
  100% { transform: rotate( 0.0deg) }
}

.welcome-card h2 {
  font-size: 1.75rem;
  margin-bottom: 1rem;
  background: linear-gradient(to right, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.welcome-card p {
  color: var(--text-secondary);
  margin-bottom: 2rem;
  line-height: 1.6;
}

.quick-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  padding: 0.75rem 1.25rem;
  border-radius: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.action-btn:hover {
  background: var(--primary);
  border-color: var(--primary);
  transform: translateY(-3px);
  box-shadow: 0 5px 15px var(--primary-glow);
}

/* Messages */
.message-wrapper {
  display: flex;
  gap: 1.25rem;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.message-wrapper.assistant .message-avatar {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.message-bubble {
  padding: 1.5rem;
  border-radius: 1.25rem;
  line-height: 1.7;
  position: relative;
  min-width: 100px;
}

.message-wrapper.user .message-bubble {
  background: linear-gradient(135deg, var(--primary), #2563eb);
  border: none;
  color: white;
  border-top-right-radius: 0.25rem;
  box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3);
}

.message-wrapper.assistant .message-bubble {
  background: rgba(30, 41, 59, 0.6);
  border-top-left-radius: 0.25rem;
}

/* Markdown & Math Styling */
.message-bubble h1, .message-bubble h2, .message-bubble h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.message-wrapper.user .message-bubble h1, 
.message-wrapper.user .message-bubble h2 {
  color: white;
}

.message-bubble ul, .message-bubble ol {
  padding-left: 1.5rem;
  margin: 0.75rem 0;
}

.message-bubble li {
  margin-bottom: 0.25rem;
}

.message-bubble strong {
  font-weight: 600;
  color: var(--accent);
}

.message-wrapper.user .message-bubble strong {
  color: white;
  text-decoration: underline;
  text-decoration-color: rgba(255, 255, 255, 0.4);
  text-underline-offset: 3px;
}

.math-block {
  margin: 1.5rem 0;
  padding: 1.5rem;
  overflow-x: auto;
  text-align: center;
  font-size: 1.1rem;
  border: 1px solid var(--glass-border);
}

.message-wrapper.user .math-block {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

code {
  font-family: 'JetBrains Mono', monospace;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
  font-size: 0.9em;
}

.message-wrapper.user code {
  background: rgba(255, 255, 255, 0.2);
}

/* Loading Animation */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
  opacity: 0.6;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* Input Area */
.input-area {
  padding: 2rem;
  display: flex;
  justify-content: center;
  position: relative;
  z-index: 10;
  border-top: 1px solid var(--glass-border);
}

.input-wrapper {
  max-width: 900px;
  width: 100%;
  position: relative;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 1.5rem;
  border: 1px solid var(--glass-border);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
}

.input-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
  background: rgba(15, 23, 42, 0.8);
}

textarea {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1rem;
  padding: 1.25rem 4rem 1.25rem 1.5rem;
  resize: none;
  outline: none;
  max-height: 200px;
  font-family: inherit;
  line-height: 1.5;
}

textarea::placeholder {
  color: var(--text-tertiary);
}

.send-button {
  position: absolute;
  right: 0.75rem;
  bottom: 0.75rem;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: none;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.05);
}

.send-button:disabled {
  background: var(--text-tertiary);
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
.message-fade-enter-active, .message-fade-leave-active {
  transition: all 0.4s ease;
}
.message-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.message-fade-leave-to {
  opacity: 0;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Responsive */
@media (max-width: 1024px) {
  .sidebar {
    display: none; /* 추후 모바일 메뉴로 변경 가능 */
  }
  .messages {
    padding: 2rem 1rem;
  }
}
</style>
