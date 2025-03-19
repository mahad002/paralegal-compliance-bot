from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid
from typing import Dict, Optional, List
import uvicorn

from agents_pipeline import orchestration_agent, run_due_diligence_pipeline

app = FastAPI(title="Due Diligence Chatbot API", 
              description="API for Pakistani legal due diligence chatbot with guardrails")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for ongoing and completed requests
requests_store: Dict[str, Dict] = {}

# Input model for due diligence requests
class DueDiligenceRequest(BaseModel):
    scope: str
    jurisdictions: str
    concerns: str

# Response models
class DueDiligenceResponse(BaseModel):
    request_id: str
    status: str = "processing"
    
class DueDiligenceResult(BaseModel):
    request_id: str
    status: str
    result: Optional[str] = None
    guardrail_violated: bool = False
    error: Optional[str] = None

class DueDiligenceStatus(BaseModel):
    request_id: str
    status: str

# Format user input from the structured request
def format_user_input(request: DueDiligenceRequest) -> str:
    return f"""
Scope of due diligence request:
{request.scope}

Relevant jurisdictions:
{request.jurisdictions}

Main areas of concern:
{request.concerns}
"""

# Background task to process due diligence requests
async def process_due_diligence(request_id: str, user_input: str):
    try:
        result, guardrail_violated = await run_due_diligence_pipeline(orchestration_agent, user_input)
        
        # Update the request store with the result
        requests_store[request_id].update({
            "status": "completed",
            "result": result,
            "guardrail_violated": guardrail_violated
        })
    except Exception as e:
        # Handle any errors
        requests_store[request_id].update({
            "status": "error",
            "error": str(e)
        })

@app.post("/due-diligence", response_model=DueDiligenceResponse)
async def submit_due_diligence(request: DueDiligenceRequest, background_tasks: BackgroundTasks):
    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    
    # Format the user input
    user_input = format_user_input(request)
    
    # Store the request with initial status
    requests_store[request_id] = {
        "status": "processing",
        "input": user_input
    }
    
    # Process the request in the background
    background_tasks.add_task(process_due_diligence, request_id, user_input)
    
    return DueDiligenceResponse(request_id=request_id)

@app.get("/due-diligence/{request_id}", response_model=DueDiligenceResult)
async def get_due_diligence_result(request_id: str):
    if request_id not in requests_store:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request_data = requests_store[request_id]
    
    return DueDiligenceResult(
        request_id=request_id,
        status=request_data["status"],
        result=request_data.get("result"),
        guardrail_violated=request_data.get("guardrail_violated", False),
        error=request_data.get("error")
    )

@app.get("/due-diligence", response_model=List[DueDiligenceStatus])
async def list_due_diligence_requests():
    return [
        DueDiligenceStatus(request_id=req_id, status=data["status"])
        for req_id, data in requests_store.items()
    ]

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 