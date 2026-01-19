"""
FastAPI Backend for Actuarial Graph-RAG Agent
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import json
import asyncio
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import run_agent, run_agent_stream, set_session_id, get_session_id
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY
from neo4j import GraphDatabase

app = FastAPI(title="Actuarial Graph-RAG API", version="1.0.0")

# Store ingestion jobs status
ingestion_jobs: Dict[str, Dict[str, Any]] = {}

# CORS for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Optional session ID for artifact management

class QueryResponse(BaseModel):
    query: str
    response: str
    success: bool
    session_id: str  # Return the session ID used

class Formula(BaseModel):
    id: str
    name: str
    latex: Optional[str]
    expression: Optional[str]
    description: Optional[str]
    source_page: Optional[int]
    recommended_queries: Optional[List[str]]

class RecommendedQuery(BaseModel):
    query: str
    category: str
    formula_id: Optional[str]

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Actuarial Graph-RAG API", "status": "running"}

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Send a query to the actuarial agent."""
    try:
        # Set or generate session ID
        if request.session_id:
            set_session_id(request.session_id)
        session_id = get_session_id()
        
        response = run_agent(request.query)
        return QueryResponse(
            query=request.query,
            response=response,
            success=True,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream")
async def query_agent_stream(request: QueryRequest):
    """Stream the agent's response using Server-Sent Events (SSE)."""
    
    # Set or generate session ID before streaming starts
    if request.session_id:
        set_session_id(request.session_id)
    session_id = get_session_id()
    
    async def event_generator():
        try:
            # Send session ID as first event
            session_data = json.dumps({"type": "session", "session_id": session_id}, ensure_ascii=False)
            yield f"data: {session_data}\n\n"
            
            async for chunk in run_agent_stream(request.query):
                # Format as SSE
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.get("/api/formulas", response_model=List[Formula])
async def get_formulas():
    """Get all formulas from the graph."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (f:Formula)
                RETURN f.id AS id, f.name AS name, f.latex AS latex,
                       f.expression AS expression, f.description AS description,
                       f.source_page AS source_page,
                       f.recommended_queries AS recommended_queries
                ORDER BY f.source_page, f.id
            """)
            formulas = []
            for record in result:
                formulas.append(Formula(
                    id=record["id"] or "",
                    name=record["name"] or "",
                    latex=record["latex"],
                    expression=record["expression"],
                    description=record["description"],
                    source_page=record["source_page"],
                    recommended_queries=record["recommended_queries"]
                ))
            return formulas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommended-queries", response_model=List[RecommendedQuery])
async def get_recommended_queries():
    """Get recommended queries from all formulas."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (f:Formula)
                WHERE f.recommended_queries IS NOT NULL
                RETURN f.id AS formula_id, f.name AS name, f.recommended_queries AS queries
            """)
            recommended = []
            for record in result:
                queries = record["queries"] or []
                for q in queries:
                    recommended.append(RecommendedQuery(
                        query=q,
                        category=record["name"] or "일반",
                        formula_id=record["formula_id"]
                    ))
            
            # Add some default queries if none exist
            if not recommended:
                defaults = [
                    ("순보험료를 계산하는 공식을 알려줘", "순보험료"),
                    ("I=100, N=1000, L=500000, B=10일 때 순보험료는?", "계산"),
                    ("사고발생률이 뭐야?", "개념"),
                    ("영업보험료의 구성요소는?", "개념"),
                    ("최대우도 추정량 공식을 찾아줘", "MLE"),
                    ("이행력 공식들을 보여줘", "다면모델"),
                    ("손해율 계산 방법은?", "손해율"),
                ]
                for q, cat in defaults:
                    recommended.append(RecommendedQuery(query=q, category=cat, formula_id=None))
            
            return recommended
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/concepts")
async def get_concepts():
    """Get all concepts from the graph."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Concept)
                OPTIONAL MATCH (c)-[:DEFINES]->(d:Definition)
                RETURN c.name AS name, d.text AS definition
                ORDER BY c.name
            """)
            concepts = []
            for record in result:
                concepts.append({
                    "name": record["name"],
                    "definition": record["definition"]
                })
            return concepts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/variables")
