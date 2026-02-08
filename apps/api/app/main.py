import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import subjects, chapters, questions, upload, reviews, auth

Path(settings.storage_local_path).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="错题本 API", version="0.1.0")
app.mount("/uploads", StaticFiles(directory=settings.storage_local_path), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
app.include_router(chapters.router, prefix="/chapters", tags=["chapters"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"status": "ok"}
