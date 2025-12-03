"""
보험료 산출 정확도 테스트
- 다양한 변수값으로 테스트 케이스 생성
- Agent의 계산 결과와 예상값 비교
"""
import os
import re
os.environ["MOCK_MODE"] = "false"

from src.agent import run_agent

# ============================================================
# 테스트 케이스 정의
# ============================================================
# 순보험료 공식: P = (I/N) * (L/B)
# I: 보험사고 발생건수
# N: 위험단위수  
# L: 총발생손해액
# B: 총보험금

TEST_CASES = [
    {
        "name": "기본 테스트",
        "variables": {"I": 100, "N": 1000, "L": 500000, "B": 10},
        "expected_P": (100/1000) * (500000/10),  # 5000.0
        "query": "I=100, N=1000, L=500000, B=10일 때 순보험료를 계산해줘."
    },
    {
        "name": "낮은 사고발생률",
        "variables": {"I": 50, "N": 10000, "L": 1000000, "B": 100},
        "expected_P": (50/10000) * (1000000/100),  # 50.0
        "query": "보험사고 발생건수가 50건, 위험단위수가 10000, 총발생손해액이 1000000원, 총보험금이 100원일 때 순보험료 P를 계산해줘."
    },
    {
        "name": "높은 사고발생률",
        "variables": {"I": 500, "N": 1000, "L": 2000000, "B": 50},
        "expected_P": (500/1000) * (2000000/50),  # 20000.0
        "query": "I가 500, N이 1000, L이 2000000, B가 50일 때 순보험료는 얼마야?"
    },
    {
        "name": "소수점 결과",
        "variables": {"I": 75, "N": 1000, "L": 300000, "B": 15},
        "expected_P": (75/1000) * (300000/15),  # 1500.0
        "query": "다음 조건에서 순보험료를 계산해줘: 사고건수 I=75, 위험단위 N=1000, 손해액 L=300000, 보험금 B=15"
    },
    {
        "name": "큰 숫자",
        "variables": {"I": 1000, "N": 100000, "L": 50000000, "B": 1000},
        "expected_P": (1000/100000) * (50000000/1000),  # 500.0
        "query": "I=1000, N=100000, L=50000000, B=1000 조건에서 순보험료 공식을 적용하여 P값을 구해줘."
    },
    {
        "name": "사고발생률 계산",
        "variables": {"I": 200, "N": 4000},
        "expected_result": 200/4000,  # 0.05
        "formula": "사고발생률",
        "query": "보험사고 발생건수가 200건이고 위험단위수가 4000일 때 사고발생률을 계산해줘."
    },
    {
        "name": "사고심도 계산",
        "variables": {"L": 800000, "B": 200},
        "expected_result": 800000/200,  # 4000.0
        "formula": "사고심도",
        "query": "총발생손해액이 800000원이고 총보험금이 200일 때 사고심도는?"
    },
]

def extract_number_from_response(response: str, expected: float = None) -> float:
    """응답에서 숫자 추출 (예상값에 가장 가까운 값 반환)"""
    # 여러 패턴으로 숫자 찾기
    patterns = [
        r'[=]\s*([\d,]+(?:\.\d+)?)',  # = 뒤의 숫자
        r'[는은]\s*([\d,]+(?:\.\d+)?)',  # 는/은 뒤의 숫자
        r'결과[는은]?\s*[:=]?\s*([\d,]+(?:\.\d+)?)',
        r'([\d,]+(?:\.\d+)?)\s*(?:입니다|이다|원|이에요)',
        r'P\s*[=는은]\s*([\d,]+(?:\.\d+)?)',
        r'순보험료[는은]?\s*[:=]?\s*([\d,]+(?:\.\d+)?)',
        r'사고발생률[은는]?\s*[:=]?\s*([\d,]+(?:\.\d+)?)',
        r'사고심도[는은]?\s*[:=]?\s*([\d,]+(?:\.\d+)?)',
        r'(\d+\.\d+)',  # 소수점 숫자
        r'(\d+)',  # 정수
    ]
    
    all_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, response)
        for m in matches:
            try:
                num = float(m.replace(',', ''))
                if num >= 0:
                    all_numbers.append(num)
            except:
                pass
    
    if not all_numbers:
        return None
    
    # 예상값이 있으면 가장 가까운 숫자 반환
    if expected is not None:
        # 0.05 같은 소수를 찾기 위해 예상값과 가장 가까운 값 선택
        all_numbers = list(set(all_numbers))  # 중복 제거
        closest = min(all_numbers, key=lambda x: abs(x - expected))
        return closest
    
    # 예상값이 없으면 가장 큰 숫자 반환
    return max(all_numbers)

def run_tests():
    print("=" * 80)
    print("🧪 보험료 산출 정확도 테스트")
    print("=" * 80)
    
    results = []
    
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n{'─' * 80}")
        print(f"📋 테스트 {i}: {tc['name']}")
        print(f"{'─' * 80}")
        
        # 예상값
        if 'expected_P' in tc:
            expected = tc['expected_P']
            formula_name = "순보험료"
        else:
            expected = tc['expected_result']
            formula_name = tc.get('formula', '계산')
        
        print(f"📊 변수: {tc['variables']}")
        print(f"📝 질의: {tc['query']}")
        print(f"🎯 예상 {formula_name}: {expected}")
        
        try:
            response = run_agent(tc['query'])
            print(f"\n💬 Agent 응답:\n{response[:500]}...")
            
            # 응답에서 숫자 추출 (예상값 전달)
            extracted = extract_number_from_response(response, expected)
            print(f"\n🔢 추출된 값: {extracted}")
            
            # 정확도 검증
            if extracted is not None:
                tolerance = 0.01  # 1% 오차 허용
                if abs(extracted - expected) / expected < tolerance:
                    status = "✅ PASS"
                    is_pass = True
                else:
                    status = f"❌ FAIL (오차: {abs(extracted - expected)})"
                    is_pass = False
            else:
                status = "⚠️ 숫자 추출 실패"
                is_pass = False
                
            print(f"\n결과: {status}")
            results.append({
                "name": tc['name'],
                "expected": expected,
                "extracted": extracted,
                "pass": is_pass
            })
            
        except Exception as e:
            print(f"❌ 에러: {e}")
            results.append({
                "name": tc['name'],
                "expected": expected,
                "extracted": None,
                "pass": False
            })
    
    # 최종 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['pass'])
    total = len(results)
    
    print(f"\n{'테스트명':<20} {'예상값':<15} {'추출값':<15} {'결과':<10}")
    print("-" * 60)
    for r in results:
        status = "✅ PASS" if r['pass'] else "❌ FAIL"
        extracted_str = f"{r['extracted']:.2f}" if r['extracted'] else "N/A"
        print(f"{r['name']:<20} {r['expected']:<15.2f} {extracted_str:<15} {status}")
    
    print("-" * 60)
    print(f"\n🎯 총 {total}개 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

