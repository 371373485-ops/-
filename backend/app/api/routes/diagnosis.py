from fastapi import APIRouter, HTTPException

from app.schemas.diagnosis import DiagnosisRefineRequest, DiagnosisRequest, DiagnosisResponse
from app.services.ai_client import AIClientError, OpenAIClient, should_use_mock_ai
from app.services.ai_diagnosis_service import build_ai_diagnosis
from app.services.mock_diagnosis_service import build_mock_diagnosis
from app.services.scoring_service import build_rule_diagnosis
from app.services.history_service import save_diagnosis_history
from app.services.workflow import DiagnosisWorkflow


router = APIRouter()


@router.post("/mock", response_model=DiagnosisResponse)
def diagnose_mock(payload: DiagnosisRequest) -> DiagnosisResponse:
    return build_mock_diagnosis(payload)


@router.post("/rule", response_model=DiagnosisResponse)
def diagnose_rule(payload: DiagnosisRequest) -> DiagnosisResponse:
    return build_rule_diagnosis(payload)


def _payload_with_missing_answers(payload: DiagnosisRequest, refine_request: DiagnosisRefineRequest) -> DiagnosisRequest:
    answers = [
        answer
        for answer in refine_request.missing_answers
        if answer.field.strip() and answer.answer.strip()
    ]
    if not answers:
        return payload

    supplement_lines = ["", "", "用户补充信息："]
    supplement_lines.extend(f"- {answer.field.strip()}：{answer.answer.strip()}" for answer in answers)
    return payload.model_copy(update={"content": f"{payload.content.rstrip()}{chr(10).join(supplement_lines)}"})


@router.post("/refine", response_model=DiagnosisResponse)
def refine_diagnosis(payload: DiagnosisRefineRequest) -> DiagnosisResponse:
    refined_payload = _payload_with_missing_answers(payload.original_payload, payload)
    return build_rule_diagnosis(refined_payload)


@router.post("/ai", response_model=DiagnosisResponse)
def diagnose_ai(payload: DiagnosisRequest) -> DiagnosisResponse:
    try:
        return build_ai_diagnosis(payload)
    except AIClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/ai/status")
def ai_status() -> dict[str, object]:
    client = OpenAIClient()
    use_mock = should_use_mock_ai()
    real_ai_ready = (not use_mock) and client.is_configured
    return {
        "use_mock_ai": use_mock,
        "provider": client.provider,
        "openai_configured": client.is_configured,
        "provider_configured": client.is_configured,
        "real_ai_ready": real_ai_ready,
        "mode": "real_ai" if real_ai_ready else "mock_or_rule",
        "model": client.model,
        "base_url_configured": bool(client.base_url),
        "fallback": "未启用真实 AI 或未配置 OPENAI_API_KEY 时，系统会使用 mock/规则逻辑保持可演示。",
    }


@router.post("/workflow", response_model=DiagnosisResponse)
def diagnose_workflow(payload: DiagnosisRequest) -> DiagnosisResponse:
    result = DiagnosisWorkflow().run(payload, use_ai=True)
    save_diagnosis_history(payload, result)
    return result
