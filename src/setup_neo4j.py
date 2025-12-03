import os
from neo4j import GraphDatabase

# Configuration
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "18925jjy")

def create_constraints(driver):
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Formula) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Variable) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Definition) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Model) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Transition) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Parameter) REQUIRE n.name IS UNIQUE",
        
        # Vector indexes (placeholder for now, usually requires specific configuration)
        # "CREATE VECTOR INDEX formula_embedding IF NOT EXISTS FOR (n:Formula) ON (n.embedding) OPTIONS {indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' }}"
    ]
    
    with driver.session() as session:
        for query in queries:
            print(f"Running: {query}")
            session.run(query)

def verify_connection():
    try:
        with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
            driver.verify_connectivity()
            print("Connection to Neo4j verified successfully.")
            create_constraints(driver)
            print("Schema constraints created.")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")

if __name__ == "__main__":
    verify_connection()

