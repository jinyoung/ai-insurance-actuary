from typing import Annotated, List
from typing_extensions import TypedDict
import numpy as np

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from openai import OpenAI

from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY, MOCK_MODE
from neo4j import GraphDatabase
from src.mcp_calculator import evaluate_formula_tool

# OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Neo4j Driver
if not MOCK_MODE:
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    except Exception:
        driver = None
else:
    driver = None

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """Get embedding vector for text."""
    text = text.replace("\n", " ")
    response = openai_client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Schema documentation
SCHEMA_INFO = """
## Neo4j Graph Schema (Enhanced with Embeddings)

### Node Types:
1. **Concept** - Properties: {name, embedding[1536]}
   - Examples: "순보험료", "영업보험료", "대수의 법칙"
   
2. **Definition** - Properties: {text, embedding[1536]}
   - Contains explanation text for concepts
   
3. **Variable** - Properties: {name, latex, description, unit, role, embedding[1536]}
   - Examples: P (순보험료), I (보험사고 발생건수), N (위험단위수)
   - role: "input" or "output"
   
4. **Formula** - Properties: {id, name, latex, expression, description, embedding[1536]}
   - latex: LaTeX representation (e.g., "P = \\frac{I}{N} \\times \\frac{L}{B}")
   - expression: Python-evaluable (e.g., "(I/N) * (L/B)")

### Relationship Types:
- (Concept)-[:DEFINES]->(Definition)
- (Concept)-[:RELATED_TO]->(Concept)
- (Concept)-[:COMPOSED_OF]->(Concept)
- (Variable)-[:USED_IN]->(Formula)
- (Formula)-[:PART_OF]->(Concept)
- (Formula)-[:CALCULATES]->(Concept)

### Example Queries:
- Find formula by name: MATCH (f:Formula {name: '순보험료 공식'}) RETURN f
- Get formula with variables: 
  MATCH (v:Variable)-[:USED_IN]->(f:Formula {id: 'F1'}) 
  RETURN f.latex, f.expression, collect({name: v.name, desc: v.description, role: v.role})
"""

@tool
def similarity_search(query: str, node_type: str = "all", top_k: int = 3) -> str:
    """
    Performs semantic similarity search on the graph.
    node_type: "Formula", "Concept", "Variable", "Definition", or "all"
    Returns the most similar nodes based on embedding similarity.
    """
    if not driver:
        return "Database connection not available."
    
    try:
        query_embedding = get_embedding(query)
        
        # Get all nodes of the specified type with embeddings
        if node_type == "all":
            cypher = """
                MATCH (n) WHERE n.embedding IS NOT NULL
                RETURN labels(n)[0] AS type, n AS node
            """
        else:
            cypher = f"""
                MATCH (n:{node_type}) WHERE n.embedding IS NOT NULL
                RETURN '{node_type}' AS type, n AS node
            """
        
        with driver.session() as session:
            result = session.run(cypher)
            records = list(result)
            
            # Calculate similarities
            scored = []
            for record in records:
                node = record["node"]
                node_embedding = node.get("embedding")
                if node_embedding:
                    sim = cosine_similarity(query_embedding, node_embedding)
                    scored.append({
                        "type": record["type"],
                        "similarity": sim,
                        "properties": {k: v for k, v in node.items() if k != "embedding"}
                    })
            
            # Sort by similarity
            scored.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = scored[:top_k]
            
            return str(top_results)
    except Exception as e:
        return f"Search error: {e}"

@tool
def run_cypher(query: str) -> str:
    """
    Executes a Cypher query against the Neo4j database.
    Use this to find specific formulas, concepts, variables and their relationships.
    """
    if not driver:
        return "Database connection not available."
    
    try:
        with driver.session() as session:
            result = session.run(query)
            data = []
            for record in result:
                row = {}
                for key in record.keys():
                    val = record[key]
                    if hasattr(val, 'items'):  # Node
                        row[key] = {k: v for k, v in val.items() if k != "embedding"}
                    else:
                        row[key] = val
                data.append(row)
            return str(data)
    except Exception as e:
        return f"Cypher error: {e}"

@tool
def get_formula_details(formula_name: str) -> str:
    """
    Gets detailed information about a formula including its LaTeX representation,
    expression, and all variables with their descriptions.
    """
    if not driver:
        return "Database connection not available."
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (f:Formula)
                WHERE f.name CONTAINS $name OR f.id = $name
                OPTIONAL MATCH (v:Variable)-[:USED_IN]->(f)
                RETURN f.id AS id, f.name AS name, f.latex AS latex, 
                       f.expression AS expression, f.description AS description,
                       collect({
                           name: v.name, 
                           latex: v.latex,
                           description: v.description, 
                           unit: v.unit, 
                           role: v.role
                       }) AS variables
            """, name=formula_name)
            
            records = list(result)
            if not records:
                return f"Formula '{formula_name}' not found."
            
            return str([dict(r) for r in records])
    except Exception as e:
        return f"Error: {e}"

@tool
def calculate_formula(formula_expression: str, variables: str) -> str:
    """
    Evaluates a mathematical formula expression.
    formula_expression: Python-evaluable expression like "(I/N) * (L/B)"
    variables: JSON string with variable values, e.g., '{"I": 100, "N": 1000, "L": 500000, "B": 10}'
    """
    import json
    try:
        vars_dict = json.loads(variables)
        result = evaluate_formula_tool(formula_expression, vars_dict)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# LLM
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)
tools = [similarity_search, run_cypher, get_formula_details, calculate_formula]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Graph Construction
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

graph = workflow.compile()

SYSTEM_PROMPT = f"""You are an Actuarial Assistant for Korean insurance documents.
You have access to a Neo4j knowledge graph with embedded vectors for semantic search.

{SCHEMA_INFO}

## Available Tools:
1. **similarity_search(query, node_type, top_k)**: Semantic search using embeddings. 
   - Use this FIRST to find relevant formulas/concepts.
   - node_type can be "Formula", "Concept", "Variable", "Definition", or "all"

2. **get_formula_details(formula_name)**: Get complete formula info including LaTeX and all variables.

3. **run_cypher(query)**: Execute Cypher queries for specific graph traversals.

4. **calculate_formula(expression, variables)**: Evaluate a formula with given values.

## Instructions:
1. For questions about formulas or concepts, use similarity_search FIRST.
2. Once you find a relevant formula, use get_formula_details to get the full LaTeX and variables.
3. When calculating, extract the 'expression' field from the formula and use calculate_formula.
4. Always show the LaTeX formula in your response.
5. Respond in Korean when the user asks in Korean.
6. Explain the actuarial reasoning behind your answers.
"""

def run_agent(user_query: str):
    initial_state = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query)
    ]}
    result = graph.invoke(initial_state)
    return result["messages"][-1].content
