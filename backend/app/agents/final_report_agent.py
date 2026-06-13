from app.schemas.diagnosis import RiskReviewSummary
from app.schemas.workflow import FinalReportInput, FinalReportOutput
from app.services.rewrite_explanation_service import build_rewrite_explanations


class FinalReportAgent:
    name = "FinalReportAgent"

    def run(self, agent_input: FinalReportInput) -> FinalReportOutput:
        report = agent_input.diagnosis
        if agent_input.title_rewrite:
            report.rewritten_titles = agent_input.title_rewrite.as_list()
            report.rewritten_versions.titles = report.rewritten_titles
        if agent_input.body_rewrite:
            report.optimized_body = agent_input.body_rewrite.optimized_body
            report.rewritten_versions.body = report.optimized_body
        if agent_input.tag_cover:
            report.recommended_tags = agent_input.tag_cover.recommended_tags
            report.cover_text = agent_input.tag_cover.cover_text
            report.comment_guides = [agent_input.tag_cover.first_comment, agent_input.tag_cover.publish_time_suggestion]
            report.rewritten_versions.tags = report.recommended_tags
            report.rewritten_versions.cover_text = report.cover_text
            report.rewritten_versions.comment_guides = report.comment_guides
        if agent_input.risk_review:
            report.risks = agent_input.risk_review.risks
            report.suggestions = list(dict.fromkeys(report.suggestions + agent_input.risk_review.revision_suggestions))
            report.risk_review = RiskReviewSummary(
                risk_level=agent_input.risk_review.risk_level,
                overall_level=agent_input.risk_review.risk_level,
                risk_items=agent_input.risk_review.risk_items,
                safe_alternatives=agent_input.risk_review.safe_alternatives,
                human_review_required=agent_input.risk_review.human_review_required,
                risks=agent_input.risk_review.risks,
                suggestions=agent_input.risk_review.revision_suggestions,
            )
            if agent_input.risk_review.risk_level == "high":
                report.rewritten_titles = []
                report.optimized_body = "\n".join(agent_input.risk_review.safe_alternatives)
                report.rewritten_versions.titles = []
                report.rewritten_versions.body = report.optimized_body
        if agent_input.similar_cases:
            report.matched_samples = agent_input.similar_cases.matched_samples
            report.case_match_message = agent_input.similar_cases.message
        if agent_input.errors:
            report.problems = report.problems + [f"{error.agent} 执行失败：{error.message}" for error in agent_input.errors]
        report.rewrite_explanations = build_rewrite_explanations(
            agent_input.payload,
            report.rewritten_titles,
            report.optimized_body,
            report.recommended_tags,
            report.cover_text,
            report.comment_guides,
        )
        report.mode = "workflow"
        return FinalReportOutput(report=report)
