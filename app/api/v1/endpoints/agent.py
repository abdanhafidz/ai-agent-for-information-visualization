from fastapi import APIRouter, Depends, HTTPException
from app.services.agent_service import AgentService
from app.schema.agent_schema import AgentRequest, AgentResponse
from app.core.container import Container
from dependency_injector.wiring import inject, Provide

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)

@router.post("/analyze", response_model=AgentResponse)
@inject
async def analyze_data(
    request: AgentRequest,
    mock: bool = False,
    service: AgentService = Depends(Provide[Container.agent_service]),
):
    try:
        if mock:
            # result = service.mock_analyze(request.prompt, request.dataset_ids) # Mock not implemented for multi yet
            # Fallback for now or raise error? User wants real inference mostly.
            # Let's just use real analyze for now or empty list
             result = [] 
        else:
            result = service.analyze(request.prompt, request.dataset_ids)
            
        return AgentResponse(results=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
