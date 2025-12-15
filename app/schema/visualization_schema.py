from pydantic import BaseModel
from typing import Optional, Dict, Any

class VisualizationBase(BaseModel):
    dataset_id: int
    prompt: str
    chart_config: Dict[str, Any]
    explanation: Optional[str] = None
    sql_query: Optional[str] = None

class VisualizationCreate(VisualizationBase):
    pass

class VisualizationRead(VisualizationBase):
    id: int
