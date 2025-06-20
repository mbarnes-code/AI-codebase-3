from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import ollama

app = FastAPI()

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama2"
    options: dict = {}

class GenerateResponse(BaseModel):
    response: str

@app.post("/generate", response_model=GenerateResponse)
def generate_text(req: GenerateRequest):
    try:
        # Call Ollama API (assumes Ollama is running locally or in Docker)
        result = ollama.generate(model=req.model, prompt=req.prompt, options=req.options)
        return {"response": result["response"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
