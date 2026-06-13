from pydantic import BaseModel, Field

from app.schemas.case import CaseMatchResponse
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse, RiskEvidenceItem, RiskItem
from app.schemas.pattern import PatternAnalysisResponse


class AgentError(BaseModel):
    agent: str
    message: str


class ContentDiagnosisInput(BaseModel):
    payload: DiagnosisRequest
    use_ai: bool = False


class ContentDiagnosisOutput(BaseModel):
    diagnosis: DiagnosisResponse


class ViralPatternInput(BaseModel):
    category: str | None = None


class ViralPatternOutput(BaseModel):
    patterns: PatternAnalysisResponse
    references: list[str] = Field(default_factory=list)


class SimilarCaseInput(BaseModel):
    payload: DiagnosisRequest


class SimilarCaseOutput(BaseModel):
    cases: CaseMatchResponse


class TitleRewriteInput(BaseModel):
    payload: DiagnosisRequest
    pattern_references: list[str] = Field(default_factory=list)


class TitleRewriteOutput(BaseModel):
    strong_hook: str
    save_worthy: str
    contrast_conflict: str
    beginner_friendly: str
    workplace_version: str

    def as_list(self) -> list[str]:
        return [
            self.strong_hook,
            self.save_worthy,
            self.contrast_conflict,
            self.beginner_friendly,
            self.workplace_version,
        ]


class BodyRewriteInput(BaseModel):
    payload: DiagnosisRequest
    diagnosis_suggestions: list[str] = Field(default_factory=list)


class BodyRewriteOutput(BaseModel):
    optimized_body: str
    rewrite_notes: list[str]


class TagAndCoverInput(BaseModel):
    payload: DiagnosisRequest
    similar_tags: list[str] = Field(default_factory=list)


class TagAndCoverOutput(BaseModel):
    recommended_tags: list[str]
    cover_text: list[str]
    first_comment: str
    publish_time_suggestion: str


class RiskReviewInput(BaseModel):
    payload: DiagnosisRequest
    rewritten_titles: list[str] = Field(default_factory=list)
    optimized_body: str = ""


class RiskReviewOutput(BaseModel):
    risk_level: str
    risk_items: list[RiskEvidenceItem] = Field(default_factory=list)
    safe_alternatives: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    risks: list[RiskItem]
    revision_suggestions: list[str]


class FinalReportInput(BaseModel):
    payload: DiagnosisRequest
    diagnosis: DiagnosisResponse
    title_rewrite: TitleRewriteOutput | None = None
    body_rewrite: BodyRewriteOutput | None = None
    tag_cover: TagAndCoverOutput | None = None
    risk_review: RiskReviewOutput | None = None
    similar_cases: CaseMatchResponse | None = None
    errors: list[AgentError] = Field(default_factory=list)


class FinalReportOutput(BaseModel):
    report: DiagnosisResponse


class WorkflowTraceItem(BaseModel):
    agent: str
    status: str
    message: str | None = None
