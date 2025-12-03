import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "18925jjy")

print(f"Connecting to {uri} as {user} with password length {len(password)}")
print(f"Password first 2 chars: {password[:2]}")
print(f"Password last 2 chars: {password[-2:]}")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")

