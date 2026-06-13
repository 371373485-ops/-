from pydantic import BaseModel


class MatchedSample(BaseModel):
    id: int
    title: str
    category: str
    tags: list[str]
    likes: int
    collects: int
    comments: int
    similarity_score: float
    similarity_reason: str
    what_to_learn: list[str]
    suggested_adaptation: str
    caution: str


class CaseMatchResponse(BaseModel):
    matched_samples: list[MatchedSample]
    message: str | None = None
