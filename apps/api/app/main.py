import os
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import subjects, chapters, questions, upload, reviews, auth, files

Path(settings.storage_local_path).mkdir(parents=True, exist_ok=True)
for sub in ("avatars", "questions", "pdfs"):
    (Path(settings.storage_local_path) / sub).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="错题本 API", version="0.1.0")


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """生产环境：反向代理若仍为 http 则重定向到 https。"""
    async def dispatch(self, request: Request, call_next):
        if not settings.force_https:
            return await call_next(request)
        proto = request.headers.get("x-forwarded-proto", "").strip().lower()
        if proto == "http":
            url = str(request.url.replace(scheme="https"))
            return RedirectResponse(url, status_code=301)
        return await call_next(request)


app.add_middleware(HTTPSRedirectMiddleware)
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
app.include_router(files.router, prefix="/files", tags=["files"])


@app.get("/health")
async def health():
    return {"status": "ok"}
