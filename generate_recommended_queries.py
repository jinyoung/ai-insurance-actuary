"""
추천 질의 자동 생성기
각 수식에 대해 사용자가 물어볼 만한 질의를 자동 생성합니다.
"""
import json
from neo4j import GraphDatabase
from openai import OpenAI
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def generate_recommended_queries(formula_name: str, latex: str, description: str, variables: list) -> list:
    """LLM을 사용하여 수식에 대한 추천 질의 생성"""
    
    var_info = ", ".join([f"{v['name']}({v.get('description', '')})" for v in variables]) if variables else "없음"
    
    prompt = f"""다음 보험계리 수식에 대해 사용자가 물어볼 만한 질의 3개를 생성하세요.

수식명: {formula_name}
LaTeX: {latex}
설명: {description}
변수: {var_info}

질의 유형:
1. 수식 설명 요청 (예: "~~ 공식이 뭐야?", "~~를 설명해줘")
2. 계산 요청 (예: "X=10, Y=20일 때 ~~ 계산해줘")
3. 개념 질문 (예: "~~와 ~~의 관계는?", "~~는 언제 사용해?")

JSON 배열로만 반환하세요:
["질의1", "질의2", "질의3"]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        content = response.choices[0].message.content
        # Parse JSON
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"  ⚠️ Query generation failed: {e}")
        # Fallback queries
        return [
            f"{formula_name}을 설명해줘",
            f"{formula_name}의 LaTeX 수식을 보여줘",
            f"{formula_name}는 언제 사용해?"
        ]

def update_all_formulas_with_queries():
    """모든 수식에 추천 질의 추가"""
    print("=" * 70)
    print("🔮 추천 질의 자동 생성")
    print("=" * 70)
    
    with driver.session() as session:
        # Get all formulas
        result = session.run("""
            MATCH (f:Formula)
            OPTIONAL MATCH (v:Variable)-[:USED_IN]->(f)
            RETURN f.id AS id, f.name AS name, f.latex AS latex, 
                   f.description AS description,
                   collect({name: v.name, description: v.description}) AS variables
        """)
        
        formulas = list(result)
        print(f"📐 {len(formulas)}개 수식 처리 중...\n")
        
        for record in formulas:
            formula_id = record["id"]
            name = record["name"] or formula_id
            latex = record["latex"] or ""
            description = record["description"] or ""
            variables = [v for v in record["variables"] if v.get("name")]
            
            print(f"  [{formula_id}] {name[:40]}...", end=" ", flush=True)
            
            # Generate queries
            queries = generate_recommended_queries(name, latex, description, variables)
            
            # Update in database
            session.run("""
                MATCH (f:Formula {id: $id})
                SET f.recommended_queries = $queries
            """, id=formula_id, queries=queries)
            
            print(f"✅ {len(queries)} queries")
    
    print("\n🎉 완료!")

def show_all_recommended_queries():
    """모든 추천 질의 표시"""
    print("\n" + "=" * 70)
    print("📋 전체 추천 질의 목록")
    print("=" * 70)
    
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.recommended_queries IS NOT NULL
            RETURN f.name AS name, f.recommended_queries AS queries
            ORDER BY f.name
        """)
        
        for record in result:
            print(f"\n📐 {record['name']}")
            for q in record['queries']:
                print(f"   • {q}")

if __name__ == "__main__":
    update_all_formulas_with_queries()
    show_all_recommended_queries()

