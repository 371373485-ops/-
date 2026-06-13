from app.schemas.history import HistoryDetail, HistoryListResponse, MarkdownExportResponse
from app.services.history_service import delete_history, export_history_markdown, get_history, list_history
from fastapi import APIRouter


router = APIRouter()


@router.get("", response_model=HistoryListResponse)
def read_history() -> HistoryListResponse:
    return list_history()


@router.get("/{history_id}", response_model=HistoryDetail)
def read_history_detail(history_id: int) -> HistoryDetail:
    return get_history(history_id)


@router.get("/{history_id}/export", response_model=MarkdownExportResponse)
def export_history(history_id: int) -> MarkdownExportResponse:
    return export_history_markdown(history_id)


@router.delete("/{history_id}")
def remove_history(history_id: int) -> dict[str, bool]:
    return delete_history(history_id)
