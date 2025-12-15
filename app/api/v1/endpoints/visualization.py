from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from app.core.container import Container
from app.schema.visualization_schema import VisualizationCreate, VisualizationRead
from app.services.visualization_service import VisualizationService

router = APIRouter(
    prefix="/visualizations",
    tags=["visualizations"],
)

@router.post("/", response_model=VisualizationRead)
@inject
def create_visualization(
    schema: VisualizationCreate,
    service: VisualizationService = Depends(Provide[Container.visualization_service]),
):
    return service.create_visualization(schema)

@router.get("/dataset/{dataset_id}", response_model=list[VisualizationRead])
@inject
def get_dataset_visualizations(
    dataset_id: int,
    service: VisualizationService = Depends(Provide[Container.visualization_service]),
):
    return service.list_visualizations(dataset_id)

@router.get("/", response_model=list[VisualizationRead])
@inject
def get_visualizations(
    service: VisualizationService = Depends(Provide[Container.visualization_service]),
):
    return service.get_all_visualizations()

@router.get("/{dataset_id}", response_model=VisualizationRead | None)
@inject
def get_visualization(
    dataset_id: int,
    service: VisualizationService = Depends(Provide[Container.visualization_service]),
):
    return service.get_visualization(dataset_id)

@router.delete("/")
@inject
def delete_all_visualizations(
    service: VisualizationService = Depends(Provide[Container.visualization_service]),
):
    service.delete_all_visualizations()
    return {"message": "All visualizations deleted"}