async def get_variables():
    """Get all variables from the graph."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (v:Variable)
                OPTIONAL MATCH (v)-[:USED_IN]->(f:Formula)
                RETURN v.name AS name, v.latex AS latex, v.description AS description,
                       v.unit AS unit, collect(f.name) AS used_in_formulas
                ORDER BY v.name
            """)
            variables = []
            for record in result:
                variables.append({
                    "name": record["name"],
                    "latex": record["latex"],
                    "description": record["description"],
                    "unit": record["unit"],
                    "used_in_formulas": record["used_in_formulas"]
                })
            return variables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph-stats")
async def get_graph_stats():
    """Get graph statistics."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                ORDER BY count DESC
            """)
            stats = {}
            for record in result:
                stats[record["label"]] = record["count"]
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== INGESTION API ==============

class IngestionStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0-100
    current_page: int
    total_pages: int
    formulas_found: int
    message: str
    started_at: Optional[str]
    completed_at: Optional[str]

@app.post("/api/ingestion/upload")
async def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF file and start ingestion process."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    file_path = f"uploads/{job_id}_{file.filename}"
    
    # Save uploaded file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Initialize job status
    ingestion_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "current_page": 0,
        "total_pages": 0,
        "formulas_found": 0,
        "message": "파일 업로드 완료. 처리 대기 중...",
        "file_path": file_path,
        "file_name": file.filename,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "formulas": []
    }
    
    # Start background processing
    background_tasks.add_task(process_pdf_ingestion, job_id, file_path)
    
    return {"job_id": job_id, "message": "PDF 업로드 완료. 인제스천 시작됨."}

async def process_pdf_ingestion(job_id: str, file_path: str):
    """Background task to process PDF ingestion."""
    import fitz  # PyMuPDF
    from PIL import Image
    import io
    from openai import OpenAI
    
    job = ingestion_jobs[job_id]
    job["status"] = "processing"
    job["message"] = "PDF 분석 시작..."
    
    try:
        # Open PDF
        doc = fitz.open(file_path)
        total_pages = len(doc)
        job["total_pages"] = total_pages
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        all_formulas = []
        
        for i in range(total_pages):
            job["current_page"] = i + 1
            job["progress"] = ((i + 1) / total_pages) * 100
            job["message"] = f"페이지 {i + 1}/{total_pages} 처리 중..."
            
            # Convert page to image
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=200)
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Extract formulas using VLM
            formulas = await extract_formulas_vlm(client, image, i + 1)
            
            for f in formulas:
                f["source_page"] = i + 1
                all_formulas.append(f)
            
            job["formulas_found"] = len(all_formulas)
            job["formulas"] = all_formulas
            
            # Small delay to prevent rate limiting
            await asyncio.sleep(0.5)
        
        doc.close()
        
        # Insert into Neo4j
        job["message"] = "Neo4j 그래프에 수식 삽입 중..."
        inserted = await insert_formulas_to_neo4j(all_formulas)
        
        job["status"] = "completed"
        job["progress"] = 100
        job["message"] = f"완료! {len(all_formulas)}개 수식 추출, {inserted}개 삽입됨"
        job["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        job["status"] = "failed"
        job["message"] = f"오류 발생: {str(e)}"
        import traceback
        traceback.print_exc()

async def extract_formulas_vlm(client, image, page_num):
    """Extract formulas from image using GPT-4 Vision."""
    import base64
    import io
    
    # Encode image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    prompt = """이 이미지에서 모든 수학 공식/수식을 찾아 추출하세요.

각 공식에 대해 다음 JSON 형식으로 반환하세요:
{
  "formulas": [
    {
      "name": "공식 이름 (한글)",
      "latex": "LaTeX 수식 표현",
      "expression": "Python으로 계산 가능한 표현식",
      "description": "공식에 대한 설명",
      "variables": [
        {"name": "변수명", "latex": "LaTeX 변수", "description": "변수 설명", "unit": "단위"}
      ]
    }
  ]
}

수식이 없으면 {"formulas": []} 반환. 반드시 유효한 JSON만 반환하세요."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=4096
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content.strip())
        return result.get("formulas", [])
    except Exception as e:
        print(f"Error extracting formulas from page {page_num}: {e}")
        return []

