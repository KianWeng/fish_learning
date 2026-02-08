from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    sort: int = 0
    cover_url: str | None = None


class SubjectUpdate(BaseModel):
    name: str | None = None
    sort: int | None = None
    cover_url: str | None = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    sort: int
    cover_url: str | None = None

    class Config:
        from_attributes = True
