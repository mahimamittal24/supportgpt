import os
import uuid
from pypdf import PdfReader
from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# --------------------
# Load env
# --------------------
load_dotenv()

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = "support-index"

PDF_DIR = "data/pdfs"

# --------------------
# Search client
# --------------------
search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)

def ingest_pdfs():
    documents = []

    for pdf_file in os.listdir(PDF_DIR):
        if not pdf_file.endswith(".pdf"):
            continue

        print(f"Processing {pdf_file}")
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        reader = PdfReader(pdf_path)

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if not text or len(text.strip()) < 40:
                continue

            documents.append({
                "id": str(uuid.uuid4()),
                "content": text.strip(),
                "source": pdf_file,
                "page": page_number   # MUST be int
            })

    if not documents:
        print("No content extracted.")
        return

    search_client.upload_documents(documents)
    print(f"Uploaded {len(documents)} chunks to Azure AI Search")

if __name__ == "__main__":
    ingest_pdfs()