async def insert_formulas_to_neo4j(formulas):
    """Insert formulas into Neo4j graph."""
    from openai import OpenAI
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    inserted = 0
    
    with driver.session() as session:
        for i, formula in enumerate(formulas):
            if not formula.get("latex") and not formula.get("expression"):
                continue
            
            formula_id = f"F_auto_{datetime.now().strftime('%Y%m%d')}_{i+1}"
            name = formula.get("name", f"공식 {i+1}")
            latex = formula.get("latex", "")
            expression = formula.get("expression", "")
            description = formula.get("description", "")
            source_page = formula.get("source_page", 0)
            
            # Check for duplicates
            check = session.run("""
                MATCH (f:Formula) WHERE f.latex = $latex RETURN f
            """, latex=latex)
            if check.single():
                continue
            
            # Create embedding
            embed_text = f"{name}: {description} LaTeX: {latex}"[:8000]
            try:
                response = client.embeddings.create(
                    input=[embed_text.replace("\n", " ")],
                    model="text-embedding-3-small"
                )
                embedding = response.data[0].embedding
            except:
                embedding = None
            
            # Insert formula
            if embedding:
                session.run("""
                    MERGE (f:Formula {id: $id})
                    SET f.name = $name,
                        f.latex = $latex,
                        f.expression = $expression,
                        f.description = $description,
                        f.source_page = $source_page,
                        f.embedding = $embedding
                """, id=formula_id, name=name, latex=latex,
                    expression=expression, description=description,
                    source_page=source_page, embedding=embedding)
            else:
                session.run("""
                    MERGE (f:Formula {id: $id})
                    SET f.name = $name,
                        f.latex = $latex,
                        f.expression = $expression,
                        f.description = $description,
                        f.source_page = $source_page
                """, id=formula_id, name=name, latex=latex,
                    expression=expression, description=description,
                    source_page=source_page)
            
            inserted += 1
            
            # Insert variables
            for var in formula.get("variables", []):
                var_name = var.get("name", "")
                if not var_name:
                    continue
                
                session.run("""
                    MERGE (v:Variable {name: $name})
                    ON CREATE SET v.latex = $latex,
                                  v.description = $description,
                                  v.unit = $unit
                """, name=var_name, latex=var.get("latex", var_name),
                    description=var.get("description", ""), unit=var.get("unit", ""))
                
                session.run("""
                    MATCH (v:Variable {name: $var_name})
                    MATCH (f:Formula {id: $formula_id})
                    MERGE (v)-[:USED_IN]->(f)
                """, var_name=var_name, formula_id=formula_id)
    
    driver.close()
    return inserted

@app.get("/api/ingestion/status/{job_id}", response_model=IngestionStatus)
async def get_ingestion_status(job_id: str):
    """Get the status of an ingestion job."""
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = ingestion_jobs[job_id]
    return IngestionStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        current_page=job["current_page"],
        total_pages=job["total_pages"],
        formulas_found=job["formulas_found"],
        message=job["message"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at")
    )

@app.get("/api/ingestion/jobs")
async def list_ingestion_jobs():
    """List all ingestion jobs."""
    return [
        {
            "job_id": job["job_id"],
            "status": job["status"],
            "file_name": job.get("file_name", ""),
            "formulas_found": job["formulas_found"],
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at")
        }
        for job in ingestion_jobs.values()
    ]

@app.delete("/api/ingestion/job/{job_id}")
async def delete_ingestion_job(job_id: str):
    """Delete an ingestion job."""
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = ingestion_jobs[job_id]
    
    # Delete uploaded file
    if os.path.exists(job.get("file_path", "")):
        os.remove(job["file_path"])
    
    del ingestion_jobs[job_id]
    return {"message": "Job deleted"}


