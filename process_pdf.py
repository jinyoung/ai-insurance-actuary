import json
import os
from src.ingestion import PDFIngestion

def run_processing():
    pdf_path = "data/nre2007-02_02-1.pdf"
    
    print(f"Starting ingestion for {pdf_path}...")
    ingestion = PDFIngestion(pdf_path)
    
    # Process only first 2 pages for testing to save API costs and time
    chunks = ingestion.process(max_pages=2)
    
    output_file = "graph_data_chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    print(f"Processing complete. Data saved to {output_file}")
    
    # Print a preview
    if chunks:
        print("\n--- Page 1 Preview ---")
        print(chunks[0]["content"][:500] + "...")
        print("\n--- Formula Extraction Preview ---")
        print(chunks[0].get("formulas_raw"))

if __name__ == "__main__":
    run_processing()

