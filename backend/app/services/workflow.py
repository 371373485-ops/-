from collections.abc import Callable
from typing import TypeVar

from app.agents.body_rewrite_agent import BodyRewriteAgent
from app.agents.content_diagnosis_agent import ContentDiagnosisAgent
from app.agents.final_report_agent import FinalReportAgent
from app.agents.risk_review_agent import RiskReviewAgent
from app.agents.similar_case_agent import SimilarCaseAgent
from app.agents.tag_cover_agent import TagAndCoverAgent
from app.agents.title_rewrite_agent import TitleRewriteAgent
from app.agents.viral_pattern_agent import ViralPatternAgent
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.schemas.workflow import (
    AgentError,
    BodyRewriteInput,
    ContentDiagnosisInput,
    ContentDiagnosisOutput,
    FinalReportInput,
    RiskReviewInput,
    SimilarCaseInput,
    TagAndCoverInput,
    TitleRewriteInput,
    ViralPatternInput,
)
from app.services.scoring_service import build_rule_diagnosis


T = TypeVar("T")


class DiagnosisWorkflow:
    def __init__(self) -> None:
        self.content_agent = ContentDiagnosisAgent()
        self.pattern_agent = ViralPatternAgent()
        self.case_agent = SimilarCaseAgent()
        self.title_agent = TitleRewriteAgent()
        self.body_agent = BodyRewriteAgent()
        self.tag_cover_agent = TagAndCoverAgent()
        self.risk_agent = RiskReviewAgent()
        self.final_agent = FinalReportAgent()

    def run(self, payload: DiagnosisRequest, use_ai: bool = False) -> DiagnosisResponse:
        errors: list[AgentError] = []

        content_output = self._safe_run(
            self.content_agent.name,
            lambda: self.content_agent.run(ContentDiagnosisInput(payload=payload, use_ai=use_ai)),
            errors,
        )
        if not content_output:
            content_output = ContentDiagnosisOutput(diagnosis=build_rule_diagnosis(payload))
            errors.append(AgentError(agent=self.content_agent.name, message="已降级为规则诊断。"))

        pattern_output = self._safe_run(
            self.pattern_agent.name,
            lambda: self.pattern_agent.run(ViralPatternInput(category=payload.category)),
            errors,
        )

        case_output = self._safe_run(
            self.case_agent.name,
            lambda: self.case_agent.run(SimilarCaseInput(payload=payload)),
            errors,
        )

        title_output = self._safe_run(
            self.title_agent.name,
            lambda: self.title_agent.run(
                TitleRewriteInput(
                    payload=payload,
                    pattern_references=pattern_output.references if pattern_output else [],
                )
            ),
            errors,
        )

        body_output = self._safe_run(
            self.body_agent.name,
            lambda: self.body_agent.run(BodyRewriteInput(payload=payload, diagnosis_suggestions=content_output.diagnosis.suggestions)),
            errors,
        )

        similar_tags = []
        if case_output:
            for sample in case_output.cases.matched_samples:
                similar_tags.extend(sample.tags)
        tag_cover_output = self._safe_run(
            self.tag_cover_agent.name,
            lambda: self.tag_cover_agent.run(TagAndCoverInput(payload=payload, similar_tags=similar_tags)),
            errors,
        )

        risk_output = self._safe_run(
            self.risk_agent.name,
            lambda: self.risk_agent.run(
                RiskReviewInput(
                    payload=payload,
                    rewritten_titles=title_output.as_list() if title_output else content_output.diagnosis.rewritten_titles,
                    optimized_body=body_output.optimized_body if body_output else content_output.diagnosis.optimized_body,
                )
            ),
            errors,
        )

        final_output = self.final_agent.run(
            FinalReportInput(
                payload=payload,
                diagnosis=content_output.diagnosis,
                title_rewrite=title_output,
                body_rewrite=body_output,
                tag_cover=tag_cover_output,
                risk_review=risk_output,
                similar_cases=case_output.cases if case_output else None,
                errors=errors,
            )
        )
        return final_output.report

    def _safe_run(self, agent_name: str, fn: Callable[[], T], errors: list[AgentError]) -> T | None:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - workflow must degrade instead of crashing
            errors.append(AgentError(agent=agent_name, message=str(exc)))
            return None
