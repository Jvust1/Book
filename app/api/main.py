"""Local-only FastAPI adapter over the Book App runtime service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .errors import AppNotFoundError, AppUnavailableError, BookAppError, InvalidModeError
from .models import (
    ChapterResponse,
    CourseResponse,
    LibraryResponse,
    ModeResponse,
    SectionResponse,
    SourceResponse,
)
from .service import BookAppService


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOCAL_WEB_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app = FastAPI(title="Book App API", version="1d")
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_WEB_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def default_service() -> BookAppService:
    """Open the repository runtime lazily so module import cannot fail closed."""

    return BookAppService(REPOSITORY_ROOT)


def get_service() -> BookAppService:
    return default_service()


def _error_response(error: BookAppError, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error.code, "message": error.user_message}},
    )


@app.exception_handler(AppNotFoundError)
async def handle_not_found(_request: Request, error: AppNotFoundError) -> JSONResponse:
    return _error_response(error, 404)


@app.exception_handler(InvalidModeError)
async def handle_invalid_mode(_request: Request, error: InvalidModeError) -> JSONResponse:
    return _error_response(error, 400)


@app.exception_handler(AppUnavailableError)
async def handle_unavailable(_request: Request, error: AppUnavailableError) -> JSONResponse:
    return _error_response(error, 503)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/library", response_model=LibraryResponse)
def library(service: BookAppService = Depends(get_service)) -> LibraryResponse:
    return service.library()


@app.get("/api/courses/{course_id}", response_model=CourseResponse)
def course(course_id: str, service: BookAppService = Depends(get_service)) -> CourseResponse:
    return service.course(course_id)


@app.get(
    "/api/courses/{course_id}/chapters/{chapter_id}",
    response_model=ChapterResponse,
)
def chapter(
    course_id: str,
    chapter_id: str,
    service: BookAppService = Depends(get_service),
) -> ChapterResponse:
    return service.chapter(course_id, chapter_id)


@app.get(
    "/api/courses/{course_id}/sections/{section_id}",
    response_model=SectionResponse,
)
def section(
    course_id: str,
    section_id: str,
    service: BookAppService = Depends(get_service),
) -> SectionResponse:
    return service.section(course_id, section_id)


def _mode_response(
    course_id: str,
    section_id: str,
    mode: str,
    service: BookAppService,
) -> ModeResponse:
    return service.mode(course_id, section_id, mode)


@app.get(
    "/api/courses/{course_id}/sections/{section_id}/preview",
    response_model=ModeResponse,
)
def preview(
    course_id: str,
    section_id: str,
    service: BookAppService = Depends(get_service),
) -> ModeResponse:
    return _mode_response(course_id, section_id, "preview", service)


@app.get(
    "/api/courses/{course_id}/sections/{section_id}/learn",
    response_model=ModeResponse,
)
def learn(
    course_id: str,
    section_id: str,
    service: BookAppService = Depends(get_service),
) -> ModeResponse:
    return _mode_response(course_id, section_id, "learn", service)


@app.get(
    "/api/courses/{course_id}/sections/{section_id}/review",
    response_model=ModeResponse,
)
def review(
    course_id: str,
    section_id: str,
    service: BookAppService = Depends(get_service),
) -> ModeResponse:
    return _mode_response(course_id, section_id, "review", service)


@app.get(
    "/api/courses/{course_id}/sections/{section_id}/practice",
    response_model=ModeResponse,
)
def practice(
    course_id: str,
    section_id: str,
    service: BookAppService = Depends(get_service),
) -> ModeResponse:
    return _mode_response(course_id, section_id, "practice", service)


@app.get(
    "/api/courses/{course_id}/sources/{kind}/{source_id}",
    response_model=SourceResponse,
)
def source(
    course_id: str,
    kind: str,
    source_id: str,
    service: BookAppService = Depends(get_service),
) -> SourceResponse:
    return service.source(course_id, kind, source_id)
