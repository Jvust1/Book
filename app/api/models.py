"""Stable JSON DTOs between Python runtime and Book App clients."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


LearningMode = Literal["preview", "learn", "review", "practice"]
AnswerStyle = Literal["brief", "explain", "compare", "proof"]
QAScopeRequested = Literal["book", "section_then_book"]
QAScopeUsed = Literal["section", "book"]


class CourseCard(BaseModel):
    course_id: str
    name_zh: str
    name_en: str | None
    authors: list[str]
    book_id: str
    chapter_count: int
    section_count: int
    runtime_status: str


class LibraryResponse(BaseModel):
    library_id: str
    name: str
    courses: list[CourseCard]


class SectionCard(BaseModel):
    section_id: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    printed_page_start: int | str | None
    printed_page_end: int | str | None
    pdf_page_start: int | None
    pdf_page_end: int | None


class ChapterCard(BaseModel):
    chapter_id: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    section_count: int


class CourseResponse(BaseModel):
    course: CourseCard
    chapters: list[ChapterCard]
    section_count: int


class ChapterResponse(BaseModel):
    course_id: str
    book_id: str
    chapter: ChapterCard
    sections: list[SectionCard]


class SectionResponse(BaseModel):
    course_id: str
    book_id: str
    chapter_id: str | None
    section: SectionCard
    object_count: int
    figure_count: int
    translation_available: bool


class ModeItem(BaseModel):
    kind: str
    source_id: str
    object_type: str | None
    type_zh: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    printed_page: int | str | None
    pdf_page: int | None
    content_zh: str | None
    translation_available: bool


class SourceRef(BaseModel):
    kind: str
    source_id: str


class LearningSliceDerivedPrompt(BaseModel):
    text: str
    derivation: Literal["deterministic_template"]
    source_ref: SourceRef


class LearningSliceObjectCount(BaseModel):
    object_type: str
    count: int


class LearningSliceOverview(BaseModel):
    object_count: int
    figure_count: int
    translation_available: bool


class LearningSlicePrerequisites(BaseModel):
    status: Literal["unavailable"]
    items: list[SourceRef]


class LearningSlicePreset(BaseModel):
    id: Literal["one_minute", "five_minute", "full"]
    label: str
    source_refs: list[SourceRef]


class LearningSlicePracticeFilter(BaseModel):
    id: Literal["all", "exercise", "problem"]
    label: str


class LearningSlicePracticeItem(BaseModel):
    source_ref: SourceRef
    solution_status: Literal["unavailable"]


class LearningSliceGroup(BaseModel):
    id: Literal[
        "definitions",
        "theorem_family",
        "formulas",
        "examples",
        "other_objects",
        "figures",
        "translations",
    ]
    label: str
    source_refs: list[SourceRef]


class LearningSliceExtensionStatus(BaseModel):
    status: Literal["unavailable"]


class LearningSliceExtensions(BaseModel):
    supplementary: LearningSliceExtensionStatus
    lecture: LearningSliceExtensionStatus


class PreviewLearningSlicePresentation(BaseModel):
    schema_version: Literal["learning_slice_v1"]
    mode: Literal["preview"]
    overview: LearningSliceOverview
    object_counts: list[LearningSliceObjectCount]
    objectives: list[LearningSliceDerivedPrompt]
    prerequisites: LearningSlicePrerequisites
    core_definitions: list[SourceRef]
    core_formulas: list[SourceRef]
    key_figures: list[SourceRef]
    quick_checks: list[LearningSliceDerivedPrompt]


class ReviewLearningSlicePresentation(BaseModel):
    schema_version: Literal["learning_slice_v1"]
    mode: Literal["review"]
    presets: list[LearningSlicePreset]
    prompts: list[LearningSliceDerivedPrompt]


class PracticeLearningSlicePresentation(BaseModel):
    schema_version: Literal["learning_slice_v1"]
    mode: Literal["practice"]
    filters: list[LearningSlicePracticeFilter]
    items: list[LearningSlicePracticeItem]


class LearnLearningSlicePresentation(BaseModel):
    schema_version: Literal["learning_slice_v1"]
    mode: Literal["learn"]
    groups: list[LearningSliceGroup]
    extensions: LearningSliceExtensions


LearningSlicePresentation = Annotated[
    PreviewLearningSlicePresentation
    | ReviewLearningSlicePresentation
    | PracticeLearningSlicePresentation
    | LearnLearningSlicePresentation,
    Field(discriminator="mode"),
]


class ModeResponse(BaseModel):
    mode: LearningMode
    course_id: str
    book_id: str
    chapter_id: str | None
    section_id: str
    source_status: str
    items: list[ModeItem]
    source_refs: list[SourceRef]
    presentation: LearningSlicePresentation


class SourceContextItem(BaseModel):
    kind: str
    source_id: str
    type: str | None
    number: str | None
    title_zh: str | None


class SourceResponse(BaseModel):
    course_id: str
    book_id: str
    section_id: str | None
    kind: str
    source_id: str
    type: str | None
    type_zh: str
    number: str | None
    title_zh: str | None
    title_en: str | None
    content_zh: str | None
    formula: str | None
    printed_page: int | str | None
    pdf_page: int | None
    source_anchor: str | None
    source_batch: str | None
    translation_available: bool
    context_before: list[SourceContextItem]
    context_after: list[SourceContextItem]


class SearchResultItem(BaseModel):
    rank: int
    score: int
    source_kind: str
    source_id: str
    object_type: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    formula: str | None
    pdf_page: int | None
    printed_page: int | str | None
    source_anchor: str | None
    snippet: str | None


class SearchResponse(BaseModel):
    course_id: str
    book_id: str
    query: str
    result_count: int
    results: list[SearchResultItem]


class StudyRecordResponse(BaseModel):
    course_id: str
    book_id: str
    section_id: str
    mode: LearningMode
    status: Literal["in_progress", "completed"]
    progress: Literal[0, 100]
    started_at: str
    last_studied_at: str
    completed_at: str | None
    updated_at: str


class StudyRecordListResponse(BaseModel):
    course_id: str
    records: list[StudyRecordResponse]


class QAHistoryMessageDTO(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QARequest(BaseModel):
    question: str
    section_id: str | None = None
    history: list[QAHistoryMessageDTO] = Field(default_factory=list)


class QACitationItem(BaseModel):
    evidence_id: str
    source_kind: str
    source_id: str
    chapter_id: str | None
    section_id: str | None
    object_type: str | None
    type_zh: str | None
    number: str | None
    title_zh: str | None
    title_en: str | None
    printed_page: int | str | None
    pdf_page: int | None
    source_anchor: str | None


class QAResponse(BaseModel):
    course_id: str
    book_id: str
    question: str
    answer: str | None
    answer_kind: Literal["generated", "system_notice"]
    answer_style: AnswerStyle | None
    scope_requested: QAScopeRequested
    scope_used: QAScopeUsed
    insufficient_evidence: bool
    message: str | None
    citations: list[QACitationItem]
