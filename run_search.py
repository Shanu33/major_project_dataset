from googlesearch import search
import time

queries = [
    'tender "structural drawings" "schedule of quantities" filetype:pdf',
    '"structural drawings" "BOQ" civil works filetype:pdf',
    'tender "structural drawings" "bill of quantities" filetype:pdf'
]

urls = []
for q in queries:
    try:
        print(f"Searching: {q}")
        results = search(q, num_results=15)
        for url in results:
            if url.lower().endswith('.pdf'):
                urls.append(url)
                print(f"Found: {url}")
        time.sleep(2)
    except Exception as e:
        print(f"Error: {e}")

with open('Stage_18/02_Source_Discovery/found_urls.txt', 'a') as f:
    for u in list(set(urls)):
        f.write(u + "\n")

print(f"Total unique PDFs found: {len(set(urls))}")
