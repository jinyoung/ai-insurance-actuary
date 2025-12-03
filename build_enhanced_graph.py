"""
Enhanced Graph Builder with:
1. LaTeX formula parsing with parameter nodes
2. Embedding vectors for similarity search
"""
import json
from neo4j import GraphDatabase
from openai import OpenAI
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY

# OpenAI client for embeddings
client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """Get embedding vector for text."""
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def create_vector_index(driver):
    """Create vector index for similarity search."""
    with driver.session() as session:
        # Create vector indexes for each node type
        indexes = [
            """
            CREATE VECTOR INDEX concept_embedding IF NOT EXISTS
            FOR (n:Concept) ON (n.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
            """,
            """
            CREATE VECTOR INDEX formula_embedding IF NOT EXISTS
            FOR (n:Formula) ON (n.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
            """,
            """
            CREATE VECTOR INDEX variable_embedding IF NOT EXISTS
            FOR (n:Variable) ON (n.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
            """,
            """
            CREATE VECTOR INDEX definition_embedding IF NOT EXISTS
            FOR (n:Definition) ON (n.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
            """
        ]
        for idx_query in indexes:
            try:
                session.run(idx_query)
                print(f"✅ Vector index created")
            except Exception as e:
                print(f"⚠️ Index creation: {e}")

