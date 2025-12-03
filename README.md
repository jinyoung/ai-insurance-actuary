# 보험계리 Graph-RAG 시스템

Neo4j + LangChain + LangGraph + VLM 기반 보험료 산출 근거 자동 해석 시스템

## 🚀 실행 방법

### 1. Backend 실행 (FastAPI)
```bash
cd /Users/uengine/insumath
PYTHONPATH=. python3 -m uvicorn backend:app --host 0.0.0.0 --port 8000
```

### 2. Frontend 실행 (Vue.js)
```bash
cd /Users/uengine/insumath/frontend
npm run dev
```

### 3. 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📊 시스템 구성

### Backend (FastAPI)
- `/api/query` - Agent에 질의
- `/api/formulas` - 전체 수식 목록
- `/api/recommended-queries` - 추천 질의
- `/api/concepts` - 개념 목록
- `/api/variables` - 변수 목록
- `/api/graph-stats` - 그래프 통계

### Frontend (Vue.js)
- 채팅 인터페이스
- LaTeX 수식 렌더링 (KaTeX)
- 추천 질의 사이드바
- 공식 목록

## 📐 현재 데이터
- **32개 수식** (LaTeX + Python expression)
- **43개 변수** (설명, 단위 포함)
- **10개 개념** (정의 포함)
- **96개 추천 질의** (자동 생성)

## 🛠️ 기술 스택
- **Backend**: FastAPI, LangChain, LangGraph, Neo4j
- **Frontend**: Vue.js 3, Vite, KaTeX
- **AI**: GPT-4o (Agent, VLM, Embeddings)
- **Database**: Neo4j (Graph + Vector)

