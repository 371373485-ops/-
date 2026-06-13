from pydantic import BaseModel, Field


SOURCE_TYPES = (
    "demo_generated",
    "own_account_manual",
    "authorized_manual",
    "third_party_export",
    "public_dataset",
    "structure_observation",
)


class SampleBase(BaseModel):
    title: str
    content: str
    tags: list[str]
    category: str
    likes: int = Field(..., ge=0)
    collects: int = Field(..., ge=0)
    comments: int = Field(..., ge=0)
    cover_text: str
    publish_time: str | None = None
    source_note: str
    source_type: str


class SampleItem(SampleBase):
    id: int
    created_at: str


class SampleImportResponse(BaseModel):
    imported_count: int
    samples: list[SampleItem]


class SampleListResponse(BaseModel):
    items: list[SampleItem]
    total: int
