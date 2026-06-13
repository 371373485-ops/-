from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.case import MatchedSample


ImpactArea = Literal["click", "completion", "trust", "interaction", "compliance"]
ExtendedImpactArea = Literal["click", "completion", "collection", "trust", "interaction", "compliance"]
ConfidenceLevel = Literal["high", "medium", "low"]
SeverityLevel = Literal["low", "medium", "high"]


class DiagnosisRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=80)
    target_audience: str = Field(..., min_length=1, max_length=120)
    goal: str = Field(..., min_length=1, max_length=40)
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    cover_text: str | None = Field(default=None, max_length=120)
    comment_guide: str | None = Field(default=None, max_length=240)


class MissingInputAnswer(BaseModel):
    field: str = Field(..., min_length=1, max_length=80)
    answer: str = Field(..., min_length=1, max_length=1000)


class DiagnosisRefineRequest(BaseModel):
    original_payload: DiagnosisRequest
    missing_answers: list[MissingInputAnswer] = Field(default_factory=list)


class ScoreItem(BaseModel):
    name: str
    key: str | None = None
    score: int = Field(..., ge=0, le=100)
    weight: float | None = Field(default=None, ge=0, le=1)
    reason: str
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    level: str
    message: str


class RiskEvidenceItem(BaseModel):
    field: str
    triggered_text: str
    risk_type: str
    reason: str
    severity: SeverityLevel
    suggested_rewrite: str


class EvidenceFinding(BaseModel):
    priority: str = Field(..., pattern="^P[0-3]$")
    dimension: str
    source: str
    evidence: str
    issue: str
    impact: str
    action: str


class PriorityAction(BaseModel):
    priority: int = Field(..., ge=1, le=5)
    action: str
    reason: str
    expected_effect: str


class TopBlocker(BaseModel):
    rank: int = Field(..., ge=1, le=3)
    field: str
    issue: str
    evidence: str
    severity: SeverityLevel
    why_it_blocks: str
    suggested_focus: str


class EvidenceBasedIssue(BaseModel):
    field: str
    original_excerpt: str
    issue: str
    why_it_matters: str
    impact_area: ImpactArea
    severity: SeverityLevel
    rewrite_principle: str
    example_fix: str


class DiagnosisEvidenceSource(BaseModel):
    field: str
    provided: bool
    confidence: ConfidenceLevel
    note: str


class ScoreDeduction(BaseModel):
    dimension: str
    points_lost: int
    reason: str
    evidence: str
    improvement_path: str


class ScoreExplanation(BaseModel):
    score: int = Field(..., ge=0, le=100)
    band: str
    interpretation: str
    main_loss_factors: list[str] = Field(default_factory=list)
    next_score_goal: str
    disclaimer: str


class EvidenceDiagnosisItem(BaseModel):
    field: str
    evidence: str
    judgement: str
    why_it_matters: str
    impact_area: ExtendedImpactArea
    confidence: ConfidenceLevel
    severity: SeverityLevel
    revision_principle: str
    example_fix: str
    needs_user_input: bool = False


class ReaderPerspective(BaseModel):
    stage: Literal["feed", "title", "opening", "body", "ending", "risk"]
    likely_reaction: str
    trust_change: str
    action_intent: str
    evidence: str


class RevisionTask(BaseModel):
    rank: int
    title: str
    target_field: str
    reason: str
    evidence: str
    expected_effect: ExtendedImpactArea
    suggested_action: str
    status: Literal["todo", "done"] = "todo"


class ReaderReactionSimulation(BaseModel):
    title_first_impression: str
    after_first_three_lines: str
    likely_drop_off_reason: str
    strongest_interest_point: str
    information_to_frontload: list[str] = Field(default_factory=list)


class StructureAnalysis(BaseModel):
    opening_hook: str
    information_hierarchy: str
    trust_building: str
    detail_evidence: str
    emotional_resonance: str
    action_guidance: str


class CredibilityReview(BaseModel):
    is_too_generic: bool
    sounds_like_ad: bool
    missing_trust_signals: list[str] = Field(default_factory=list)
    strong_trust_signals: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class MissingUserInput(BaseModel):
    field: str
    reason: str
    suggested_prompt: str


class RewrittenVersions(BaseModel):
    titles: list[str] = Field(default_factory=list)
    body: str = ""
    tags: list[str] = Field(default_factory=list)
    cover_text: list[str] = Field(default_factory=list)
    comment_guides: list[str] = Field(default_factory=list)


class RewriteExplanation(BaseModel):
    target: str
    original_excerpt: str
    rewritten_excerpt: str
    reason: str
    expected_effect: ImpactArea
    source_issue_field: str | None = None
    source_evidence: str | None = None
    linked_revision_task_rank: int | None = None


class RiskReviewSummary(BaseModel):
    risk_level: SeverityLevel = "low"
    overall_level: SeverityLevel = "low"
    risk_items: list[RiskEvidenceItem] = Field(default_factory=list)
    safe_alternatives: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    risks: list[RiskItem] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class SampleInsight(BaseModel):
    sample_count: int
    reusable_structures: list[str] = Field(default_factory=list)
    opening_patterns: list[str] = Field(default_factory=list)
    title_patterns: list[str] = Field(default_factory=list)
    trust_signals: list[str] = Field(default_factory=list)
    caution: str


class DiagnosisResponse(BaseModel):
    diagnosis_id: str = Field(default_factory=lambda: str(uuid4()))
    overall_score: int = Field(..., ge=0, le=100)
    category: str = ""
    summary: str
    scores: list[ScoreItem]
    diagnosis_sources: list[DiagnosisEvidenceSource] = Field(default_factory=list)
    score_deductions: list[ScoreDeduction] = Field(default_factory=list)
    score_explanation: ScoreExplanation | None = None
    evidence_diagnosis: list[EvidenceDiagnosisItem] = Field(default_factory=list)
    reader_perspectives: list[ReaderPerspective] = Field(default_factory=list)
    revision_tasks: list[RevisionTask] = Field(default_factory=list, max_length=3)
    top_3_blockers: list[TopBlocker] = Field(default_factory=list, max_length=3)
    evidence_based_issues: list[EvidenceBasedIssue] = Field(default_factory=list)
    reader_reaction_simulation: ReaderReactionSimulation | None = None
    structure_analysis: StructureAnalysis | None = None
    credibility_review: CredibilityReview | None = None
    missing_user_inputs: list[MissingUserInput] = Field(default_factory=list)
    rewritten_versions: RewrittenVersions = Field(default_factory=RewrittenVersions)
    rewrite_explanations: list[RewriteExplanation] = Field(default_factory=list)
    risk_review: RiskReviewSummary = Field(default_factory=RiskReviewSummary)
    ai_disclosure_notice: str = "当前结果可能由规则、mock 或真实 AI 生成；AI 输出仅供内容诊断参考，发布前请人工复核。"
    evidence_findings: list[EvidenceFinding] = Field(default_factory=list)
    priority_actions: list[PriorityAction] = Field(default_factory=list)
    problems: list[str]
    suggestions: list[str]
    rewritten_titles: list[str]
    optimized_body: str
    recommended_tags: list[str]
    cover_text: list[str]
    comment_guides: list[str]
    risks: list[RiskItem]
    matched_samples: list[MatchedSample] = Field(default_factory=list)
    case_match_message: str | None = None
    sample_insights: SampleInsight | None = None
    mode: str = "mock"
