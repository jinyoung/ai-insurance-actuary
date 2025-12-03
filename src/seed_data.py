from src.graph_builder import GraphBuilder

def seed_sample_data():
    builder = GraphBuilder()
    if not builder.verify_connection():
        print("Cannot seed data: Connection failed.")
        return

    # PRD Section 7 Example
    # Formula: P = (I / N) * (L / B)
    
    cypher_statements = [
        # Create Formula
        """
        MERGE (f:Formula {id: "P1", latex: "P = (I / N) \\times (L / B)"})
        """,
        
        # Create Variables
        """
        MERGE (v1:Variable {name: "I"})
        MERGE (v2:Variable {name: "N"})
        MERGE (v3:Variable {name: "L"})
        MERGE (v4:Variable {name: "B"})
        """,
        
        # Create Concepts
        """
        MERGE (c1:Concept {name: "순보험료"})
        MERGE (c2:Concept {name: "사고발생률"})
        MERGE (c3:Concept {name: "본인부담의료비"})
        MERGE (c4:Concept {name: "사고건당 본인부담금"})
        """,
        
        # Create Model
        """
        MERGE (m:Model {name: "전통적 순보험료법"})
        """,
        
        # Relationships
        """
        MATCH (f:Formula {id: "P1"})
        MATCH (v1:Variable {name: "I"}), (v2:Variable {name: "N"}), (v3:Variable {name: "L"}), (v4:Variable {name: "B"})
        MERGE (v1)-[:USED_IN]->(f)
        MERGE (v2)-[:USED_IN]->(f)
        MERGE (v3)-[:USED_IN]->(f)
        MERGE (v4)-[:USED_IN]->(f)
        """,
        
        """
        MATCH (v3:Variable {name: "L"})
        MATCH (c4:Concept {name: "사고건당 본인부담금"})
        MERGE (c4)-[:DEFINES]->(v3)
        """,
        
        """
        MATCH (f:Formula {id: "P1"})
        MATCH (m:Model {name: "전통적 순보험료법"})
        MERGE (f)-[:PART_OF]->(m)
        """
    ]
    
    with builder.driver.session() as session:
        for stmt in cypher_statements:
            try:
                session.run(stmt)
                print("Executed statement.")
            except Exception as e:
                print(f"Error: {e}")

    builder.close()

if __name__ == "__main__":
    seed_sample_data()

