import fitz  # PyMuPDF
from PIL import Image
from src.vlm_parser import VLMParser
import os
import io

class PDFIngestion:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.vlm = VLMParser()

    def process(self, max_pages=None, start_page=0):
        """
        Process the PDF:
        1. Convert to images (using PyMuPDF)
        2. Use VLM to extract text, structure, and formulas
        3. Return structured chunks
        
        max_pages: Limit processing (None = all pages)
        start_page: Start from this page (0-indexed)
        """
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        chunks = []
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            if max_pages is None:
                max_pages = total_pages
            
            end_page = min(start_page + max_pages, total_pages)
            print(f"📄 Opened PDF with {total_pages} pages.")
            print(f"📖 Processing pages {start_page + 1} to {end_page}...")
            
            for i in range(start_page, end_page):
                print(f"\n🔍 Processing page {i+1}/{total_pages}...")
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200)  # Higher DPI for better formula recognition
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Extract everything using VLM
                print(f"   📐 Extracting formulas...")
                formulas = self.vlm.parse_formulas(image)
                
                print(f"   📝 Extracting text structure...")
                structure = self.vlm.extract_text_and_structure(image)
                
                num_formulas = len(formulas.get("formulas", []))
                print(f"   ✅ Found {num_formulas} formulas")
                
                chunk = {
                    "page": i + 1,
                    "formulas": formulas.get("formulas", []),
                    "structure": structure,
                    "raw_formula_response": formulas.get("raw", None)
                }
                chunks.append(chunk)
                
            doc.close()
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            import traceback
            traceback.print_exc()
            return []

        return chunks

    def process_formulas_only(self, max_pages=None, start_page=0):
        """
        Process PDF focusing only on formula extraction (faster).
        """
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        all_formulas = []
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            if max_pages is None:
                max_pages = total_pages
            
            end_page = min(start_page + max_pages, total_pages)
            print(f"📄 PDF: {total_pages} pages, processing {start_page + 1} to {end_page}")
            
            for i in range(start_page, end_page):
                print(f"🔍 Page {i+1}...", end=" ", flush=True)
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200)
                
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                formulas = self.vlm.parse_formulas(image)
                formula_list = formulas.get("formulas", [])
                
                for f in formula_list:
                    f["source_page"] = i + 1
                    all_formulas.append(f)
                
                print(f"✅ {len(formula_list)} formulas")
                
            doc.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

        return all_formulas

if __name__ == "__main__":
    pass
