from pydantic import BaseModel


class ChapterCreate(BaseModel):
    subject_id: int
    name: str
    sort: int = 0
    parent_id: int | None = None


class ChapterUpdate(BaseModel):
    name: str | None = None
    sort: int | None = None
    parent_id: int | None = None


class ChapterResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    sort: int
    parent_id: int | None = None

    class Config:
        from_attributes = True
