from collections.abc import Sequence

from app.schemas.diagnosis import DiagnosisRequest, EvidenceDiagnosisItem, RewriteExplanation, RevisionTask


DETAIL_REQUIREMENTS = (
    ("真实场景", ("场景", "上班", "通勤", "早上", "晚上", "出门", "会议", "学习")),
    ("真实使用周期", ("用了", "使用", "观察", "天", "周", "月", "小时", "连续")),
    ("观察到的变化", ("记录", "变化", "之前", "后来", "前后", "发现", "对比")),
    ("不适用情况", ("失败", "不适合", "踩坑", "无效", "没用", "限制", "前提", "谨慎", "因人而异")),
    ("适用人群", ("适合", "不适合", "人群", "新手", "上班族", "学生", "宝妈")),
    ("不可公开信息边界", ("不能公开", "不方便公开", "隐私", "脱敏", "客户数据", "账号", "姓名", "手机号")),
)


PLACEHOLDER_BY_FIELD = {
    "真实场景": "【请补充真实场景】",
    "真实使用周期": "【请补充真实使用周期】",
    "观察到的变化": "【请补充观察到的变化】",
    "不适用情况": "【请补充不适用情况】",
    "适用人群": "【请补充适合/不适合人群】",
    "不可公开信息边界": "【请标注不能公开的信息】",
}


def missing_detail_placeholders(payload: DiagnosisRequest) -> list[str]:
    text = f"{payload.title}\n{payload.content}\n{payload.cover_text or ''}\n{payload.comment_guide or ''}"
    missing = []
    for field, keywords in DETAIL_REQUIREMENTS:
        if not any(keyword in text for keyword in keywords):
            missing.append(PLACEHOLDER_BY_FIELD[field])
    return missing


def append_missing_detail_placeholders(text: str, payload: DiagnosisRequest) -> str:
    placeholders = missing_detail_placeholders(payload)
    if not placeholders:
        return text
    return f"{text}\n\n需要用户补充的真实细节：\n" + "\n".join(f"- {item}" for item in placeholders)


def build_rewrite_explanations(
    payload: DiagnosisRequest,
    rewritten_titles: list[str],
    optimized_body: str,
    recommended_tags: list[str],
    cover_text: list[str],
    comment_guides: list[str],
    evidence_diagnosis: Sequence[EvidenceDiagnosisItem] | None = None,
    revision_tasks: Sequence[RevisionTask] | None = None,
) -> list[RewriteExplanation]:
    explanations: list[RewriteExplanation] = []
    placeholders = missing_detail_placeholders(payload)
    placeholder_note = f" 原文缺少必要真实细节，改写只能使用占位提示：{'、'.join(placeholders)}。" if placeholders else ""
    title_link = _find_linked_issue(evidence_diagnosis, revision_tasks, ("click",))
    body_link = _find_linked_issue(evidence_diagnosis, revision_tasks, ("trust", "completion"))
    tag_link = _find_linked_issue(evidence_diagnosis, revision_tasks, ("interaction",))

    for index, title in enumerate(rewritten_titles, start=1):
        explanations.append(
            RewriteExplanation(
                target=f"标题{index}",
                original_excerpt=payload.title,
                rewritten_excerpt=title,
                reason=(
                    "围绕目标人群、内容赛道和发布前检查场景重写，让读者更快判断是否与自己有关。"
                    "未新增用户没有提供的经历、数据或效果承诺。"
                    f"{placeholder_note}"
                ),
                expected_effect="click" if index <= 3 else "trust",
                **title_link,
            )
        )

    if optimized_body:
        explanations.append(
            RewriteExplanation(
                target="正文",
                original_excerpt=_snippet(payload.content),
                rewritten_excerpt=_snippet(optimized_body, 160),
                reason=(
                    "前置信息：把目标人群、主题和结论放到开头；"
                    "删除或弱化：弱化绝对承诺、泛泛推荐和无证据判断；"
                    "可信信号提示：提示补充真实使用周期、适用人群、真实对比体验和限制条件；"
                    "改善目标：提升完读和信任，并降低夸大宣传或合规风险。"
                    f"{placeholder_note}"
                ),
                expected_effect="completion",
                **body_link,
            )
        )

    if recommended_tags:
        explanations.append(
            RewriteExplanation(
                target="标签",
                original_excerpt="、".join(payload.tags) if payload.tags else "未提供标签",
                rewritten_excerpt="、".join(recommended_tags),
                reason="补齐赛道、人群、目标和内容形式标签，帮助读者识别内容边界。",
                expected_effect="interaction",
                **tag_link,
            )
        )

    for index, item in enumerate(cover_text, start=1):
        explanations.append(
            RewriteExplanation(
                target=f"封面文案{index}",
                original_excerpt=payload.cover_text or "未提供封面文案",
                rewritten_excerpt=item,
                reason="封面只承接一个最强判断点，减少点击前的信息犹豫。",
                expected_effect="click",
                **title_link,
            )
        )

    for index, item in enumerate(comment_guides, start=1):
        explanations.append(
            RewriteExplanation(
                target=f"评论引导{index}",
                original_excerpt=payload.comment_guide or "未提供评论引导",
                rewritten_excerpt=item,
                reason="评论引导改为站内开放问题，鼓励用户补充真实情况，避免站外引流或诱导式互动。",
                expected_effect="interaction",
                **tag_link,
            )
        )

    return explanations


def _find_linked_issue(
    evidence_diagnosis: Sequence[EvidenceDiagnosisItem] | None,
    revision_tasks: Sequence[RevisionTask] | None,
    impact_areas: tuple[str, ...],
) -> dict[str, str | int | None]:
    issues = list(evidence_diagnosis or [])
    linked_issue = next((item for item in issues if item.impact_area in impact_areas), None)
    if linked_issue is None:
        return {}

    linked_rank = _find_revision_task_rank(linked_issue, revision_tasks)
    return {
        "source_issue_field": linked_issue.field,
        "source_evidence": linked_issue.evidence,
        "linked_revision_task_rank": linked_rank,
    }


def _find_revision_task_rank(issue: EvidenceDiagnosisItem, revision_tasks: Sequence[RevisionTask] | None) -> int | None:
    for task in revision_tasks or []:
        if task.target_field == issue.field:
            return task.rank
        if task.evidence and task.evidence == issue.evidence:
            return task.rank
    return None


def _snippet(text: str, limit: int = 90) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact or "未提供"
    return compact[: limit - 3].rstrip() + "..."
