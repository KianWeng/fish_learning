from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    sort: int = 0


class SubjectUpdate(BaseModel):
    name: str | None = None
    sort: int | None = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    sort: int

    class Config:
        from_attributes = True
