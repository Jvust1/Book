"""Local-only FastAPI adapter over the Book App runtime service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.study import (
    StudyRecord,
    StudyRecordRepository,
    StudyRecordRepositoryError,
    StudyRecordService,
    resolve_study_db_path,
)
from runtime import QAHistoryMessage

from .errors import (
    AppNotFoundError,
    AppUnavailableError,
    BookAppError,
    InvalidModeError,
    InvalidQAQuestionError,
    InvalidSearchQueryError,
    QAProviderInvalidResponseError,
    QAProviderUnconfiguredError,
)
from .models import (
    ChapterResponse,
    CourseResponse,
    LibraryResponse,
    ModeResponse,
    QARequest,
    QAResponse,
    SearchResponse,
    SectionResponse,
    SourceResponse,
    StudyRecordListResponse,
    StudyRecordResponse,
)
from .qa_provider_factory import QAProviderConfigurationError, provider_from_environment
from .service import BookAppService


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOCAL_WEB_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app = FastAPI(title="Book App API", version="1f-v2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_WEB_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _validate_model(model_type: type[QARequest], payload: object) -> QARequest:
    """Validate request DTOs across Pydantic v1 and v2 runtimes.

    The Android build uses Pydantic v1 because Chaquopy does not provide the
    native ``pydantic-core`` wheel required by Pydantic v2. Desktop installs
    continue to use the v2 API when available.
    """

    if not isinstance(payload, dict):
        raise ValueError("QA request must be a JSON object")
    history = payload.get("history", [])
    if not isinstance(history, list) or any(not isinstance(row, dict) for row in history):
        raise ValueError("QA history must be a list of JSON objects")

    validator = getattr(model_type, "model_validate", None)
    if validator is not None:
        return validator(payload)
    return model_type.parse_obj(payload)


@lru_cache(maxsize=1)
def default_service() -> BookAppService:
    """Open the repository runtime lazily so module import cannot fail closed."""

    try:
        provider = provider_from_environment()
    except QAProviderConfigurationError as exc:
        raise QAProviderUnconfiguredError(
            code="qa_provider_unconfigured",
            user_message="教材问答模型未配置",
            detail=str(exc),
        ) from exc
    return BookAppService(REPOSITORY_ROOT, qa_provider=provider)


def get_service() -> BookAppService:
    return default_service()


@lru_cache(maxsize=1)
def default_study_repository() -> StudyRecordRepository:
    return StudyRecordRepository(resolve_study_db_path())


def get_study_repository() -> StudyRecordRepository:
    return default_study_repository()


def get_study_service(
    book_service: BookAppService = Depends(get_service),
    repository: StudyRecordRepository = Depends(get_study_repository),
) -> StudyRecordService:
    return StudyRecordService(book_service, repository)


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


@app.exception_handler(InvalidSearchQueryError)
async def handle_invalid_search_query(
    _request: Request, error: InvalidSearchQueryError
) -> JSONResponse:
    return _error_response(error, 400)


@app.exception_handler(InvalidQAQuestionError)
async def handle_invalid_qa_question(
    _request: Request, error: InvalidQAQuestionError
) -> JSONResponse:
    return _error_response(error, 400)


@app.exception_handler(QAProviderInvalidResponseError)
async def handle_invalid_qa_provider_response(
    _request: Request, error: QAProviderInvalidResponseError
) -> JSONResponse:
    return _error_response(error, 502)


@app.exception_handler(AppUnavailableError)
async def handle_unavailable(_request: Request, error: AppUnavailableError) -> JSONResponse:
    return _error_response(error, 503)


@app.exception_handler(StudyRecordRepositoryError)
async def handle_study_repository_error(
    _request: Request, error: StudyRecordRepositoryError
) -> JSONResponse:
    return _error_response(
        AppUnavailableError(
            code="study_store_unavailable",
            user_message="学习进度暂无法保存",
            detail=str(error),
        ),
        503,
    )


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


@app.get(
    "/api/courses/{course_id}/search",
    response_model=SearchResponse,
)
def search(
    course_id: str,
    q: str = "",
    limit: int = 30,
    service: BookAppService = Depends(get_service),
) -> SearchResponse:
    return service.search(course_id, q, limit=limit)


@app.post(
    "/api/courses/{course_id}/qa",
    response_model=QAResponse,
)
async def qa(
    course_id: str,
    request: Request,
    service: BookAppService = Depends(get_service),
) -> QAResponse:
    try:
        payload = _validate_model(QARequest, await request.json())
    except (ValueError, TypeError, ValidationError) as exc:
        raise InvalidQAQuestionError(
            code="invalid_qa_question",
            user_message="提问内容无效",
            detail="Invalid QA request body",
        ) from exc

    history = tuple(
        QAHistoryMessage(role=row.role, content=row.content)
        for row in payload.history
    )
    return service.ask(
        course_id,
        payload.question,
        section_id=payload.section_id,
        history=history,
    )


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


def _study_record_response(record: StudyRecord) -> StudyRecordResponse:
    return StudyRecordResponse(
        course_id=record.course_id,
        book_id=record.book_id,
        section_id=record.section_id,
        mode=record.mode,
        status=record.status,
        progress=record.progress,
        started_at=record.started_at,
        last_studied_at=record.last_studied_at,
        completed_at=record.completed_at,
        updated_at=record.updated_at,
    )


@app.post(
    "/api/courses/{course_id}/sections/{section_id}/study/{mode}/touch",
    response_model=StudyRecordResponse,
)
def touch_study(
    course_id: str,
    section_id: str,
    mode: str,
    service: StudyRecordService = Depends(get_study_service),
) -> StudyRecordResponse:
    return _study_record_response(service.touch(course_id, section_id, mode))


@app.post(
    "/api/courses/{course_id}/sections/{section_id}/study/{mode}/complete",
    response_model=StudyRecordResponse,
)
def complete_study(
    course_id: str,
    section_id: str,
    mode: str,
    service: StudyRecordService = Depends(get_study_service),
) -> StudyRecordResponse:
    return _study_record_response(service.complete(course_id, section_id, mode))


@app.get(
    "/api/courses/{course_id}/study-records",
    response_model=StudyRecordListResponse,
)
def course_study_records(
    course_id: str,
    service: StudyRecordService = Depends(get_study_service),
) -> StudyRecordListResponse:
    records = service.list_course(course_id)
    return StudyRecordListResponse(
        course_id=course_id,
        records=[_study_record_response(record) for record in records],
    )


@app.get(
    "/api/study/recent",
    response_model=StudyRecordResponse | None,
)
def recent_study(
    service: StudyRecordService = Depends(get_study_service),
) -> StudyRecordResponse | None:
    record = service.recent()
    return None if record is None else _study_record_response(record)


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
