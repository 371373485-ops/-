from fastapi import APIRouter

from app.agents.similar_case_agent import SimilarCaseAgent
from app.schemas.case import CaseMatchResponse
from app.schemas.diagnosis import DiagnosisRequest


router = APIRouter()


@router.post("/match", response_model=CaseMatchResponse)
def match_cases(payload: DiagnosisRequest) -> CaseMatchResponse:
    return SimilarCaseAgent().match(payload)
