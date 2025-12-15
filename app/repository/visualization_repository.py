from app.repository.base_repository import BaseRepository
from app.model.visualization import Visualization

class VisualizationRepository(BaseRepository[Visualization]):
    def __init__(self, session_factory):
        super().__init__(session_factory, Visualization)

    def get_by_dataset_id(self, dataset_id: int) -> Visualization | None:
        with self.session_factory() as session:
            return session.query(self.model).filter(self.model.dataset_id == dataset_id).first()

    def get_all_by_dataset_id(self, dataset_id: int) -> list[Visualization]:
        with self.session_factory() as session:
            items = session.query(self.model).filter(self.model.dataset_id == dataset_id).all()
            for item in items:
                session.expunge(item)
            return items

    def delete_all(self):
        with self.session_factory() as session:
            session.query(self.model).delete()
            session.commit()
