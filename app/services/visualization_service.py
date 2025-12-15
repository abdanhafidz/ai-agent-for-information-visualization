from app.repository.visualization_repository import VisualizationRepository
from app.schema.visualization_schema import VisualizationCreate, VisualizationRead
from app.model.visualization import Visualization

class VisualizationService:
    def __init__(self, repository: VisualizationRepository):
        self.repository = repository

    def create_visualization(self, data: VisualizationCreate) -> Visualization:
        # Always create new
        viz = Visualization(**data.dict())
        return self.repository.create(viz)

    def list_visualizations(self, dataset_id: int) -> list[Visualization]:
        return self.repository.get_all_by_dataset_id(dataset_id)

    def get_visualization(self, dataset_id: int) -> Visualization | None:
        return self.repository.get_by_dataset_id(dataset_id)
    
    def get_all_visualizations(self) -> list[Visualization]:
        return self.repository.read_list()

    def delete_all_visualizations(self):
        self.repository.delete_all()
