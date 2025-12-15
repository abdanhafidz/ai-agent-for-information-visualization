from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.services.dataset_service import DatasetService
from app.schema.dataset_schema import DatasetResponse, FindDataset
from app.schema.base_schema import FindResult
from app.core.container import Container
from dependency_injector.wiring import inject, Provide

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

@router.get("/", response_model=FindResult)
@inject
async def get_datasets(
    find_query: FindDataset = Depends(),
    service: DatasetService = Depends(Provide[Container.dataset_service]),
):
    return service.get_list(find_query)

@router.post("/upload", response_model=DatasetResponse)
@inject
async def upload_dataset(
    file: UploadFile = File(...),
    service: DatasetService = Depends(Provide[Container.dataset_service]),
):
    content = await file.read()
    try:
        return service.upload_dataset(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/preview")
@inject
async def get_dataset_preview(
    dataset_id: int,
    service: DatasetService = Depends(Provide[Container.dataset_service]),
):
    try:
        return service.get_preview(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
