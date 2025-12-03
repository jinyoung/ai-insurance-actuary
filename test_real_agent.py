import sys
import os

# Disable Mock Mode - use real Neo4j
os.environ["MOCK_MODE"] = "false"

from src.agent import run_agent

if __name__ == "__main__":
    print("=" * 60)
    print("🧮 보험계리 Graph-RAG Agent 테스트")
    print("=" * 60)
    
    queries = [
        "순보험료 공식을 찾아서 설명해줘.",
        "I=100, N=1000, L=500000, B=10일 때 순보험료를 계산해줘.",
        "영업보험료의 구성요소가 뭐야?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔹 Query {i}: {query}")
        print("-" * 50)
        try:
            response = run_agent(query)
            print(f"📝 Response:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 50)

