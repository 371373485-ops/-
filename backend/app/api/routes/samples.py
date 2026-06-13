from fastapi import APIRouter, File, Query, UploadFile

from app.schemas.sample import SampleImportResponse, SampleItem, SampleListResponse
from app.services.sample_service import delete_sample, get_sample, import_samples_csv, list_samples


router = APIRouter()


@router.post("/import", response_model=SampleImportResponse)
async def import_samples(file: UploadFile = File(...)) -> SampleImportResponse:
    return await import_samples_csv(file)


@router.get("", response_model=SampleListResponse)
def read_samples(
    category: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
) -> SampleListResponse:
    return list_samples(category=category, source_type=source_type)


@router.get("/{sample_id}", response_model=SampleItem)
def read_sample(sample_id: int) -> SampleItem:
    return get_sample(sample_id)


@router.delete("/{sample_id}")
def remove_sample(sample_id: int) -> dict[str, bool]:
    return delete_sample(sample_id)
