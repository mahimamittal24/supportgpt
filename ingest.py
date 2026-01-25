import os
import uuid
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

search_client = SearchClient(
    endpoint=os.getenv("SEARCH_ENDPOINT"),
    index_name="support-index",
    credential=AzureKeyCredential(os.getenv("SEARCH_KEY"))
)

documents = []

with open("data/support_docs.txt", "r") as file:
    for line in file:
        if line.strip():
            documents.append({
                "id": str(uuid.uuid4()),
                "content": line.strip(),
                "source": "dummy_support_data"
            })

search_client.upload_documents(documents)
print("✅ Support data uploaded successfully")
