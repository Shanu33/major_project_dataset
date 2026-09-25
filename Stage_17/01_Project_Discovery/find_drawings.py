import os
import fitz

def search_pdfs(root_dir):
    results = []
    for root, _, files in os.walk(root_dir):
        if "Stage_" in root: continue
        for f in files:
            if f.lower().endswith(".pdf"):
                path = os.path.join(root, f)
                try:
                    doc = fitz.open(path)
                    if len(doc) == 0: continue
                    text = doc[0].get_text("text").lower()
                    if "drawing" in text or "boq" in text or "bill of quantities" in text or "schedule" in text:
                        # try to find images
                        img_count = sum(len(page.get_images()) for page in doc[:min(5, len(doc))])
                        results.append(f"{path} | Pages: {len(doc)} | Images in first 5 pages: {img_count}")
                except Exception as e:
                    pass
    with open("/home/shahnawaz/Documents/DataRequirement/Stage_17/01_Project_Discovery/pdf_scan_results.txt", "w") as out:
        for r in results: out.write(r + "\n")

search_pdfs("/home/shahnawaz/Documents/DataRequirement")
