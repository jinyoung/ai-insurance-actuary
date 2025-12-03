import fitz  # PyMuPDF
from PIL import Image
from src.vlm_parser import VLMParser
import os

class PDFIngestion:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.vlm = VLMParser()

    def process(self, max_pages=3):
        """
        Process the PDF:
        1. Convert to images (using PyMuPDF)
        2. Use VLM to extract text and formulas
        3. Return structured chunks
        
        max_pages: Limit processing for testing/cost reasons (default 3)
        """
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        chunks = []
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            print(f"Opened PDF with {total_pages} pages. Processing up to {max_pages} pages.")
            
            for i in range(min(total_pages, max_pages)):
                print(f"Processing page {i+1}...")
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                import io
                image = Image.open(io.BytesIO(img_data))
                
                # 1. Extract general text/structure
                page_content = self.vlm.extract_text_and_structure(image)
                
                # 2. Extract formulas (Optional specific pass, but we can rely on the first pass for now or add a second specific one)
                # For better quality, we might ask for formula ASTs specifically if the text suggests complex math.
                formulas = self.vlm.parse_formula(image)
                
                chunk = {
                    "page": i + 1,
                    "content": page_content,
                    "formulas_raw": formulas
                }
                chunks.append(chunk)
                
            doc.close()
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            import traceback
            traceback.print_exc()
            return []

        return chunks

if __name__ == "__main__":
    # Test with a dummy file if exists
    pass
