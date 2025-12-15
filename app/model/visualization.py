from sqlmodel import Field, Relationship
from typing import Optional, Dict, Any
from app.model.base_model import BaseModel
from sqlalchemy import Column, JSON

class Visualization(BaseModel, table=True):
    dataset_id: int = Field(foreign_key="dataset.id", index=True, nullable=False)
    prompt: str = Field(nullable=False)
    chart_config: Dict[str, Any] = Field(sa_column=Column(JSON), default={})
    explanation: Optional[str] = Field(default=None)
    sql_query: Optional[str] = Field(default=None)

    dataset: "Dataset" = Relationship(back_populates="visualizations")
