아래는 **“산식·변수 단위 청킹 기반 Graph-RAG 계리엔진(보험료 산출 근거 자동 해석 시스템)”**을 구현하기 위한 **정식 PRD(Product Requirements Document)** 초안입니다.
— 업로드된 *건강보험가격 산정이론* PDF의 내용도 반영했습니다. 

---

# 📘 **PRD: 보험료 산출 근거 Graph-RAG 계리엔진**

**(Neo4j + LangChain + LangGraph + VLM + MCP 계산엔진 기반)**

---

## 1. **제품 개요 (Overview)**

보험계리 문서는 보험료 산출을 위해 복잡한 **수리적 산식**, **이행률(발생·회복률 등)**, **변수 정의**, **조건부 확률**, **순보험료 공식**, **손해율 공식** 등이 포함된다.
그러나 사람이 문서를 일일이 해석해야 하므로 자동화가 어렵다.

본 시스템은 다음을 목표로 한다:

### 🎯 **목표**

1. **문장 단위로 수식·정의·텍스트를 청킹하여 Neo4j 그래프화**
2. **수식(산식), 변수, 실제 계리 개념을 노드/엣지로 연결**
3. **LangChain + LangGraph 기반 ReAct Agent가 그래프를 탐색하며 해석**
4. **VLM 활용: 이미지 기반 식·표를 읽어 수식 파싱(JSON AST) 생성**
5. **MCP(calculation MCP server)로 실제 산식 평가 가능**
6. **최종적으로 “보험료 산출 근거(Explainable Actuarial Reasoning)” 자동 생성**

---

## 2. **사용자 시나리오 (User Stories)**

### ✔️ **1) 보험계리사가 질의**

> “이 보험상품의 순보험료 산출 근거와 사용된 산식, 변수 정의를 설명해줘.”

→ 에이전트:

* PDF 청킹 → Neo4j 조회
* “순보험료 P = (I/N) × (L/B)” 노드 찾아 그래프 따라가기
* 각 변수 정의(I, N, L, B) 조회
* 예시 숫자를 대입해 계산
* 결과에 대한 설명을 생성

---

### ✔️ **2) 보험사 언더라이터가 질문**

> “다면건강보험료 모델에서 발생률은 어떻게 추정되는가?”

→ 에이전트:

* PDF에서 다면모델 섹션 그래프 검색
* 이행력(transition intensity) 노드들 탐색
* 모델 구조 (Healthy ↔ Sick ↔ Dead) 그래프 생성
* 설명을 자연어로 출력

---

### ✔️ **3) LLM + Neo4j 기반 시뮬레이션 요청**

> “사고발생률 0.01, 사고건당 본인부담 50만원일 경우 순보험료를 계산해줘.”

→ MCP 계산 엔진을 통해 산식 평가

```
P = (I/N) × (L/B)
```

결과값 + 설명 출력

---

## 3. **시스템 구성도 (Architecture)**

### **전체 구성**

```
PDF / Image → VLM → 문장 / 수식 / 표 단위 청킹
                  ↓
           LangChain 파이프라인
                  ↓
  청크 분류(Classify): 정의 / 산식 / 개념 / 표
                  ↓
        노드/엣지 생성 → Neo4j(Graph-RAG)
                  ↓
LangGraph ReAct Agent (Tool-using Agent)
          ↙                  ↘
 Neo4j Cypher Tool     MCP 계산엔진
```

---

## 4. **기능 요구사항 (Functional Requirements)**

---

### ### 4.1 **청킹 + 구조화 기능**

#### 4.1.1 **문장 단위 청킹**

* PDF 문서로부터 문장 단위 split
* 수식은 block-level로 캡처
* 표와 그림은 이미지 형태로 추출

#### 4.1.2 **VLM 기반 수식 파싱**

* 수식/표를 이미지로 읽고 LaTeX 또는 JSON AST 생성
* 예:

  ```
  P = (I/N) × (L/B)
  ⇒ {
     "type": "formula",
     "lhs": "P",
     "rhs": ["I/N", "L/B"],
     "variables": ["I", "N", "L", "B"]
  }
  ```

---

### 4.2 **그래프 스키마 (Neo4j)**

#### **노드 타입**

| 노드         | 설명                    |
| ---------- | --------------------- |
| Formula    | 수식 블록                 |
| Variable   | 변수 정의                 |
| Definition | 개념, 예: 순보험료, 손해율      |
| Concept    | 이론적 개념, 예: 대수의 법칙     |
| Model      | 다면건강보험료 모델, 전통적 순보험료법 |
| Transition | 이행력(λ, μ 등)           |
| Parameter  | 숫자값 또는 예시값            |

