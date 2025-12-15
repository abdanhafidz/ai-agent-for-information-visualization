from app.repository.dataset_repository import DatasetRepository
from app.services.base_service import BaseService
from app.schema.dataset_schema import DatasetCreate
import pandas as pd
import json
import io
import time

class DatasetService(BaseService):
    def __init__(self, repository: DatasetRepository):
        super().__init__(repository)

    def upload_dataset(self, file_content: bytes, filename: str):
        # Read file
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format")

        # Sanitize table name
        # Use a timestamp or uuid to avoid collision in real app, but for now simple sanitization
        
        table_name = f"dataset_{int(time.time())}_{filename.split('.')[0].replace(' ', '_').lower()}"
        
        # Extract metadata
        columns_metadata = df.dtypes.apply(lambda x: x.name).to_dict()
        
        # Create table
        self._repository.create_table_from_df(df, table_name)
        
        # Save metadata
        dataset_create = DatasetCreate(
            filename=filename,
            table_name=table_name,
            columns_metadata=json.dumps(columns_metadata)
        )
        return self.add(dataset_create)

    def get_preview(self, dataset_id: int):
        dataset = self.get_by_id(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        return self._repository.get_preview(dataset.table_name)
