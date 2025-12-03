from neo4j import GraphDatabase

URI = 'bolt://localhost:7687'
USERNAME = 'neo4j'
PASSWORD = '18925jjy'

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Clean Cypher statements extracted from generated file
cypher_statements = [
    # Page 1 - Concepts
    'MERGE (c1:Concept {name: "실손건강보험"})',
    'MERGE (c2:Concept {name: "손해보험"})',
    'MERGE (c3:Concept {name: "대수의 법칙"})',
    'MERGE (c4:Concept {name: "영업보험료"})',
    'MERGE (c5:Concept {name: "순보험료"})',
    'MERGE (c6:Concept {name: "부가보험료"})',
    'MERGE (c7:Concept {name: "장기계약생명보험"})',
    'MERGE (c8:Concept {name: "장기손해보험"})',
    'MERGE (c9:Concept {name: "일반손해보험"})',
    'MERGE (c10:Concept {name: "보험수리적 접근"})',
    'MERGE (c11:Concept {name: "보험경계학적 접근"})',
    'MERGE (c12:Concept {name: "최적판매가격"})',
    'MERGE (c13:Concept {name: "예정이윤"})',
    'MERGE (c14:Concept {name: "생명보험"})',
    'MERGE (c15:Concept {name: "실손형 건강보험"})',
    
    # Page 2 - Additional Concepts
    'MERGE (:Concept {name: "적정성"})',
    'MERGE (:Concept {name: "비과도성"})',
    'MERGE (:Concept {name: "공정성"})',
    'MERGE (:Concept {name: "전통적 순보험료법"})',
    
    # Variables
    'MERGE (:Variable {name: "P", description: "순보험료 (1인당 평균본인부담의료비)"})',
    'MERGE (:Variable {name: "I", description: "보험사고 발생건수"})',
    'MERGE (:Variable {name: "N", description: "위험단위수"})',
    'MERGE (:Variable {name: "L", description: "총발생손해액"})',
    'MERGE (:Variable {name: "B", description: "총보험금"})',
    
    # Formulas
    'MERGE (:Formula {id: "F1", expression: "P = (I/N) * (L/B)", description: "순보험료 산출 공식"})',
    
    # Model
    'MERGE (:Model {name: "전통적 순보험료법"})',
]

# Definitions (separate because they are longer)
definitions = [
    ('실손건강보험', '실손건강보험의 원리는 손해보험의 그것과 유사하다. 동일위험을 안고 있는 다수의 경제단위가 하나의 위험집단을 구성해서 각자가 납출한 보험료에 의해 구성원 일부가 입는 의료비 손해를 보상함으로써 의료비에 의한 경제적 충격을 최소화하는 위험의 분담이 그 운영원리이다.'),
    ('대수의 법칙', '동일위험에 당면하고 있는 사람이 장래에 사고 발생의 경향을 예측할 수 있을 정도로 다수가 있어야 한다는 원칙이다.'),
    ('영업보험료', '보험가입자가 보험자에게 위험보장의 대가로서 지불하는 금액을 의미하며, 이는 보험금 지급에 충당되는 부분인 순보험료와 사업비 지급에 충당되는 부분인 부가보험료로 구성된다.'),
    ('부가보험료', '장기계약생명보험과 장기손해보험에서 예정사업비(유지비, 수금비)를 의미하며, 일반(단기)손해보험에서는 예정이윤을 포함한다.'),
    ('전통적 순보험료법', '사고발생률(빈도)와 사고건당 본인부담금(심도)을 토대로 동일위험집단에 대한 위험도를 수리적 또는 통계적 분석방법으로 예측하여 보험료를 산정하는 방법이다.'),
    ('순보험료', '보험자의 지급능력 상태가 발생하지 않는 수준이어야 한다(순보험료의 적정성 확보).'),
    ('적정성', '보험자의 지급능력에 대비한 요율의 수준을 강조한 것이다.'),
    ('비과도성', '보험료가 과도하지 않도록 해야 한다.'),
    ('공정성', '보험가입자의 개별위험에 대하여 공정하게 요율을 결정해야 한다.'),
]

# Relationships
relationships = [
    # Concept -> Concept
    ('실손건강보험', 'RELATED_TO', '손해보험'),
    ('영업보험료', 'COMPOSED_OF', '순보험료'),
    ('영업보험료', 'COMPOSED_OF', '부가보험료'),
    ('부가보험료', 'RELATED_TO', '장기계약생명보험'),
    ('부가보험료', 'RELATED_TO', '장기손해보험'),
    ('부가보험료', 'RELATED_TO', '일반손해보험'),
    ('보험경계학적 접근', 'RELATED_TO', '예정이윤'),
    ('보험경계학적 접근', 'RELATED_TO', '최적판매가격'),
    ('생명보험', 'RELATED_TO', '실손형 건강보험'),
    ('순보험료', 'RELATED_TO', '전통적 순보험료법'),
    ('실손형 건강보험', 'RELATED_TO', '순보험료'),
    
    # Variable -> Formula
]

with driver.session() as session:
    # 1. Create nodes
    print("Creating nodes...")
    for stmt in cypher_statements:
        session.run(stmt)
    print(f"  ✅ Created {len(cypher_statements)} base nodes")
    
    # 2. Create definitions and link to concepts
    print("Creating definitions...")
    for concept_name, def_text in definitions:
        query = """
        MATCH (c:Concept {name: $concept_name})
        MERGE (d:Definition {text: $def_text})
        MERGE (c)-[:DEFINES]->(d)
        """
        session.run(query, concept_name=concept_name, def_text=def_text)
    print(f"  ✅ Created {len(definitions)} definitions")
    
    # 3. Create relationships between concepts
    print("Creating relationships...")
    for src, rel_type, tgt in relationships:
        query = f"""
        MATCH (a:Concept {{name: $src}})
        MATCH (b:Concept {{name: $tgt}})
        MERGE (a)-[:{rel_type}]->(b)
        """
        session.run(query, src=src, tgt=tgt)
    print(f"  ✅ Created {len(relationships)} relationships")
    
    # 4. Link Variables to Formula
    print("Linking variables to formula...")
    var_formula_links = [
        ('P', 'F1'), ('I', 'F1'), ('N', 'F1'), ('L', 'F1'), ('B', 'F1')
    ]
    for var_name, formula_id in var_formula_links:
        query = """
        MATCH (v:Variable {name: $var_name})
        MATCH (f:Formula {id: $formula_id})
        MERGE (v)-[:USED_IN]->(f)
        """
        session.run(query, var_name=var_name, formula_id=formula_id)
    print(f"  ✅ Linked {len(var_formula_links)} variables to formula")
    
    # 5. Link Formula to Model
    print("Linking formula to model...")
    session.run("""
        MATCH (f:Formula {id: 'F1'})
        MATCH (m:Model {name: '전통적 순보험료법'})
        MERGE (f)-[:PART_OF]->(m)
    """)
    print("  ✅ Linked formula to model")

print("\n🎉 Graph data inserted successfully!")
driver.close()

