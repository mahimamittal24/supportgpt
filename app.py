import os
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

app = FastAPI(title="SupportGPT")

# Azure AI Search client
search_client = SearchClient(
    endpoint=os.getenv("SEARCH_ENDPOINT"),
    index_name="support-index",
    credential=AzureKeyCredential(os.getenv("SEARCH_KEY"))
)

# Azure OpenAI client
llm_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)

@app.get("/ask")
def ask(question: str):
    # 1. Retrieve relevant documents
    search_results = search_client.search(question, top=3)

    context_chunks = []
    for result in search_results:
        context_chunks.append(result["content"])

    context = "\n".join(context_chunks)

    # 2. Generate grounded answer
    response = llm_client.chat.completions.create(
        model="support-gpt",  # deployment name
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer support assistant. "
                    "Answer ONLY using the provided context. "
                    "If the answer is not in the context, say you don't know."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}"
            }
        ],
        temperature=0
    )

    return {
        "question": question,
        "answer": response.choices[0].message.content
    }
