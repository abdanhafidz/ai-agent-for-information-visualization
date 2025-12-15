from typing import Optional, Dict, Any
from pydantic import BaseModel

class AgentRequest(BaseModel):
    prompt: str
    dataset_id: int

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Show me the survival rate by class",
                "dataset_id": 1
            }
        }

class AgentResponse(BaseModel):
    chart_config: Optional[Dict[str, Any]] = None
    explanation: str
    sql_query: Optional[str] = None
    query_result: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "chart_config": {
                    "data": [
                        {"x": ["1st", "2nd", "3rd"], "y": [0.63, 0.47, 0.24], "type": "bar", "name": "Survival Rate"}
                    ],
                    "layout": {"title": "Survival Rate by Class", "xaxis": {"title": "Class"}, "yaxis": {"title": "Rate"}}
                },
                "explanation": "The chart shows that 1st class passengers had the highest survival rate (63%), followed by 2nd class (47%) and 3rd class (24%).",
                "sql_query": "SELECT Pclass, AVG(Survived) FROM dataset_123456_titanic GROUP BY Pclass"
            }
        }