def clear_database(driver):
    """Clear existing data."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("🗑️ Database cleared")

def insert_enhanced_graph(driver):
    """Insert enhanced graph with LaTeX formulas and embeddings."""
    
    # ============================================================
    # 1. FORMULAS with LaTeX and detailed parameters
    # ============================================================
    formulas = [
        {
            "id": "F1",
            "name": "순보험료 공식",
            "latex": r"P = \frac{I}{N} \times \frac{L}{B}",
            "expression": "(I/N) * (L/B)",
            "description": "순보험료(P)는 사고발생률(I/N)과 사고심도(L/B)의 곱으로 산출됩니다. 전통적 순보험료법의 핵심 공식입니다.",
            "variables": [
                {"name": "P", "latex": "P", "description": "순보험료 (Net Premium)", "unit": "원", "role": "output"},
                {"name": "I", "latex": "I", "description": "보험사고 발생건수 (Number of Claims)", "unit": "건", "role": "input"},
                {"name": "N", "latex": "N", "description": "위험단위수 (Number of Exposure Units)", "unit": "단위", "role": "input"},
                {"name": "L", "latex": "L", "description": "총발생손해액 (Total Loss Amount)", "unit": "원", "role": "input"},
                {"name": "B", "latex": "B", "description": "총보험금 (Total Benefits)", "unit": "원", "role": "input"},
            ]
        },
        {
            "id": "F2", 
            "name": "사고발생률 공식",
            "latex": r"\text{사고발생률} = \frac{I}{N}",
            "expression": "I/N",
            "description": "사고발생률(빈도)은 위험단위수 대비 보험사고 발생건수의 비율입니다.",
            "variables": [
                {"name": "I", "latex": "I", "description": "보험사고 발생건수", "unit": "건", "role": "input"},
                {"name": "N", "latex": "N", "description": "위험단위수", "unit": "단위", "role": "input"},
            ]
        },
        {
            "id": "F3",
            "name": "사고심도 공식", 
            "latex": r"\text{사고심도} = \frac{L}{B}",
            "expression": "L/B",
            "description": "사고심도는 사고건당 본인부담금으로, 총발생손해액을 총보험금으로 나눈 값입니다.",
            "variables": [
                {"name": "L", "latex": "L", "description": "총발생손해액", "unit": "원", "role": "input"},
                {"name": "B", "latex": "B", "description": "총보험금", "unit": "원", "role": "input"},
            ]
        },
        {
            "id": "F4",
            "name": "영업보험료 공식",
            "latex": r"\text{영업보험료} = \text{순보험료} + \text{부가보험료}",
            "expression": "P + Loading",
            "description": "영업보험료는 순보험료(위험보험료)와 부가보험료(사업비)의 합입니다.",
            "variables": [
                {"name": "P", "latex": "P", "description": "순보험료", "unit": "원", "role": "input"},
                {"name": "Loading", "latex": "\\text{부가}", "description": "부가보험료 (사업비)", "unit": "원", "role": "input"},
            ]
        }
    ]
    
    # ============================================================
    # 2. CONCEPTS with definitions
    # ============================================================
    concepts = [
        {"name": "실손건강보험", "definition": "동일위험을 안고 있는 다수의 경제단위가 하나의 위험집단을 구성해서 각자가 납출한 보험료에 의해 구성원 일부가 입는 의료비 손해를 보상하는 보험"},
        {"name": "손해보험", "definition": "우연한 사고로 인한 재산상의 손해를 보상하는 보험"},
        {"name": "대수의 법칙", "definition": "동일위험에 당면하고 있는 사람이 장래에 사고 발생의 경향을 예측할 수 있을 정도로 다수가 있어야 한다는 원칙"},
        {"name": "영업보험료", "definition": "보험가입자가 보험자에게 위험보장의 대가로서 지불하는 금액으로, 순보험료와 부가보험료로 구성"},
        {"name": "순보험료", "definition": "보험금 지급에 충당되는 부분으로, 위험보험료라고도 함"},
        {"name": "부가보험료", "definition": "사업비 지급에 충당되는 부분으로, 장기보험에서는 예정사업비, 단기보험에서는 예정이윤 포함"},
        {"name": "전통적 순보험료법", "definition": "사고발생률(빈도)와 사고건당 본인부담금(심도)을 토대로 동일위험집단에 대한 위험도를 수리적으로 예측하여 보험료를 산정하는 방법"},
        {"name": "적정성", "definition": "보험자의 지급능력 상태가 발생하지 않는 수준의 보험료"},
        {"name": "비과도성", "definition": "보험료가 과도하지 않아야 한다는 원칙"},
        {"name": "공정성", "definition": "보험가입자의 개별위험에 대하여 공정하게 요율을 결정해야 한다는 원칙"},
    ]
    
    # ============================================================
    # 3. RELATIONSHIPS
    # ============================================================
    relationships = [
        ("실손건강보험", "RELATED_TO", "손해보험"),
        ("영업보험료", "COMPOSED_OF", "순보험료"),
        ("영업보험료", "COMPOSED_OF", "부가보험료"),
        ("순보험료", "CALCULATED_BY", "전통적 순보험료법"),
        ("영업보험료", "REQUIRES", "적정성"),
        ("영업보험료", "REQUIRES", "비과도성"),
        ("영업보험료", "REQUIRES", "공정성"),
    ]
    
    with driver.session() as session:
        # --------------------------------------------------------
        # Insert Formulas with embeddings
        # --------------------------------------------------------
        print("\n📐 Inserting Formulas with LaTeX and embeddings...")
        for f in formulas:
            # Create embedding for formula
            embed_text = f"{f['name']}: {f['description']} LaTeX: {f['latex']}"
            embedding = get_embedding(embed_text)
            
            session.run("""
                MERGE (formula:Formula {id: $id})
                SET formula.name = $name,
                    formula.latex = $latex,
                    formula.expression = $expression,
                    formula.description = $description,
                    formula.embedding = $embedding
            """, id=f["id"], name=f["name"], latex=f["latex"], 
                expression=f["expression"], description=f["description"],
                embedding=embedding)
            print(f"  ✅ Formula: {f['name']}")
            
            # Insert Variables for this formula
            for v in f["variables"]:
                var_embed_text = f"변수 {v['name']}: {v['description']} ({v['role']})"
                var_embedding = get_embedding(var_embed_text)
                
                session.run("""
                    MERGE (v:Variable {name: $name})
                    SET v.latex = $latex,
                        v.description = $description,
                        v.unit = $unit,
                        v.role = $role,
                        v.embedding = $embedding
                """, name=v["name"], latex=v["latex"], description=v["description"],
                    unit=v["unit"], role=v["role"], embedding=var_embedding)
                
                # Link variable to formula
                session.run("""
                    MATCH (v:Variable {name: $var_name})
                    MATCH (f:Formula {id: $formula_id})
                    MERGE (v)-[:USED_IN]->(f)
                """, var_name=v["name"], formula_id=f["id"])
            
        # --------------------------------------------------------
        # Insert Concepts with embeddings
        # --------------------------------------------------------
        print("\n📚 Inserting Concepts with embeddings...")
        for c in concepts:
            embed_text = f"{c['name']}: {c['definition']}"
            embedding = get_embedding(embed_text)
            
            session.run("""
                MERGE (concept:Concept {name: $name})
                SET concept.embedding = $embedding
            """, name=c["name"], embedding=embedding)
            
            # Create Definition node
            def_embedding = get_embedding(c["definition"])
            session.run("""
                MATCH (concept:Concept {name: $name})
                MERGE (d:Definition {text: $text})
                SET d.embedding = $embedding
                MERGE (concept)-[:DEFINES]->(d)
            """, name=c["name"], text=c["definition"], embedding=def_embedding)
            print(f"  ✅ Concept: {c['name']}")
        
        # --------------------------------------------------------
        # Insert Relationships
        # --------------------------------------------------------
        print("\n🔗 Creating relationships...")
        for src, rel, tgt in relationships:
            session.run(f"""
                MATCH (a:Concept {{name: $src}})
                MATCH (b:Concept {{name: $tgt}})
                MERGE (a)-[:{rel}]->(b)
            """, src=src, tgt=tgt)
        
        # Link formulas to concepts
        session.run("""
            MATCH (f:Formula {id: 'F1'})
            MATCH (c:Concept {name: '전통적 순보험료법'})
            MERGE (f)-[:PART_OF]->(c)
        """)
        session.run("""
            MATCH (f:Formula {id: 'F1'})
            MATCH (c:Concept {name: '순보험료'})
            MERGE (f)-[:CALCULATES]->(c)
        """)
        print("  ✅ Relationships created")

def main():
    print("=" * 60)
    print("🔧 Enhanced Graph Builder")
    print("=" * 60)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # 1. Clear existing data
    clear_database(driver)
    
    # 2. Create vector indexes
    print("\n📊 Creating vector indexes...")
    create_vector_index(driver)
    
    # 3. Insert enhanced graph
    print("\n📥 Inserting enhanced graph data...")
    insert_enhanced_graph(driver)
    
    # 4. Verify
    print("\n" + "=" * 60)
    print("📊 Verification")
    print("=" * 60)
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count")
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        
        # Check embeddings
        result = session.run("MATCH (f:Formula) WHERE f.embedding IS NOT NULL RETURN count(f) AS count")
        print(f"\n  Formulas with embeddings: {result.single()['count']}")
        
        result = session.run("MATCH (v:Variable) WHERE v.embedding IS NOT NULL RETURN count(v) AS count")
        print(f"  Variables with embeddings: {result.single()['count']}")
        
        result = session.run("MATCH (c:Concept) WHERE c.embedding IS NOT NULL RETURN count(c) AS count")
        print(f"  Concepts with embeddings: {result.single()['count']}")
    
    driver.close()
    print("\n🎉 Done!")

if __name__ == "__main__":
    main()

