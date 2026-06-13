from pydantic import BaseModel

from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse


class HistoryListItem(BaseModel):
    id: int
    title: str
    category: str
    overall_score: int
    created_at: str


class HistoryListResponse(BaseModel):
    items: list[HistoryListItem]
    total: int


class HistoryDetail(BaseModel):
    id: int
    input: DiagnosisRequest
    output: DiagnosisResponse
    title: str
    category: str
    overall_score: int
    created_at: str


class MarkdownExportResponse(BaseModel):
    filename: str
    markdown: str
