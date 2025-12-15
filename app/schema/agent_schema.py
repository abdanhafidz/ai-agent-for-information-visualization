from typing import Optional, Dict, Any
from pydantic import BaseModel

class AgentRequest(BaseModel):
    prompt: str
    dataset_ids: list[int]

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Show me the survival rate by class",
                "dataset_ids": [1, 2]
            }
        }

class SingleAgentResult(BaseModel):
    dataset_id: int
    chart_config: Optional[Dict[str, Any]] = None
    explanation: str
    sql_query: Optional[str] = None
    query_result: Optional[str] = None

class AgentResponse(BaseModel):
    results: list[SingleAgentResult]

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "dataset_id": 1,
                        "chart_config": {
                            "data": [{"x": [1, 2], "y": [3, 4], "type": "bar"}],
                            "layout": {"title": "Chart 1"}
                        },
                        "explanation": "Explanation 1",
                        "sql_query": "SELECT * FROM t1"
                    }
                ]
            }
        }
