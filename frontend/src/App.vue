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
            <h1>AI Actuary</h1>
            <span class="subtitle">Actuarial AI Agent</span>
          </div>
        </div>
        
        <!-- Navigation Tabs -->
        <div class="nav-tabs glass-panel">
          <button 
            :class="['nav-tab', { active: activeTab === 'chat' }]" 
            @click="activeTab = 'chat'"
          >
            <span class="tab-icon">💬</span>
            채팅
          </button>
          <button 
            :class="['nav-tab', { active: activeTab === 'graph' }]" 
            @click="activeTab = 'graph'"
          >
            <span class="tab-icon">🕸️</span>
            그래프 탐색
          </button>
          <button 
            :class="['nav-tab', { active: activeTab === 'ingestion' }]" 
            @click="activeTab = 'ingestion'"
          >
            <span class="tab-icon">📤</span>
            인제스천
          </button>
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
      <aside class="sidebar glass" v-if="activeTab === 'chat'">
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
      <main class="chat-area" v-if="activeTab === 'chat'">
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
              <div class="message-content">
                <div class="message-bubble glass-panel">
                  <!-- Typing indicator when content is empty and loading -->
                  <div v-if="!msg.content && loading && msg.role === 'assistant'" class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <!-- Streaming cursor when content exists and still loading -->
                  <span v-else v-html="renderMessage(msg.content)"></span>
                  <span v-if="msg.content && loading && idx === messages.length - 1 && msg.role === 'assistant'" class="streaming-cursor">▊</span>
                </div>
                <div class="tool-status" v-if="msg.toolStatus">
                  <span class="tool-indicator"></span>
                  {{ msg.toolStatus }}
                </div>
                
                <!-- Tool Call Details (Expandable) -->
                <div class="tool-calls-container" v-if="msg.toolCalls && msg.toolCalls.length > 0">
                  <div 
                    v-for="(tc, tcIdx) in msg.toolCalls" 
                    :key="tcIdx"
                    class="tool-call-item"
                  >
                    <button 
                      class="tool-call-header"
                      @click="tc.expanded = !tc.expanded"
                    >
                      <span class="tool-call-icon">{{ tc.expanded ? '📂' : '📁' }}</span>
                      <span class="tool-call-name">🔧 {{ tc.tool }}</span>
                      <span class="tool-call-toggle">{{ tc.expanded ? '▼' : '▶' }}</span>
                    </button>
                    <transition name="slide-down">
                      <div class="tool-call-details" v-if="tc.expanded">
                        <div class="tool-detail-section" v-if="tc.input">
                          <span class="detail-label">입력:</span>
                          <pre class="detail-content">{{ tc.input }}</pre>
                        </div>
                        <div class="tool-detail-section" v-if="tc.output">
                          <span class="detail-label">결과:</span>
                          <pre class="detail-content">{{ tc.output }}</pre>
                        </div>
                      </div>
                    </transition>
                  </div>
                </div>
              </div>
            </div>
          </transition-group>

          <!-- Loading indicator only when no assistant message exists yet -->
          <div class="message-wrapper assistant" v-if="loading && messages.length > 0 && messages[messages.length - 1].role === 'user'">
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

      <!-- Graph Explorer -->
      <main class="graph-area" v-if="activeTab === 'graph'">
        <GraphExplorer />
      </main>

      <!-- Ingestion Area -->
      <main class="ingestion-area" v-if="activeTab === 'ingestion'">
        <div class="ingestion-container">
          <!-- Upload Section -->
          <div class="upload-section glass-panel">
            <div class="upload-header">
              <h2>📄 PDF 수식 추출</h2>
              <p>보험계리 문서를 업로드하면 AI가 수식을 자동으로 추출하여 그래프 데이터베이스에 저장합니다.</p>
            </div>
            
            <div 
              class="upload-dropzone"
              :class="{ 'drag-over': isDragOver, 'uploading': isUploading }"
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
              @drop.prevent="handleDrop"
              @click="triggerFileInput"
            >
              <input 
                type="file" 
                ref="fileInput" 
                accept=".pdf" 
                @change="handleFileSelect"
                style="display: none"
              />
              
              <div class="dropzone-content" v-if="!isUploading && !currentJob">
                <div class="dropzone-icon">📁</div>
                <p class="dropzone-text">PDF 파일을 드래그하거나 클릭하여 선택</p>
                <p class="dropzone-hint">최대 50MB, PDF 형식만 지원</p>
              </div>
              
              <div class="uploading-content" v-if="isUploading">
                <div class="spinner"></div>
                <p>업로드 중...</p>
              </div>
            </div>
          </div>

          <!-- Current Job Progress -->
          <div class="job-progress glass-panel" v-if="currentJob">
            <div class="job-header">
              <div class="job-info">
                <h3>{{ currentJob.file_name || '처리 중' }}</h3>
                <span :class="['job-status', currentJob.status]">
                  {{ getStatusText(currentJob.status) }}
                </span>
              </div>
              <button class="close-btn" @click="clearCurrentJob" v-if="currentJob.status === 'completed' || currentJob.status === 'failed'">
                ✕
              </button>
            </div>
            
            <div class="progress-bar-container">
              <div class="progress-bar" :style="{ width: currentJob.progress + '%' }"></div>
            </div>
            
            <div class="progress-details">
              <div class="progress-stat">
                <span class="stat-label">페이지</span>
                <span class="stat-value">{{ currentJob.current_page }} / {{ currentJob.total_pages }}</span>
              </div>
              <div class="progress-stat">
                <span class="stat-label">수식 발견</span>
                <span class="stat-value">{{ currentJob.formulas_found }}개</span>
              </div>
              <div class="progress-stat">
                <span class="stat-label">진행률</span>
                <span class="stat-value">{{ Math.round(currentJob.progress) }}%</span>
              </div>
            </div>
            
            <div class="progress-message">
              <span class="message-icon" v-if="currentJob.status === 'processing'">⏳</span>
              <span class="message-icon" v-else-if="currentJob.status === 'completed'">✅</span>
              <span class="message-icon" v-else-if="currentJob.status === 'failed'">❌</span>
              {{ currentJob.message }}
            </div>
          </div>

          <!-- Job History -->
          <div class="job-history glass-panel" v-if="ingestionJobs.length > 0">
            <h3>📋 처리 기록</h3>
            <div class="job-list">
              <div 
                v-for="job in ingestionJobs" 
                :key="job.job_id"
                class="job-item"
              >
                <div class="job-item-icon">
                  <span v-if="job.status === 'completed'">✅</span>
                  <span v-else-if="job.status === 'processing'">⏳</span>
                  <span v-else-if="job.status === 'failed'">❌</span>
                  <span v-else>📄</span>
                </div>
                <div class="job-item-info">
                  <span class="job-filename">{{ job.file_name }}</span>
                  <span class="job-meta">{{ job.formulas_found }}개 수식 • {{ formatDate(job.started_at) }}</span>
                </div>
                <button class="job-delete-btn" @click="deleteJob(job.job_id)" title="삭제">
                  🗑️
                </button>
              </div>
            </div>
          </div>

          <!-- Instructions -->
          <div class="instructions glass-panel">
            <h3>💡 사용 방법</h3>
            <div class="instruction-steps">
              <div class="step">
                <div class="step-number">1</div>
                <div class="step-content">
                  <h4>PDF 업로드</h4>
                  <p>보험계리 관련 PDF 문서를 업로드합니다.</p>
                </div>
              </div>
              <div class="step">
                <div class="step-number">2</div>
                <div class="step-content">
                  <h4>AI 분석</h4>
                  <p>GPT-4 Vision이 각 페이지에서 수식을 자동 추출합니다.</p>
                </div>
              </div>
              <div class="step">
                <div class="step-number">3</div>
                <div class="step-content">
                  <h4>그래프 저장</h4>
                  <p>추출된 수식과 변수가 Neo4j에 저장됩니다.</p>
                </div>
              </div>
              <div class="step">
                <div class="step-number">4</div>
                <div class="step-content">
                  <h4>질의응답</h4>
                  <p>채팅에서 저장된 수식에 대해 질문하세요!</p>
                </div>
              </div>
            </div>
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
import GraphExplorer from './components/GraphExplorer.vue';

