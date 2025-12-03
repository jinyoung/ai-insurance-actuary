import sys
import os

# Enable Mock Mode
os.environ["MOCK_MODE"] = "true"

from src.agent import run_agent

if __name__ == "__main__":
    print("--- Testing Agent in MOCK MODE ---")
    query = "순보험료 공식을 찾고, I=100, N=1000, L=500000, B=10일 때 값을 계산해줘."
    print(f"Query: {query}")
    response = run_agent(query)
    print("-" * 50)
    print("Agent Response:")
    print(response)
    print("-" * 50)

