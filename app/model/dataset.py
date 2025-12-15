from sqlmodel import Field
from app.model.base_model import BaseModel

class Dataset(BaseModel, table=True):
    filename: str = Field(index=True)
    table_name: str = Field(unique=True, index=True)
    columns_metadata: str = Field(default="{}", description="JSON string of column metadata")
