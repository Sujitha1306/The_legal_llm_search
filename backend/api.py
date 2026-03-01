from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from local_search_llm_v2 import OllamaSearchAgent
import asyncio

app = FastAPI()

# Enable CORS so the React app (localhost:3000/3001) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    sites: list[str]
    model: str = 'qwen3:4b-instruct'

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.sites:
        raise HTTPException(status_code=400, detail="Must provide at least one site URL.")
    if not req.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        # We process this in a thread since OllamaSearchAgent is highly synchronous (requests.get, etc.)
        def run_agent():
            agent = OllamaSearchAgent(whitelist_urls=req.sites, model=req.model)
            # The query method expects a string question and handles scraping/context via Ollama sync
            return agent.query(req.query)

        result = await asyncio.to_thread(run_agent)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