#### **엣지 타입**

| 엣지            | 설명                    |
| ------------- | --------------------- |
| DEFINES       | Variable → Definition |
| USED_IN       | Variable → Formula    |
| DERIVES_FROM  | Formula → Formula     |
| PART_OF       | Formula → Model       |
| CAUSES        | Concept → Formula     |
| HAS_PARAMETER | Formula → Parameter   |
| TRANSITION_OF | Transition → Model    |

---

### 4.3 **ReAct 에이전트**

#### 기능

1. 사용자의 질의 의도를 해석
2. 필요한 지식을 Neo4j Cypher로 조회
3. 필요 시 VLM 기반 수식 해석 수행
4. MCP 계산엔진으로 실제 계산
5. “계리적 설명(Actuarial Justification)”을 만든다

#### 도구 (Tools)

| Tool             | 기능            |
| ---------------- | ------------- |
| neo4j_query      | Cypher 쿼리 수행  |
| parse_formula    | VLM을 통해 수식 추출 |
| evaluate_formula | MCP 계산 수행     |
| summarize        | LLM 요약        |

---

### 4.4 **MCP 계산엔진**

#### 요구되는 기능

1. 파싱된 수식을 AST 형태로 받아 계산
2. 예시값 대입 가능
3. 복잡한 계리 모델도 처리 가능

   * 마코프 전이 행렬
   * 상태전이 확률
4. 안전한 샌드박싱 환경

---

## 5. **비기능 요구사항 (NFRs)**

### ▶ 성능

* 200페이지 계리 문서도 30초 내 청킹 가능
* Neo4j 질의 응답 < 1초

### ▶ 정확도

* VLM 수식 파싱 정확도 95% 이상
* 개념 매핑 정확도 90% 이상

### ▶ 확장성

* 손해보험/생명보험 등 PDF마다 새로운 스키마 자동 추가 가능

### ▶ Explainability

* 모든 답변에는 사용한 산식·근거 노드를 링크로 포함

---

## 6. **데이터 파이프라인**

### 1. PDF 로딩

→ pdf2image + OCR + VLM 수식 파싱

### 2. 청킹

→ LangChain TextSplitter (문장 기준 + 수식 기준)

### 3. 청크 분류 (LLM)

→ Definition / Concept / Formula / Transition / Table

### 4. 그래프 변환

→ 자동 Cypher 생성
→ Neo4j insert

### 5. 질의·추론

→ LangGraph ReAct Agent
→ Neo4j 조회 + MCP 계산

---

## 7. **샘플 그래프 모델링 예시**

### **순보험료 공식** 

```
P = (I / N) × (L / B)
```

노드:

* Formula(P1)
* Variable(I), Variable(N), Variable(L), Variable(B)
* Concept("순보험료"), Concept("사고발생률"), Concept("본인부담의료비")

엣지:

* USED_IN(I → P1)
* USED_IN(N → P1)
* DEFINES(“사고건당 본인부담금” → L)
* PART_OF(P1 → “전통적 순보험료법”)

---

## 8. **MVP 범위**

### **포함**

✔ 문장·수식 청킹
✔ Neo4j 저장
✔ 기본 ReAct agent
✔ MCP 계산엔진 기본 공식 처리
✔ 순보험료 계산까지 자동화
✔ 다면건강보험료 모델(Healthy/Sick/Dead) 그래프화

### **제외 (후속 버전)**

✖ 시계열 추정(최대우도법) 자동화
✖ PDF 내 통계표 자동 학습
✖ 국가별 보험계리 표준 기반 모델 자동 추출

---

## 9. **릴리즈 계획**

| 단계 | 내용                       |
| -- | ------------------------ |
| R0 | 문장 단위 청킹 + Neo4j 저장      |
| R1 | 수식 파싱(VLM) + 그래프 연결      |
| R2 | ReAct agent + Neo4j Tool |
| R3 | MCP 계산엔진 + 공식 평가         |
| R4 | 계리설명 자동 생성 (LLM)         |
| R5 | 보험상품별 End-to-End 실험      |

---

## 10. **기대 효과**

### 🔹 **1) 보험계리 문서 자동 이해**

사람이 읽기 힘든 수식을 구조화하여 검색 가능
(Explainable Actuarial AI)

