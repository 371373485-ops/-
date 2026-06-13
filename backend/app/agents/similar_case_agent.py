import re

from app.models.database import get_connection, init_db
from app.schemas.case import CaseMatchResponse, MatchedSample
from app.schemas.diagnosis import DiagnosisRequest
from app.schemas.workflow import SimilarCaseInput, SimilarCaseOutput
from app.services.sample_service import row_to_sample


TITLE_KEYWORDS = (
    "新手", "避坑", "踩坑", "清单", "教程", "攻略", "真实", "实测",
    "亲测", "普通人", "小白", "收藏", "对比", "方法", "步骤", "别再",
)
CONTENT_KEYWORDS = (
    "第一", "第二", "步骤", "清单", "总结", "真实", "经历", "实测",
    "对比", "适合", "问题", "建议", "评论", "收藏",
)
CAUTION_TEXT = "仅供结构参考，不建议照搬。请结合自己的真实经历、表达习惯和合规边界重新创作。"


class SimilarCaseAgent:
    name = "SimilarCaseAgent"

    def run(self, agent_input: SimilarCaseInput) -> SimilarCaseOutput:
        return SimilarCaseOutput(cases=self.match(agent_input.payload))

    def match(self, payload: DiagnosisRequest, limit: int = 3) -> CaseMatchResponse:
        samples = self._load_samples()
        if not samples:
            return CaseMatchResponse(matched_samples=[], message="样本库为空，暂时无法匹配用户自有或授权样本。")

        scored = []
        for sample in samples:
            score, reasons, learn_points = self._score_sample(payload, sample)
            if score >= 0.22:
                scored.append((score, sample, reasons, learn_points))

        if not scored:
            return CaseMatchResponse(matched_samples=[], message="暂未找到足够相似的样本，请先导入同赛道或相近主题样本。")

        scored.sort(key=lambda item: item[0], reverse=True)
        matched = [
            MatchedSample(
                id=sample.id,
                title=sample.title,
                category=sample.category,
                tags=sample.tags,
                likes=sample.likes,
                collects=sample.collects,
                comments=sample.comments,
                similarity_score=round(score, 4),
                similarity_reason="；".join(reasons),
                what_to_learn=learn_points,
                suggested_adaptation=self._suggest_adaptation(payload, sample),
                caution=CAUTION_TEXT,
            )
            for score, sample, reasons, learn_points in scored[:limit]
        ]
        return CaseMatchResponse(matched_samples=matched)

    def _load_samples(self):
        init_db()
        with get_connection() as connection:
            rows = connection.execute("SELECT * FROM samples ORDER BY id DESC").fetchall()
        return [row_to_sample(row) for row in rows]

    def _score_sample(self, payload: DiagnosisRequest, sample) -> tuple[float, list[str], list[str]]:
        reasons: list[str] = []
        learn_points: list[str] = []
        score = 0.0

        if sample.category == payload.category:
            score += 0.35
            reasons.append("赛道相同")
            learn_points.append("参考同赛道的选题角度和用户痛点表达。")

        title_overlap = self._overlap(self._title_tokens(payload.title), self._title_tokens(sample.title))
        if title_overlap:
            score += min(0.25, title_overlap * 0.08)
            reasons.append(f"标题关键词重合 {title_overlap} 个")
            learn_points.append("借鉴标题中的关键词组合方式，但不要复制原标题。")

        tag_overlap = len(set(payload.tags) & set(sample.tags))
        if tag_overlap:
            score += min(0.18, tag_overlap * 0.06)
            reasons.append(f"标签重合 {tag_overlap} 个")
            learn_points.append("参考标签覆盖赛道、人群和内容形式的方式。")

        content_overlap = self._overlap(self._content_tokens(payload.content), self._content_tokens(sample.content))
        if content_overlap:
            score += min(0.12, content_overlap * 0.03)
            reasons.append(f"正文关键词相近 {content_overlap} 个")
            learn_points.append("参考正文的段落结构、步骤感或经验叙述方式。")

        performance_score = self._performance_score(sample)
        score += performance_score * 0.10
        reasons.append(f"样本表现分 {round(performance_score, 2)}")

        if not learn_points:
            learn_points.append("参考样本的信息组织方式，结合自己的真实内容重新表达。")
        return score, reasons, learn_points

    def _title_tokens(self, text: str) -> set[str]:
        tokens = {keyword for keyword in TITLE_KEYWORDS if keyword in text}
        tokens.update(token.lower() for token in re.findall(r"[A-Za-z0-9]+", text) if len(token) >= 2)
        return tokens

    def _content_tokens(self, text: str) -> set[str]:
        return {keyword for keyword in CONTENT_KEYWORDS if keyword in text}

    def _overlap(self, left: set[str], right: set[str]) -> int:
        return len(left & right)

    def _performance_score(self, sample) -> float:
        raw = sample.likes + sample.collects * 1.5 + sample.comments * 2
        return min(1.0, raw / 1000)

    def _suggest_adaptation(self, payload: DiagnosisRequest, sample) -> str:
        if sample.category == payload.category:
            return "可以借鉴该样本的标题结构、标签组合和正文层次，再替换为你自己的真实经历与具体细节。"
        return "该样本只适合参考表达结构，请优先保留你的赛道、人群和真实经验，不要跨赛道照搬。"
