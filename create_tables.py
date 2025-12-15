from sqlmodel import SQLModel, create_engine
from app.core.config import configs
# Import all models to ensure they are registered in metadata
from app.model.dataset import Dataset
from app.model.visualization import Visualization

def create_db_and_tables():
    url = configs.DATABASE_URI
    print(f"Connecting to DB...")
    # SQLModel create_engine wrapper around sqlalchemy create_engine
    engine = create_engine(url)
    SQLModel.metadata.create_all(engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_db_and_tables()