export default {
  name: 'App',
  components: {
    GraphExplorer
  },
  data() {
    return {
      activeTab: 'chat',
      messages: [],
      inputQuery: '',
      loading: false,
      formulas: [],
      recommendedQueries: [],
      stats: null,
      // Session management for artifact storage
      sessionId: null,
      // Ingestion
      isDragOver: false,
      isUploading: false,
      currentJob: null,
      ingestionJobs: [],
      pollingInterval: null
    }
  },
  async mounted() {
    await this.loadData()
    await this.loadIngestionJobs()
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
    }
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

    async loadIngestionJobs() {
      try {
        const res = await axios.get('/api/ingestion/jobs')
        this.ingestionJobs = res.data.sort((a, b) => 
          new Date(b.started_at) - new Date(a.started_at)
        )
      } catch (e) {
        console.error('Failed to load ingestion jobs:', e)
      }
    },

    async sendQuery(query) {
      if (!query.trim()) return

      this.messages.push({ role: 'user', content: query })
      this.inputQuery = ''
      this.loading = true
      this.adjustHeight()

      // Add empty assistant message for streaming
      const assistantMsgIndex = this.messages.length
      this.messages.push({ role: 'assistant', content: '', toolStatus: null, toolCalls: [] })
      
      // Track current tool call for pairing input/output
      let currentToolCall = null

      this.$nextTick(() => {
        this.scrollToBottom()
      })

      try {
        // Use fetch for SSE streaming
        const response = await fetch('/api/query/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            query,
            session_id: this.sessionId  // Send session ID for artifact management
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          
          // Parse SSE data
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.type === 'session') {
                  // Store session ID from server
                  this.sessionId = data.session_id
                  console.log('Session ID:', this.sessionId)
                } else if (data.type === 'token') {
                  // Append token to message content
                  this.messages[assistantMsgIndex].content += data.content
                  this.$nextTick(() => this.scrollToBottom())
                } else if (data.type === 'tool_start') {
                  // Show tool execution status
                  this.messages[assistantMsgIndex].toolStatus = `🔧 ${data.tool} 실행 중...`
                  // Create new tool call entry
                  currentToolCall = {
                    tool: data.tool,
                    input: data.input || '',
                    output: '',
                    expanded: false
                  }
                } else if (data.type === 'tool_end') {
                  // Clear tool status and save tool call result
                  this.messages[assistantMsgIndex].toolStatus = null
                  if (currentToolCall) {
                    currentToolCall.output = data.output || ''
                    this.messages[assistantMsgIndex].toolCalls.push(currentToolCall)
                    currentToolCall = null
                  }
                } else if (data.type === 'error') {
                  this.messages[assistantMsgIndex].content += `\n\n⚠️ 오류: ${data.content}`
                } else if (data.type === 'done') {
                  // Streaming complete
                  this.messages[assistantMsgIndex].toolStatus = null
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line)
              }
            }
          }
        }

        // Handle empty response
        if (!this.messages[assistantMsgIndex].content) {
          this.messages[assistantMsgIndex].content = '응답을 생성하지 못했습니다.'
        }
      } catch (e) {
        console.error('Stream error:', e)
        this.messages[assistantMsgIndex].content = '⚠️ 오류가 발생했습니다: ' + e.message
        this.messages[assistantMsgIndex].toolStatus = null
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
    },

    // Ingestion methods
    triggerFileInput() {
      if (!this.isUploading && !this.currentJob) {
        this.$refs.fileInput.click()
      }
    },

    handleDrop(event) {
      this.isDragOver = false
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.uploadFile(files[0])
      }
    },

    handleFileSelect(event) {
      const files = event.target.files
      if (files.length > 0) {
        this.uploadFile(files[0])
      }
    },

    async uploadFile(file) {
      if (!file.name.endsWith('.pdf')) {
        alert('PDF 파일만 업로드할 수 있습니다.')
        return
      }

      if (file.size > 50 * 1024 * 1024) {
        alert('파일 크기는 50MB를 초과할 수 없습니다.')
        return
      }

      this.isUploading = true

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await axios.post('/api/ingestion/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })

        this.currentJob = {
          job_id: response.data.job_id,
          file_name: file.name,
          status: 'pending',
          progress: 0,
          current_page: 0,
          total_pages: 0,
          formulas_found: 0,
          message: '처리 대기 중...'
        }

        this.startPolling(response.data.job_id)
      } catch (e) {
        console.error('Upload failed:', e)
        alert('업로드 실패: ' + (e.response?.data?.detail || e.message))
      } finally {
        this.isUploading = false
        this.$refs.fileInput.value = ''
      }
    },

    startPolling(jobId) {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
      }

      this.pollingInterval = setInterval(async () => {
        try {
          const res = await axios.get(`/api/ingestion/status/${jobId}`)
          this.currentJob = { ...this.currentJob, ...res.data }

          if (res.data.status === 'completed' || res.data.status === 'failed') {
            clearInterval(this.pollingInterval)
            this.pollingInterval = null
            await this.loadIngestionJobs()
            await this.loadData() // Refresh stats and formulas
          }
        } catch (e) {
          console.error('Polling error:', e)
        }
      }, 1000)
    },

    clearCurrentJob() {
      this.currentJob = null
    },

    async deleteJob(jobId) {
      if (!confirm('이 작업 기록을 삭제하시겠습니까?')) return

      try {
        await axios.delete(`/api/ingestion/job/${jobId}`)
        await this.loadIngestionJobs()
      } catch (e) {
        console.error('Delete failed:', e)
      }
    },

    getStatusText(status) {
      const texts = {
        pending: '대기 중',
        processing: '처리 중',
        completed: '완료',
        failed: '실패'
      }
      return texts[status] || status
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('ko-KR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
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
  --accent-glow: rgba(6, 182, 212, 0.5);
  
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
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

/* Navigation Tabs */
.nav-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.35rem;
  border-radius: 12px;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-tab:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.nav-tab.active {
  background: var(--primary);
  color: white;
  box-shadow: 0 2px 10px var(--primary-glow);
}

.tab-icon {
  font-size: 1.1rem;
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

.message-content {
  flex: 1;
  min-width: 0;
}

/* Tool Status Indicator */
.tool-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 0.75rem;
  font-size: 0.85rem;
  color: var(--primary);
  animation: pulse 2s infinite;
}

.tool-indicator {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Streaming cursor */
.streaming-cursor {
  display: inline-block;
  color: var(--primary);
  animation: cursorBlink 0.8s infinite;
  margin-left: 2px;
  font-weight: normal;
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
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

/* ============== ENHANCED TABLE STYLES ============== */
.message-bubble table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 1.5rem 0;
  font-size: 0.9rem;
  background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8));
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.2),
    0 2px 4px -1px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.message-bubble thead {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.15));
}

