from typing import Optional
from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo, FindBase

class DatasetBase(BaseModel):
    filename: str
    table_name: str
    columns_metadata: Optional[str] = None

class DatasetCreate(BaseModel):
    filename: str
    table_name: str
    columns_metadata: Optional[str] = "{}"

class FindDataset(FindBase):
    filename: Optional[str] = None
    table_name: Optional[str] = None

class DatasetResponse(ModelBaseInfo, DatasetBase):
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "filename": "titanic.csv",
                "table_name": "dataset_123456_titanic",
                "columns_metadata": "{\"PassengerId\": \"int64\", \"Survived\": \"int64\", \"Pclass\": \"int64\"}",
                "created_at": "2023-10-27T10:00:00Z",
                "updated_at": "2023-10-27T10:00:00Z"
            }
        }
