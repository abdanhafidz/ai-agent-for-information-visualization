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
            result = service.mock_analyze(request.prompt, request.dataset_id)
        else:
            result = service.analyze(request.prompt, request.dataset_id)
            
        return AgentResponse(
            chart_config=result.get("chart_config"),
            explanation=result.get("explanation"),
            sql_query=result.get("sql_query"),
            query_result=result.get("query_result")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
