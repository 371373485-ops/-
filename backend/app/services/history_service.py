import json
import sqlite3
from typing import Any

from fastapi import HTTPException

from app.models.database import get_connection, init_db
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.schemas.history import HistoryDetail, HistoryListItem, HistoryListResponse, MarkdownExportResponse


def save_diagnosis_history(payload: DiagnosisRequest, output: DiagnosisResponse) -> int:
    init_db()
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO diagnosis_history (input_json, output_json, title, category, overall_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    payload.model_dump_json(),
                    output.model_dump_json(),
                    payload.title,
                    payload.category,
                    output.overall_score,
                ),
            )
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="保存诊断历史失败，请检查本地数据库文件权限或稍后重试。") from exc
    return int(cursor.lastrowid)


def list_history() -> HistoryListResponse:
    init_db()
    try:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, title, category, overall_score, created_at FROM diagnosis_history ORDER BY id DESC"
            ).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="读取历史列表失败，请检查数据库状态。") from exc
    items = [
        HistoryListItem(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            overall_score=row["overall_score"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return HistoryListResponse(items=items, total=len(items))


def get_history(history_id: int) -> HistoryDetail:
    init_db()
    try:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM diagnosis_history WHERE id = ?", (history_id,)).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="读取历史详情失败，请检查数据库状态。") from exc
    if not row:
        raise HTTPException(status_code=404, detail="历史记录不存在。")
    return _row_to_detail(row)


def delete_history(history_id: int) -> dict[str, bool]:
    init_db()
    try:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM diagnosis_history WHERE id = ?", (history_id,))
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="删除历史记录失败，请检查数据库状态。") from exc
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="历史记录不存在。")
    return {"deleted": True}


def export_history_markdown(history_id: int) -> MarkdownExportResponse:
    detail = get_history(history_id)
    markdown = _build_markdown(detail)
    return MarkdownExportResponse(filename=f"diagnosis-report-{history_id}.md", markdown=markdown)


def _row_to_detail(row: Any) -> HistoryDetail:
    payload = DiagnosisRequest.model_validate(json.loads(row["input_json"]))
    output = DiagnosisResponse.model_validate(json.loads(row["output_json"]))
    return HistoryDetail(
        id=row["id"],
        input=payload,
        output=output,
        title=row["title"],
        category=row["category"],
        overall_score=row["overall_score"],
        created_at=row["created_at"],
    )


def _build_markdown(detail: HistoryDetail) -> str:
    payload = detail.input
    output = detail.output
    content_summary = payload.content[:180] + ("..." if len(payload.content) > 180 else "")

    lines = [
        "# 小红书爆款内容诊断报告",
        "",
        f"- 生成时间：{detail.created_at}",
        f"- 原始标题：{payload.title}",
        f"- 内容赛道：{payload.category}",
        f"- 目标人群：{payload.target_audience}",
        f"- 发布目标：{payload.goal}",
        "",
        "## 原始正文摘要",
        "",
        content_summary,
        "",
        "## 爆款潜力总分",
        "",
        str(output.overall_score),
        "",
        "## 各维度评分",
        "",
    ]
    for item in output.scores:
        lines.extend([f"- {item.name}：{item.score}/100", f"  - 理由：{item.reason}"])

    lines.extend(["", "## 证据型诊断", ""])
    if output.evidence_findings:
        for item in output.evidence_findings:
            lines.extend(
                [
                    f"### {item.priority}｜{item.dimension}｜{item.source}",
                    f"- 原文证据：{item.evidence}",
                    f"- 问题：{item.issue}",
                    f"- 影响：{item.impact}",
                    f"- 改法：{item.action}",
                    "",
                ]
            )
    else:
        lines.append("暂无证据型诊断。")

    lines.extend(["", "## 优先改法", ""])
    if output.priority_actions:
        lines.extend([f"{item.priority}. {item.action}（{item.reason}；{item.expected_effect}）" for item in output.priority_actions])
    else:
        lines.append("暂无优先改法。")

    lines.extend(["", "## 问题诊断", ""])
    lines.extend([f"- {item}" for item in output.problems])
    lines.extend(["", "## 修改建议", ""])
    lines.extend([f"- {item}" for item in output.suggestions])
    lines.extend(["", "## 优化标题", ""])
    lines.extend([f"- {item}" for item in output.rewritten_titles])
    lines.extend(["", "## 优化正文", "", output.optimized_body])
    lines.extend(["", "## 推荐标签", "", " ".join(f"#{tag}" for tag in output.recommended_tags)])
    lines.extend(["", "## 封面文案", ""])
    lines.extend([f"- {item}" for item in output.cover_text])
    lines.extend(["", "## 评论区引导", ""])
    lines.extend([f"- {item}" for item in output.comment_guides])
    lines.extend(["", "## 风险审查", ""])
    lines.extend([f"- {risk.level}：{risk.message}" for risk in output.risks])
    lines.extend(["", "## 相似案例", ""])
    if output.matched_samples:
        for sample in output.matched_samples:
            lines.extend(
                [
                    f"### {sample.title}",
                    f"- 赛道：{sample.category}",
                    f"- 数据：点赞 {sample.likes} / 收藏 {sample.collects} / 评论 {sample.comments}",
                    f"- 匹配原因：{sample.similarity_reason}",
                    f"- 可借鉴点：{'；'.join(sample.what_to_learn)}",
                    f"- 建议适配：{sample.suggested_adaptation}",
                    f"- 注意：{sample.caution}",
                    "",
                ]
            )
    else:
        lines.append(output.case_match_message or "暂无相似案例。")

    return "\n".join(lines).strip() + "\n"
