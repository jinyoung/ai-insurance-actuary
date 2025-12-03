"""
FastAPI Backend for Actuarial Graph-RAG Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent import run_agent
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from neo4j import GraphDatabase

app = FastAPI(title="Actuarial Graph-RAG API", version="1.0.0")

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

class QueryResponse(BaseModel):
    query: str
    response: str
    success: bool

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
        response = run_agent(request.query)
        return QueryResponse(
            query=request.query,
            response=response,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# Serve Vue.js static files
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

