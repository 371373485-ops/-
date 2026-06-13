from app.schemas.workflow import ContentDiagnosisInput, ContentDiagnosisOutput
from app.services.ai_client import OpenAIClient, should_use_mock_ai
from app.services.ai_diagnosis_service import build_ai_diagnosis
from app.services.scoring_service import build_rule_diagnosis


class ContentDiagnosisAgent:
    name = "ContentDiagnosisAgent"

    def run(self, agent_input: ContentDiagnosisInput) -> ContentDiagnosisOutput:
        use_real_ai = agent_input.use_ai and not should_use_mock_ai() and OpenAIClient().is_configured
        diagnosis = build_ai_diagnosis(agent_input.payload) if use_real_ai else build_rule_diagnosis(agent_input.payload)
        if not use_real_ai and agent_input.use_ai:
            diagnosis.mode = "workflow_mock"
        else:
            diagnosis.mode = "workflow_ai" if use_real_ai else "workflow_rule"
        return ContentDiagnosisOutput(diagnosis=diagnosis)