# ============== GRAPH EXPLORER API ==============

class NodeData(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class RelationshipData(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    type: str
    properties: Optional[Dict[str, Any]] = {}

class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

class NodeUpdate(BaseModel):
    properties: Dict[str, Any]

class CreateNodeRequest(BaseModel):
    label: str
    properties: Dict[str, Any]

class CreateRelationshipRequest(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: Optional[Dict[str, Any]] = {}


@app.get("/api/graph/data")
async def get_graph_data(limit: int = 200):
    """Get full graph data for NVL visualization."""
    try:
        with driver.session() as session:
            # Get all nodes with their labels and properties
            nodes_result = session.run("""
                MATCH (n)
                WHERE NOT n:_GraphConfig
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
                LIMIT $limit
            """, limit=limit)
            
            nodes = []
            for record in nodes_result:
                node_id = record["id"]
                labels = record["labels"]
                props = dict(record["properties"])
                
                # Remove embedding from properties (too large)
                if "embedding" in props:
                    del props["embedding"]
                
                nodes.append({
                    "id": node_id,
                    "labels": labels,
                    "properties": props,
                    "caption": props.get("name") or props.get("id") or props.get("text", "")[:50] or labels[0] if labels else "Node"
                })
            
            # Get all relationships
            rels_result = session.run("""
                MATCH (a)-[r]->(b)
                WHERE NOT a:_GraphConfig AND NOT b:_GraphConfig
                RETURN elementId(r) AS id, elementId(a) AS source, elementId(b) AS target, 
                       type(r) AS type, properties(r) AS properties
                LIMIT $limit
            """, limit=limit * 2)
            
            relationships = []
            for record in rels_result:
                relationships.append({
                    "id": record["id"],
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                    "properties": dict(record["properties"]) if record["properties"] else {}
                })
            
            return {"nodes": nodes, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/node/{node_id}")
async def get_node_detail(node_id: str):
    """Get detailed information about a specific node."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE elementId(n) = $node_id
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN n, labels(n) AS labels, properties(n) AS properties,
                       collect(DISTINCT {
                           relationship: type(r),
                           direction: CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END,
                           connectedNode: elementId(connected),
                           connectedLabels: labels(connected),
                           connectedCaption: COALESCE(connected.name, connected.id, connected.text)
                       }) AS connections
            """, node_id=node_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Node not found")
            
            props = dict(record["properties"])
            if "embedding" in props:
                del props["embedding"]
            
            return {
                "id": node_id,
                "labels": record["labels"],
                "properties": props,
                "connections": [c for c in record["connections"] if c["connectedNode"]]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/graph/node/{node_id}")
async def update_node(node_id: str, update: NodeUpdate):
    """Update a node's properties."""
    try:
        with driver.session() as session:
            # Build dynamic SET clause
            set_parts = []
            params = {"node_id": node_id}
            
            for key, value in update.properties.items():
                if key not in ["embedding"]:  # Skip embedding
                    safe_key = key.replace(" ", "_").replace("-", "_")
                    set_parts.append(f"n.{safe_key} = ${safe_key}")
                    params[safe_key] = value
            
            if not set_parts:
                raise HTTPException(status_code=400, detail="No valid properties to update")
            
            query = f"""
                MATCH (n)
                WHERE elementId(n) = $node_id
                SET {', '.join(set_parts)}
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Node not found")
            
            props = dict(record["properties"])
            if "embedding" in props:
                del props["embedding"]
            
            return {
                "id": record["id"],
                "labels": record["labels"],
                "properties": props,
                "message": "Node updated successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/node")
async def create_node(request: CreateNodeRequest):
    """Create a new node."""
    try:
        with driver.session() as session:
            # Build properties
            props_parts = []
            params = {}
            
            for key, value in request.properties.items():
                if key not in ["embedding"]:
                    safe_key = key.replace(" ", "_").replace("-", "_")
                    props_parts.append(f"{safe_key}: ${safe_key}")
                    params[safe_key] = value
            
            # Create node with label
            label = request.label.replace(" ", "_").replace("-", "_")
            props_str = ", ".join(props_parts) if props_parts else ""
            
            query = f"""
                CREATE (n:{label} {{{props_str}}})
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            return {
                "id": record["id"],
                "labels": record["labels"],
                "properties": dict(record["properties"]),
                "message": "Node created successfully"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/graph/node/{node_id}")
async def delete_node(node_id: str):
    """Delete a node and its relationships."""
    try:
        with driver.session() as session:
            # First check if node exists
            check = session.run("""
                MATCH (n) WHERE elementId(n) = $node_id RETURN n
            """, node_id=node_id)
            
            if not check.single():
                raise HTTPException(status_code=404, detail="Node not found")
            
            # Delete node and relationships
            session.run("""
                MATCH (n) WHERE elementId(n) = $node_id
                DETACH DELETE n
            """, node_id=node_id)
            
            return {"message": "Node deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/graph/relationship")
async def create_relationship(request: CreateRelationshipRequest):
    """Create a relationship between two nodes."""
    try:
        with driver.session() as session:
            # Sanitize relationship type
            rel_type = request.type.replace(" ", "_").replace("-", "_").upper()
            
            # Build properties
            props_parts = []
            params = {
                "source_id": request.source_id,
                "target_id": request.target_id
            }
            
            if request.properties:
                for key, value in request.properties.items():
                    safe_key = key.replace(" ", "_").replace("-", "_")
                    props_parts.append(f"{safe_key}: ${safe_key}")
                    params[safe_key] = value
            
            props_str = "{" + ", ".join(props_parts) + "}" if props_parts else ""
            
            query = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $source_id AND elementId(b) = $target_id
                CREATE (a)-[r:{rel_type} {props_str}]->(b)
                RETURN elementId(r) AS id, elementId(a) AS source, elementId(b) AS target,
                       type(r) AS type, properties(r) AS properties
            """
            
            result = session.run(query, **params)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="One or both nodes not found")
            
            return {
                "id": record["id"],
                "source": record["source"],
                "target": record["target"],
                "type": record["type"],
                "properties": dict(record["properties"]) if record["properties"] else {},
                "message": "Relationship created successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/graph/relationship/{rel_id}")
async def delete_relationship(rel_id: str):
    """Delete a relationship."""
    try:
        with driver.session() as session:
            # Check if relationship exists
            check = session.run("""
                MATCH ()-[r]->() WHERE elementId(r) = $rel_id RETURN r
            """, rel_id=rel_id)
            
            if not check.single():
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            # Delete relationship
            session.run("""
                MATCH ()-[r]->() WHERE elementId(r) = $rel_id DELETE r
            """, rel_id=rel_id)
            
            return {"message": "Relationship deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/labels")
async def get_all_labels():
    """Get all node labels in the graph."""
    try:
        with driver.session() as session:
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result if record["label"] != "_GraphConfig"]
            return {"labels": labels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/relationship-types")
async def get_relationship_types():
    """Get all relationship types in the graph."""
    try:
        with driver.session() as session:
            result = session.run("CALL db.relationshipTypes()")
            types = [record["relationshipType"] for record in result]
            return {"types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/search")
async def search_graph(q: str, limit: int = 50):
    """Search nodes by name or content."""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE NOT n:_GraphConfig AND (
                    toLower(n.name) CONTAINS toLower($query) OR
                    toLower(n.id) CONTAINS toLower($query) OR
                    toLower(n.description) CONTAINS toLower($query) OR
                    toLower(n.latex) CONTAINS toLower($query) OR
                    toLower(n.text) CONTAINS toLower($query)
                )
                RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
                LIMIT $limit
            """, query=q, limit=limit)
            
            nodes = []
            for record in result:
                props = dict(record["properties"])
                if "embedding" in props:
                    del props["embedding"]
                nodes.append({
                    "id": record["id"],
                    "labels": record["labels"],
                    "properties": props
                })
            
            return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve Vue.js static files
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4100)

