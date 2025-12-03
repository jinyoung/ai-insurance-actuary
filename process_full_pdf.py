"""
전체 PDF 처리 및 수식 추출 + Neo4j 그래프 구축
"""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ingestion import PDFIngestion
from neo4j import GraphDatabase
from openai import OpenAI
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY

# OpenAI client for embeddings
client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    """Get embedding vector for text."""
    text = text.replace("\n", " ")[:8000]  # Limit text length
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def process_full_pdf():
    """Process all pages of the PDF and extract formulas."""
    pdf_path = "data/nre2007-02_02-1.pdf"
    
    print("=" * 70)
    print("📄 전체 PDF 처리 시작")
    print("=" * 70)
    
    ingestion = PDFIngestion(pdf_path)
    
    # Process all pages (formulas only for speed)
    all_formulas = ingestion.process_formulas_only(max_pages=None)
    
    # Save to JSON
    output_file = "all_formulas_extracted.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_formulas, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 총 {len(all_formulas)}개 수식 추출됨")
    print(f"💾 저장: {output_file}")
    
    return all_formulas

def insert_formulas_to_graph(formulas):
    """Insert extracted formulas into Neo4j graph."""
    print("\n" + "=" * 70)
    print("🔧 Neo4j 그래프에 수식 삽입")
    print("=" * 70)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Don't clear - add to existing data
    formula_count = 0
    variable_count = 0
    
    with driver.session() as session:
        for i, formula in enumerate(formulas):
            if not formula.get("latex") and not formula.get("expression"):
                continue
                
            formula_id = f"F_auto_{i+1}"
            name = formula.get("name", f"공식 {i+1}")
            latex = formula.get("latex", "")
            expression = formula.get("expression", "")
            description = formula.get("description", "")
            source_page = formula.get("source_page", 0)
            
            # Skip if already exists with same latex
            check = session.run("""
                MATCH (f:Formula) WHERE f.latex = $latex RETURN f
            """, latex=latex)
            if check.single():
                print(f"  ⏭️ Skip duplicate: {name[:30]}...")
                continue
            
            # Create embedding
            embed_text = f"{name}: {description} LaTeX: {latex}"
            try:
                embedding = get_embedding(embed_text)
            except Exception as e:
                print(f"  ⚠️ Embedding error: {e}")
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
            
            formula_count += 1
            print(f"  ✅ [{formula_id}] {name[:40]}...")
            
            # Insert variables
            variables = formula.get("variables", [])
            for var in variables:
                var_name = var.get("name", "")
                if not var_name:
                    continue
                    
                var_latex = var.get("latex", var_name)
                var_desc = var.get("description", "")
                var_unit = var.get("unit", "")
                
                # Create variable embedding
                var_embed_text = f"변수 {var_name}: {var_desc}"
                try:
                    var_embedding = get_embedding(var_embed_text)
                except:
                    var_embedding = None
                
                if var_embedding:
                    session.run("""
                        MERGE (v:Variable {name: $name})
                        ON CREATE SET v.latex = $latex,
                                      v.description = $description,
                                      v.unit = $unit,
                                      v.embedding = $embedding
                    """, name=var_name, latex=var_latex, description=var_desc,
                        unit=var_unit, embedding=var_embedding)
                else:
                    session.run("""
                        MERGE (v:Variable {name: $name})
                        ON CREATE SET v.latex = $latex,
                                      v.description = $description,
                                      v.unit = $unit
                    """, name=var_name, latex=var_latex, description=var_desc,
                        unit=var_unit)
                
                # Link variable to formula
                session.run("""
                    MATCH (v:Variable {name: $var_name})
                    MATCH (f:Formula {id: $formula_id})
                    MERGE (v)-[:USED_IN]->(f)
                """, var_name=var_name, formula_id=formula_id)
                
                variable_count += 1
    
    driver.close()
    
    print(f"\n📊 삽입 완료: {formula_count}개 수식, {variable_count}개 변수")
    return formula_count, variable_count

def verify_graph():
    """Verify the graph contents."""
    print("\n" + "=" * 70)
    print("📊 그래프 검증")
    print("=" * 70)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Count nodes
        result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC")
        print("\n노드 현황:")
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        
        # List all formulas
        result = session.run("""
            MATCH (f:Formula) 
            RETURN f.id AS id, f.name AS name, f.latex AS latex, f.source_page AS page
            ORDER BY f.source_page, f.id
        """)
        
        print("\n📐 전체 수식 목록:")
        for record in result:
            page = record['page'] or "?"
            print(f"  [{record['id']}] p.{page} - {record['name'][:50]}")
            if record['latex']:
                print(f"       LaTeX: {record['latex'][:60]}...")
    
    driver.close()

def main():
    print("🚀 전체 PDF 수식 추출 및 그래프 구축 시작\n")
    
    # Step 1: Process PDF and extract formulas
    formulas = process_full_pdf()
    
    if not formulas:
        print("❌ 수식이 추출되지 않았습니다.")
        return
    
    # Step 2: Insert into Neo4j
    insert_formulas_to_graph(formulas)
    
    # Step 3: Verify
    verify_graph()
    
    print("\n🎉 완료!")

if __name__ == "__main__":
    main()

