"""Explicit test-only server factory; production app imports never enable this fixture.

Run: python -m uvicorn app_tests.synthetic_pilot_server:create_app --factory --host 127.0.0.1 --port 8000
All course inputs and SQLite state live in a temporary directory; QA is deterministic.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from app.api.main import app, get_service, get_study_repository
from app.api.service import BookAppService
from app.study import StudyRecordRepository
from app_tests.synthetic_chapter import write_synthetic_chapter
from runtime import DeterministicFakeModelProvider


def create_app():
    temporary = TemporaryDirectory(prefix="book-original-pilot-")
    root = Path(temporary.name)
    try:
        service = BookAppService(write_synthetic_chapter(root / "repository"),
                                 qa_provider=DeterministicFakeModelProvider())
        repository = StudyRecordRepository(root / "study.sqlite3")
    except Exception:
        temporary.cleanup()
        raise
    prior_overrides = app.dependency_overrides.copy()
    prior_lifespan = app.router.lifespan_context
    app.dependency_overrides[get_service] = lambda: service
    app.dependency_overrides[get_study_repository] = lambda: repository

    @asynccontextmanager
    async def lifespan(application):
        try:
            async with prior_lifespan(application):
                yield
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(prior_overrides)
            app.router.lifespan_context = prior_lifespan
            temporary.cleanup()

    app.router.lifespan_context = lifespan
    return app
