from sqlmodel import Field, Relationship
from typing import Optional, List
from app.model.base_model import BaseModel
from app.model.visualization import Visualization

class Dataset(BaseModel, table=True):
    filename: str = Field(index=True)
    table_name: str = Field(unique=True, index=True)
    columns_metadata: str = Field(default="{}", description="JSON string of column metadata")
    
    visualizations: List["Visualization"] = Relationship(back_populates="dataset")
