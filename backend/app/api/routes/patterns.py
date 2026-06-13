from fastapi import APIRouter, Query

from app.schemas.pattern import PatternAnalysisResponse
from app.services.pattern_service import analyze_patterns


router = APIRouter()


@router.get("/analyze", response_model=PatternAnalysisResponse)
def analyze_pattern_endpoint(category: str | None = Query(default=None)) -> PatternAnalysisResponse:
    return analyze_patterns(category=category)
