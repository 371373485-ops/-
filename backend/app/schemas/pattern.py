from app.schemas.sample import SampleItem
from pydantic import BaseModel


class FrequencyItem(BaseModel):
    value: str
    count: int


class TitleLengthBucket(BaseModel):
    bucket: str
    count: int


class StructureCount(BaseModel):
    name: str
    count: int
    ratio: float


class OpeningStructureCount(BaseModel):
    name: str
    count: int
    ratio: float


class CategoryPatternSummary(BaseModel):
    category: str
    sample_count: int
    average_likes: float
    average_collects: float
    average_comments: float
    collect_rate: float
    comment_rate: float
    style_summary: str


class PatternAnalysisResponse(BaseModel):
    category: str | None
    sample_count: int
    insufficient_sample_warning: str | None
    frequent_title_keywords: list[FrequencyItem]
    frequent_tags: list[FrequencyItem]
    title_length_distribution: list[TitleLengthBucket]
    average_likes: float
    average_collects: float
    average_comments: float
    collect_rate: float
    comment_rate: float
    top_samples: list[SampleItem]
    title_structures: list[StructureCount]
    opening_structures: list[OpeningStructureCount]
    category_summaries: list[CategoryPatternSummary]
