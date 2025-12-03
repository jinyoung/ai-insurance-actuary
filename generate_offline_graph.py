from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import OPENAI_API_KEY

def generate_cypher_from_text(text):
    llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0)
    
    prompt = f"""
    You are an expert Actuarial Graph Engineer.
    Analyze the following text from an actuarial document and extract Entities and Relationships to build a Neo4j graph.
    
    Target Node Types:
    - Concept (e.g., "실손건강보험", "대수의 법칙")
    - Definition (The text explaining a concept)
    - Variable (Mathematical variables if any, e.g., "P", "I")
    - Formula (Mathematical formulas)
    
    Target Relationship Types:
    - DEFINES (Concept -> Definition)
    - RELATED_TO (Concept -> Concept)
    - USED_IN (Variable -> Formula)
    - COMPOSED_OF (Concept -> Concept) e.g., Premium composed of NetPremium and Loading.
    
    Text:
    {text}
    
    Output strictly valid Cypher MERGE statements to construct this graph.
    Use MERGE to avoid duplicates.
    Do not include markdown formatting like ```cypher. Just the raw queries.
    Escape quotes in text properly.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.replace("```cypher", "").replace("```", "")
