from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class GraphBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def init_schema(self):
        """Initialize the schema with constraints and indexes."""
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Formula) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Variable) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Definition) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Model) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Transition) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Parameter) REQUIRE n.name IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for query in queries:
                try:
                    session.run(query)
                    print(f"Executed: {query}")
                except Exception as e:
                    print(f"Error executing {query}: {e}")

    def verify_connection(self):
        try:
            self.driver.verify_connectivity()
            print("Neo4j connection verified.")
            return True
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            return False

if __name__ == "__main__":
    builder = GraphBuilder()
    if builder.verify_connection():
        builder.init_schema()
    builder.close()