### 🔹 **2) 보험료 산출 근거 자동 생성**

산식 + 변수 + 예시 + 계산 결과를 즉시 제공

### 🔹 **3) Agent 기반 시뮬레이션**

보험료의 민감도 분석까지 가능

### 🔹 **4) Graph-RAG 기반 계리 지식 축적**

보험사 내 계리 지식자산을 그래프로 영구 보관

---

## 11. **결론 요약**

이 PRD는 업로드된 계리 문서 내용을 기반으로:

* **수식·변수·계리 개념을 Neo4j로 그래프화**
* **LangGraph ReAct Agent가 그래프를 탐색**
* **VLM으로 수식 파싱**
* **MCP 계산엔진으로 실제 보험료 계산**
* **최종적으로 계리적 설명을 LLM이 생성**

하는 **보험료 산출 지능형 계리엔진**의 구현 전체 설계를 제시했다.

---

필요하시면
📌 **Neo4j 스키마 Cypher 생성**,
📌 **LangGraph 에이전트 코드**,
📌 **VLM 수식 파서 예시**,
📌 **MCP 계산엔진 파이썬 코드**,
📌 **전체 시스템 아키텍처 다이어그램(SVG)**
까지 이어서 만들어드릴게요.



다음과 같은 결론을 **명확하게** 말씀드릴 수 있습니다:

# ✅ 결론: **네, 필요하다. 그리고 “노드 임베딩 + 관계 임베딩 + 그래프 구조 임베딩”이 모두 필요하다.**

(특히 **보험계리 문서**처럼 *산식·정의·변수·관계*가 얽힌 지식을 정확히 찾으려면 **Graph Embedding 계층**을 반드시 넣는 것이 최선입니다.)

아래에서 왜 필요한지, 어떤 방식이 적합한지, 그리고 실제로 Neo4j에서 어떤 기술을 쓰면 되는지 모두 정리해드립니다.

---

# 1. ✔ 그래프 RAG에서 임베딩이 필요한 이유

보험계리 문서는 다음의 특성을 가집니다:

* **수식 간 의존 관계가 깊다**
  P = (I/N)*(L/B)

* **변수 정의가 문장형이라 검색 비용이 높다**
  I = 보험사고 발생건수
  N = 위험단위수

* **모델 간 계층 구조가 존재한다**
  전통적 순보험료법 → 순보험료 공식 → 변수들

* **결정적 추론(경로 탐색)과 의미적 추론(의미 유사도)이 동시에 필요**

따라서 단순 키워드만으로 필요한 노드를 찾기는 거의 불가능하다.

그래서 “그래프 기반 semantic retrieval”이 필요해진다.

---

# 2. ✔ 필요한 임베딩의 종류 (3계층)

## 2.1 **Node Embedding (노드 임베딩) → 필요함**

각 노드가 가진 텍스트 콘텐츠(정의, 수식 설명, 도메인 설명)를
LLM 임베딩으로 벡터화하면 다음 기능이 가능해진다:

* 의미 기반 검색 (semantic similarity)
* “사고발생률”과 “incidence intensity” 같은 동의 개념 자동 연결
* 영문/국문 구분 없이 의미로 매칭

특히 수학 수식 주변 텍스트를 임베딩하면
"순보험료"라는 질의 → 수식 노드 자동 선택

**기술 예시**
Neo4j Vector Index + OpenAI text-embedding-3-large
or
GraphRAG-style node embeddings

---

## 2.2 **Relation Embedding (관계 임베딩) → 매우 중요함**

보험계리는 **공식이 서로 어떻게 연결되는지**가 핵심이므로
엣지가 단순 연결 정보 이상을 표현해야 한다.

예:

* P **USES** I
* I **DERIVES_FROM** 발생률
* 발생률 **IS_PART_OF** 순보험료 모델

따라서 관계도 임베딩해야 그래프 RAG가 다음을 수행할 수 있다:

* "순보험료의 구성요소?" → 관계 중심 검색
* "어떤 변수가 어떤 산식에 사용되는지?" → 관계 유사도 검색
* "이 현상은 어떤 모델의 일부인가?" → 구조 기반 탐색

**기술 예시**

* Relational Graph Convolutional Network (R-GCN)
* Neo4j Graph Data Science (GDS) → relationship embeddings
* Multi-relational embedding models (TransE, DistMult, RotatE)

---

## 2.3 **Graph Structure Embedding (Holistic Graph Embedding) → 가장 중요**

