from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    course: str | None = None  # 科目：常见科目名或自定义字符串
    sort: int = 0
    cover_url: str | None = None


class SubjectUpdate(BaseModel):
    name: str | None = None
    course: str | None = None
    sort: int | None = None
    cover_url: str | None = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    course: str | None = None
    sort: int
    cover_url: str | None = None

    class Config:
        from_attributes = True
