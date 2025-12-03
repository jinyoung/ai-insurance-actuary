import base64
import io
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.config import OPENAI_API_KEY

class VLMParser:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, max_tokens=4096)

    def encode_image(self, image):
        """Encodes a PIL Image to base64."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def parse_formulas(self, image):
        """Parses all formulas from an image into structured JSON."""
        base64_image = self.encode_image(image)
        
        prompt = """이 이미지에서 모든 수학 공식/수식을 찾아 추출하세요.

각 공식에 대해 다음 JSON 형식으로 반환하세요:
{
  "formulas": [
    {
      "name": "공식 이름 (한글)",
      "latex": "LaTeX 수식 표현",
      "expression": "Python으로 계산 가능한 표현식 (예: (I/N) * (L/B))",
      "description": "공식에 대한 설명",
      "variables": [
        {"name": "변수명", "latex": "LaTeX 변수", "description": "변수 설명", "unit": "단위"}
      ]
    }
  ]
}

주의사항:
1. 분수는 LaTeX에서 \\frac{분자}{분모}, Python에서 (분자)/(분모)로 표현
2. 그리스 문자: λ(lambda), μ(mu), γ(gamma), δ(delta), σ(sigma) 등
3. 적분, 시그마, 곱기호 등 수학 기호 정확히 추출
4. 수식이 없으면 {"formulas": []} 반환
5. 반드시 유효한 JSON만 반환하세요. 설명 텍스트 없이 JSON만 반환하세요.

이미지에서 수식을 찾아 JSON으로 반환하세요:"""
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ]
        )
        
        response = self.llm.invoke([message])
        
        # Parse JSON from response
        try:
            content = response.content
            # Clean up markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {"formulas": [], "raw": response.content}

    def extract_text_and_structure(self, image):
        """Extracts text and structural elements (sections, definitions) from a page image."""
        base64_image = self.encode_image(image)
        
        prompt = """이 페이지의 내용을 분석하여 다음 JSON 형식으로 반환하세요:

{
  "sections": [
    {
      "title": "섹션 제목",
      "content": "섹션 내용 텍스트"
    }
  ],
  "definitions": [
    {
      "term": "용어",
      "definition": "정의 설명"
    }
  ],
  "key_concepts": ["핵심 개념1", "핵심 개념2"],
  "full_text": "페이지 전체 텍스트"
}

반드시 유효한 JSON만 반환하세요."""
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ]
        )
        
        response = self.llm.invoke([message])
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except:
            return {"full_text": response.content, "sections": [], "definitions": []}

    def extract_all(self, image):
        """Extracts both text/structure and formulas from an image."""
        formulas = self.parse_formulas(image)
        structure = self.extract_text_and_structure(image)
        return {
            "formulas": formulas.get("formulas", []),
            "structure": structure
        }
