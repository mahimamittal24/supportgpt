import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

app = FastAPI(title="SupportGPT")

# ---------- Models ----------
class AskRequest(BaseModel):
    session_id: str
    question: str


# ---------- Azure Search ----------
search_client = SearchClient(
    endpoint=os.getenv("SEARCH_ENDPOINT"),
    index_name="support-index",
    credential=AzureKeyCredential(os.getenv("SEARCH_KEY"))
)

# ---------- Azure OpenAI ----------
llm_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-15-preview"
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")


# ---------- API ----------
@app.post("/ask")
def ask(req: AskRequest):
    try:
        # 1. Retrieve documents
        results = search_client.search(
            req.question,
            top=3,
            include_total_count=True
        )

        context_chunks = []
        sources = []

        for r in results:
            context_chunks.append(
                f"[Source: {r['source']} | Page: {r['page']}]\n{r['content']}"
            )
            sources.append({
                "source": r["source"],
                "page": r["page"],
                "score": r["@search.score"]
            })

        if not context_chunks:
            return {
                "session_id": req.session_id,
                "question": req.question,
                "answer": "I don't know.",
                "sources": []
            }

        context = "\n\n".join(context_chunks)

        # 2. Call Azure OpenAI
        response = llm_client.chat.completions.create(
            model=DEPLOYMENT_NAME,  # 🔥 THIS FIXES YOUR 404
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a customer support assistant. "
                        "Answer ONLY using the provided context. "
                        "Cite page numbers in your answer. "
                        "If the answer is not present, say 'I don't know'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion:\n{req.question}"
                }
            ],
            temperature=0
        )

        return {
            "session_id": req.session_id,
            "question": req.question,
            "answer": response.choices[0].message.content,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