어떤 노드가 어떤 그래프 구조 안에 있는지가 중요하다.

예:

* “순보험료 공식”은 “전통적 순보험료법”의 children
* “사고건당 본인부담의료비(L/B)”는 “사고심도” 개념과 연결
* “이행력 λ, μ, γ, δ”는 “다면건강보험료 모델” 구조의 일부

그래프 전체 구조를 embedding하면:

* 복잡한 계리 모델을 구조 단위로 검색
* “이민 상태에서 회복까지의 모든 공식” 같은 질의 해결
* 모델의 계층형 설명 자동 생성

**기술 예시**

* GraphSAGE
* GAT (Graph Attention Networks)
* GraphRAG (Microsoft 방식)
* Neo4j GDS FastRP / Node2Vec / GraphSAGE

---

# 3. ✔ 왜 단순 노드 검색으로는 부족한가?

실제로 다음 같은 질문이 들어오면 단순 벡터 검색으로는 절대 안 된다:

> “다면건강보험료 모델에서 회복률 추정식의 근거를 찾아줘.”

이 질문을 해결하려면:

1. 질의 임베딩 →
2. “다면건강보험료”라는 컨텍스트 탐색 →
3. 연결된 “Recover intensity δ(x,z)” 노드 탐색 →
4. 그 노드를 유도하는 “Maximum Likelihood Estimator” 수식 탐색 →
5. 그 수식 주변 텍스트와 변수 정보 필요

이건 **멀티 홉(multi-hop) 추론**이며,
벡터 검색만으로는 절대 되지 않는다.

따라서:

**그래프 구조 + 노드 의미 + 관계 의미 → 3층 embedding이 필수**

---

# 4. ✔ 결국 어떤 임베딩 전략을 채택해야 하나?

아래가 가장 성공률 높은 접근이다:

---

## ⭐ **추천 아키텍처: Neo4j GraphRAG Hybrid Embedding Layer**

### 1) Node Embedding

* Description, Definition, Formula 주변 텍스트를 embedding
* Neo4j vector index 저장

### 2) Relation Embedding (R-GCN)

* 관계유형별 weight 학습
* “USED_IN” vs “DERIVES_FROM” vs “DEFINES” 의미적으로 구분

### 3) Structural Embedding (GraphSAGE or FastRP)

* 그래프 구조 (neighbors, depth, degree)를 반영한 벡터
* GraphSAGE로 노드 전체에 embedding 부여

### 4) Multi-hop Retrieval

* LangGraph agent가 retrieval toolkit을 사용하여

  * semantic search
  * graph traversal
  * relational reasoning
    을 조합

---

# 5. ✔ 요약

| 필요 여부  | 임베딩 종류         | 이유                     |
| ------ | -------------- | ---------------------- |
| 반드시 필요 | **노드 임베딩**     | 의미 기반 검색 (보험 용어/정의 검색) |
| 매우 필요  | **관계 임베딩**     | 변수-공식-모델 간의 의미적 연결 이해  |
| 핵심요소   | **그래프 구조 임베딩** | 계리 모델의 구조적 종속성 파악      |

---

# 6. ✔ 당신이 만들고자 하는 시스템에 적용하면?

### 🔥 결과적으로 다음이 가능해진다:

* “순보험료를 해석해줘”
  → 공식 + 변수 + 사용근거 + 이론을 계층적으로 반환

* “발생률이 순보험료에 미치는 영향 분석해줘”
  → GraphSAGE 기반 multi-hop 추론

* “이행모델에서 λ, μ, δ를 계리적으로 해석해줘”
  → 관계 기반 검색 + 수식 기반 계산

* “PDF에서 산식만 찾아 계산해줘”
  → VLM + formula AST → MCP 계산

---

# 7. ✔ 결론

> **그래프 RAG 기반 계리 엔진에서는 Node Embedding + Relation Embedding + Structural Embedding이 모두 필요하다.**
> (Neo4j GDS + LangChain agent가 가장 현실적인 조합)

---

원하시면 이어서 아래도 만들어드릴 수 있어요:

* Neo4j용 **구체적 embedding schema 코드**
* GDS 기반 **GraphSAGE 학습 파이프라인**
* LangGraph 기반 **GraphRAG Agent 코드**
* Relation Embedding (TransE/RotatE) 적용법
* "계리용 수식 AST → 계산엔진" 설계서

어떤 내용을 더 이어갈까요?