.message-bubble th {
  padding: 1rem 1.25rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

.message-bubble th:first-child {
  border-top-left-radius: 1rem;
}

.message-bubble th:last-child {
  border-top-right-radius: 1rem;
}

.message-bubble td {
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  transition: background 0.2s ease;
}

.message-bubble tbody tr {
  transition: all 0.2s ease;
}

.message-bubble tbody tr:hover {
  background: rgba(59, 130, 246, 0.08);
}

.message-bubble tbody tr:hover td {
  color: #fff;
}

.message-bubble tbody tr:last-child td {
  border-bottom: none;
}

.message-bubble tbody tr:last-child td:first-child {
  border-bottom-left-radius: 1rem;
}

.message-bubble tbody tr:last-child td:last-child {
  border-bottom-right-radius: 1rem;
}

/* Alternate row colors */
.message-bubble tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02);
}

.message-bubble tbody tr:nth-child(odd) {
  background: transparent;
}

/* Number columns - right align */
.message-bubble td:nth-child(n+3) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
}

/* First column styling */
.message-bubble td:first-child {
  font-weight: 500;
  color: var(--text-primary);
}

/* Table wrapper for horizontal scroll */
.message-bubble .table-wrapper {
  overflow-x: auto;
  margin: 1rem 0;
  border-radius: 1rem;
}

