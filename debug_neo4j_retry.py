import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Force reload or set directly to ensure no stale env vars
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "18925jjy"

print(f"Connecting to {NEO4J_URI} as {NEO4J_USERNAME}")

try:
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        driver.verify_connectivity()
        print("Connection successful!")
        
        # Try a simple query to ensure permissions are okay
        with driver.session() as session:
            result = session.run("RETURN 1 AS num")
            print(f"Query result: {result.single()['num']}")
            
except Exception as e:
    print(f"Connection failed: {e}")

