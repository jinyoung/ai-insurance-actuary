import sys
import os

os.environ["MOCK_MODE"] = "false"

from src.agent import run_agent

if __name__ == "__main__":
    print("=" * 70)
    print("🧮 보험계리 Graph-RAG Agent 테스트 (Enhanced with Embeddings)")
    print("=" * 70)
    
    queries = [
        "순보험료를 계산하는 공식이 뭐야? LaTeX로 보여줘.",
        "I=100, N=1000, L=500000, B=10일 때 순보험료 P를 계산해줘.",
        "사고발생률이 뭐야?",
        "영업보험료의 구성요소를 알려줘.",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"🔹 Query {i}: {query}")
        print("-" * 70)
        try:
            response = run_agent(query)
            print(f"📝 Response:\n{response}")
        except Exception as e:
            import traceback
            print(f"❌ Error: {e}")
            traceback.print_exc()
        print("-" * 70)