/* Responsive table */
@media (max-width: 768px) {
  .message-bubble table {
    font-size: 0.8rem;
  }
  
  .message-bubble th,
  .message-bubble td {
    padding: 0.625rem 0.875rem;
  }
}

/* User message table (lighter colors) */
.message-wrapper.user .message-bubble table {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.message-wrapper.user .message-bubble thead {
  background: rgba(255, 255, 255, 0.15);
}

.message-wrapper.user .message-bubble th {
  color: rgba(255, 255, 255, 0.95);
}

.message-wrapper.user .message-bubble td {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

.message-wrapper.user .message-bubble tbody tr:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* ============== BLOCKQUOTE STYLES ============== */
.message-bubble blockquote {
  margin: 1.25rem 0;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(59, 130, 246, 0.08));
  border-left: 4px solid var(--accent);
  border-radius: 0 0.75rem 0.75rem 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.message-bubble blockquote p {
  margin: 0;
}

.message-wrapper.user .message-bubble blockquote {
  background: rgba(255, 255, 255, 0.1);
  border-left-color: rgba(255, 255, 255, 0.5);
  color: rgba(255, 255, 255, 0.9);
}

/* ============== PRE/CODE BLOCK STYLES ============== */
.message-bubble pre {
  margin: 1rem 0;
  padding: 1.25rem;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow-x: auto;
}

.message-bubble pre code {
  padding: 0;
  background: transparent;
  font-size: 0.85rem;
  line-height: 1.6;
}

/* ============== TOOL CALLS EXPANDABLE SECTION ============== */
.tool-calls-container {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-call-item {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.75rem;
  overflow: hidden;
}

.tool-call-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.tool-call-header:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--text-primary);
}

.tool-call-icon {
  font-size: 1rem;
}

.tool-call-name {
  flex: 1;
  font-weight: 500;
  font-family: 'JetBrains Mono', monospace;
}

.tool-call-toggle {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  transition: transform 0.2s ease;
}

.tool-call-details {
  padding: 0 1rem 1rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tool-detail-section {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.detail-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
}

.detail-content {
  margin: 0;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

/* Slide down animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 500px;
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

/* ============== GRAPH EXPLORER STYLES ============== */

.graph-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ============== INGESTION STYLES ============== */

.ingestion-area {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.ingestion-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Upload Section */
.upload-section {
  border-radius: 1.5rem;
  padding: 2rem;
}

.upload-header {
  text-align: center;
  margin-bottom: 2rem;
}

.upload-header h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(to right, var(--primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.upload-header p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.upload-dropzone {
  border: 2px dashed var(--glass-border);
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-dropzone:hover {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.05);
}

.upload-dropzone.drag-over {
  border-color: var(--accent);
  background: rgba(6, 182, 212, 0.1);
  transform: scale(1.02);
}

.upload-dropzone.uploading {
  pointer-events: none;
  opacity: 0.7;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.dropzone-icon {
  font-size: 3rem;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.dropzone-text {
  font-size: 1.1rem;
  color: var(--text-primary);
}

.dropzone-hint {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.uploading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--glass-border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Job Progress */
.job-progress {
  border-radius: 1.5rem;
  padding: 1.5rem;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.job-info h3 {
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.job-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  font-weight: 600;
}

.job-status.pending {
  background: rgba(148, 163, 184, 0.2);
  color: var(--text-secondary);
}

.job-status.processing {
  background: rgba(59, 130, 246, 0.2);
  color: var(--primary);
}

.job-status.completed {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);
}

.job-status.failed {
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0.5rem;
  font-size: 1rem;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.progress-bar-container {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px var(--primary-glow);
}

.progress-details {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1rem;
}

.progress-stat {
  text-align: center;
}

.progress-stat .stat-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
}

.progress-stat .stat-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.progress-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.75rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.message-icon {
  font-size: 1.2rem;
}

/* Job History */
.job-history {
  border-radius: 1.5rem;
  padding: 1.5rem;
}

.job-history h3 {
  font-size: 1rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.job-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0.75rem;
  transition: background 0.2s;
}

.job-item:hover {
  background: rgba(0, 0, 0, 0.3);
}

.job-item-icon {
  font-size: 1.5rem;
}

.job-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.job-filename {
  font-size: 0.95rem;
  color: var(--text-primary);
}

.job-meta {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.job-delete-btn {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.job-delete-btn:hover {
  opacity: 1;
}

/* Instructions */
.instructions {
  border-radius: 1.5rem;
  padding: 2rem;
}

.instructions h3 {
  font-size: 1rem;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.instruction-steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.step {
  display: flex;
  gap: 1rem;
}

.step-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
  color: var(--text-primary);
}

.step-content p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
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
    display: none;
  }
  .messages {
    padding: 2rem 1rem;
  }
  .instruction-steps {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 1rem;
  }
  .nav-tabs {
    display: none;
  }
  .stats {
    display: none;
  }
}
</style>
