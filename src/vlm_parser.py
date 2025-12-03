import base64
import io
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.config import OPENAI_API_KEY

class VLMParser:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, max_tokens=1024)

    def encode_image(self, image):
        """Encodes a PIL Image to base64."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def parse_formula(self, image):
        """Parses a formula from an image into JSON AST."""
        base64_image = self.encode_image(image)
        
        prompt = """
        Analyze the image and extract any mathematical formulas.
        Return the result in the following JSON format:
        {
            "type": "formula",
            "lhs": "Left Hand Side variable",
            "rhs": ["Right Hand Side terms"],
            "variables": ["List of all variables used"],
            "latex": "LaTeX representation"
        }
        If no formula is found, return null.
        """
        
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
        return response.content

    def extract_text_and_structure(self, image):
        """Extracts text and structural elements (tables, headers) from a page image."""
        base64_image = self.encode_image(image)
        
        prompt = """
        Extract the text from this page. Identify sections, definitions, and tables.
        Return a markdown string.
        """
        
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
        return response.content

