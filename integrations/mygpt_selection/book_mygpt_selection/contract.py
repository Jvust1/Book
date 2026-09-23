"""Closed, bounded projections of the actual r6 Reader layers.

This module does not read learner state, authenticate callers, or call a model.
A digest identifies a projection; Authority supplies revocable authorization.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z')
RECORD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.'-]{0,159}\Z")
VERSION = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.@-]{0,159}\Z')
HEX = re.compile(r'[a-f0-9]{64}\Z')
MAX_PARTS = 512
MAX_CHARACTERS = 12000
MAX_PAYLOAD_BYTES = 64000

class BridgeError(ValueError):
    """Public errors contain fixed codes, never source text, secrets or paths."""
    def __init__(self, code: str, status: int = 422):
        self.code, self.status = code, status
        super().__init__(code)


def require(condition: bool, code: str, status: int = 422) -> None:
    if not condition:
        raise BridgeError(code, status)


def identifier(value: Any, *, version: bool = False) -> str:
    require(type(value) is str and (VERSION if version else ID).fullmatch(value) is not None,
            'INVALID_IDENTIFIER')
    return value


def record_identifier(value: Any) -> str:
    require(type(value) is str and RECORD_ID.fullmatch(value) is not None, 'INVALID_RECORD_IDENTIFIER')
    return value


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise BridgeError('INVALID_JSON') from None


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(data: bytes, limit: int = MAX_PAYLOAD_BYTES) -> Any:
    require(type(data) is bytes and len(data) <= limit, 'BODY_TOO_LARGE', 413)
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    def invalid_constant(_):
        raise BridgeError('INVALID_JSON_NUMBER')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, BridgeError):
            raise
        raise BridgeError('INVALID_JSON') from None


@dataclass(frozen=True)
class Selection:
    course_id: str
    book_id: str
    book_version_id: str
    section_id: str
    record_id: str
    layer: str
    layer_id: str | None
    portion: str
    representation: str

    @classmethod
    def parse(cls, value: Any) -> 'Selection':
        require(type(value) is dict and set(value) == set(cls.__dataclass_fields__), 'INVALID_SELECTION_FIELDS')
        for name in ('course_id', 'book_id', 'section_id'):
            identifier(value[name])
        identifier(value['book_version_id'], version=True)
        record_identifier(value['record_id'])
        require(value['layer'] in ('source', 'completion', 'correction', 'derived'), 'INVALID_LAYER')
        require(value['representation'] in ('raw', 'display'), 'INVALID_REPRESENTATION')
        if value['layer'] == 'source':
            require(value['layer_id'] is None, 'SOURCE_LAYER_ID_FORBIDDEN')
        else:
            record_identifier(value['layer_id'])
        require(value['portion'] in (('hint', 'solution') if value['layer'] == 'derived' else ('body',)),
                'INVALID_PORTION')
        return cls(**value)

    def json(self) -> dict:
        # Revalidate even if a Python caller bypassed parse() using the constructor.
        value = asdict(self)
        self.parse(value)
        return value


def text(value: Any, maximum: int = MAX_CHARACTERS) -> str:
    require(type(value) is str and len(value) <= maximum, 'INVALID_OR_OVERSIZED_TEXT')
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise BridgeError('INVALID_UNICODE') from None
    return value


def parts(value: Any, representation: str) -> tuple[list[dict], bool]:
    require(type(value) is list and len(value) <= MAX_PARTS, 'INVALID_OR_OVERSIZED_PARTS')
    result, excluded, characters = [], False, 0
    for part in value:
        require(type(part) is dict, 'INVALID_PART')
        if part.get('kind') == 'text':
            raw = text(part.get('text'))
            item = text(part['render_text']) if representation == 'display' and 'render_text' in part else raw
            result.append({'kind': 'text', 'text': item})
        elif part.get('kind') == 'math':
            raw = text(part.get('latex'))
            item = text(part.get('render_latex') or raw) if representation == 'display' else raw
            require(type(part.get('display', False)) is bool, 'INVALID_MATH_DISPLAY')
            result.append({'kind': 'math', 'latex': item, 'display': part.get('display', False)})
        else:
            excluded = True
            continue
        characters += len(item)
        require(characters <= MAX_CHARACTERS, 'SELECTION_TOO_LARGE', 413)
    return result, excluded


def indexed_records(section: dict) -> dict[str, dict]:
    records = section.get('records')
    require(type(records) is list and len(records) <= 20000, 'INVALID_RECORDS')
    index = {}
    for record in records:
        require(type(record) is dict, 'INVALID_RECORD')
        rid = record_identifier(record.get('id'))
        require(rid not in index, 'DUPLICATE_RECORD_ID')
        require(record.get('section_id') == section.get('id'), 'RECORD_SECTION_MISMATCH')
        index[rid] = record
    return index


def eligible_corrections(record: dict, manifest: dict, section: dict) -> list[dict]:
    result = []
    candidates = record.get('corrections', [])
    require(type(candidates) is list and len(candidates) <= 64, 'INVALID_CORRECTIONS')
    for c in candidates:
        if not isinstance(c, dict):
            continue
        if (c.get('record_id') == record['id'] and c.get('course_id') == manifest['course_id']
            and c.get('section_id') == section['id'] and c.get('confidence') == 'HIGH'
            and c.get('presentation') == 'prefer_corrected'
            and c.get('status') == 'CHECKED_BY_ASSISTANT'
            and c.get('evidence_status') == 'SCOPED_EVIDENCE_CHECKED'
            and c.get('source_preserved') is True and isinstance(c.get('check_ids'), list)
            and 0 < len(c['check_ids']) <= 64 and all(type(x) is str and 0 < len(x) <= 200 for x in c['check_ids'])
            and c.get('original_title') == record.get('title')
            and canonical(c.get('original_parts')) == canonical(record.get('parts'))
            and isinstance(c.get('corrected_parts'), list) and c['corrected_parts']):
            result.append(c)
    return result


def project(manifest: dict, section: dict, selection: Selection) -> dict:
    """Project one body/hint/solution; never infer a selection from reading time."""
    selected = selection.json()
    require(type(manifest) is dict and type(section) is dict, 'INVALID_SOURCE')
    for key in ('course_id', 'book_id', 'book_version_id'):
        require(manifest.get(key) == selected[key], 'SOURCE_VERSION_MISMATCH', 409)
    require(section.get('id') == selection.section_id, 'SOURCE_SECTION_MISMATCH', 409)
    require('book_version_id' not in section or section['book_version_id'] == selection.book_version_id,
            'SOURCE_VERSION_MISMATCH', 409)
    require(any(s.get('id') == selection.section_id for s in manifest.get('sections', []) if isinstance(s, dict)),
            'SECTION_NOT_IN_MANIFEST', 409)
    records = indexed_records(section)
    require(selection.record_id in records, 'RECORD_NOT_FOUND', 404)
    record = records[selection.record_id]
    chosen, parent_ids, warnings = record.get('parts'), [record['id']], []
    title = text(record.get('title', ''), 1000)
    origin = 'SOURCE_TRANSCRIPTION_NOT_INDEPENDENTLY_CERTIFIED'
    if selection.layer == 'source':
        if record.get('source_completion') or eligible_corrections(record, manifest, section):
            warnings.append('RAW_SOURCE_LAYER_MAY_DIFFER_FROM_DEFAULT_READER_BODY')
    elif selection.layer == 'completion':
        c = record.get('source_completion')
        require(type(c) is dict and c.get('id') == selection.layer_id, 'COMPLETION_NOT_FOUND', 404)
        require(c.get('origin') == 'source_visual_transcription_not_generated_proof', 'COMPLETION_ORIGIN_MISMATCH')
        chosen = c.get('parts')
        origin = 'SOURCE_COMPLETION_TRANSCRIPTION_NOT_INDEPENDENTLY_CERTIFIED'
    elif selection.layer == 'correction':
        matches = eligible_corrections(record, manifest, section)
        require(len(matches) == 1 and matches[0].get('id') == selection.layer_id,
                'CORRECTION_NOT_UNIQUELY_ELIGIBLE', 409)
        chosen = matches[0]['corrected_parts']
        origin = 'AI_CORRECTION_NOT_TEXTBOOK_NOT_OFFICIAL_ERRATUM'
    else:
        groups = section.get('practice_groups', [])
        require(type(groups) is list and len(groups) <= 20000, 'INVALID_GROUPS')
        matches = [g for g in groups if isinstance(g, dict) and g.get('id') == selection.layer_id]
        require(len(matches) == 1, 'DERIVED_GROUP_NOT_UNIQUE', 409)
        group = matches[0]
        require(group.get('anchor_id') == record['id'], 'DERIVED_ANCHOR_MISMATCH')
        parent_ids = group.get('record_ids')
        require(type(parent_ids) is list and 0 < len(parent_ids) <= 32
                and all(type(x) is str for x in parent_ids) and len(set(parent_ids)) == len(parent_ids)
                and record['id'] in parent_ids and all(x in records for x in parent_ids), 'DERIVED_SOURCE_CLOSURE')
        guide = group.get('derived_guidance')
        require(type(guide) is dict and guide.get('textbook_official_solution') is False
                and guide.get('source_record_ids') == parent_ids, 'DERIVED_GUIDANCE_IDENTITY')
        source_sections = guide.get('source_sections')
        known = {s['id'] for s in manifest['sections']}
        require(type(source_sections) is list and 0 < len(source_sections) <= 32
                and all(type(x) is str and x in known for x in source_sections), 'DERIVED_SECTION_CLOSURE')
        chosen = guide.get(selection.portion + '_parts')
        title = text(group.get('title', ''), 1000)
        origin = 'AI_DERIVED_NOT_TEXTBOOK_NOT_OFFICIAL_SOLUTION'
    projected, excluded = parts(chosen, selection.representation)
    require(projected and any(p.get('text', p.get('latex', '')).strip() for p in projected), 'EMPTY_BODY')
    if excluded:
        warnings.append('NON_TEXT_PARTS_EXCLUDED')
    parents = []
    for rid in parent_ids:
        raw_parts, _ = parts(records[rid].get('parts'), 'raw')
        parents.append({'record_id': rid, 'source_parts_sha256': digest(raw_parts)})
    payload = {'schema': 'book.selected-content.v1', 'selection': selected,
               'title': title, 'parts': projected, 'origin': origin,
               'parent_sources': parents, 'warnings': warnings,
               'qualification': 'BODY_ONLY_NO_IMAGES_NO_NOTES_NO_ANSWERS;INDEPENDENT_REVIEW_PENDING'}
    require(len(canonical(payload)) <= MAX_PAYLOAD_BYTES, 'SELECTION_TOO_LARGE', 413)
    return payload


class FileReader:
    """Fresh reads of a verified r6 root; never reads any SQLite/learner file."""
    def __init__(self, root: Path, *, expected_files: dict[str, str] | None = None):
        self.root = Path(root).resolve(strict=True)
        self.expected_files = dict(expected_files) if expected_files is not None else None
        self.packs = (self.root / 'coursepacks').resolve(strict=True)
        require(self.packs.is_relative_to(self.root), 'UNSAFE_SOURCE_ROOT')

    def _bytes(self, path: Path, limit: int) -> bytes:
        try:
            resolved = path.resolve(strict=True)
            require(path.absolute() == resolved, 'SYMLINK_SOURCE_PATH_FORBIDDEN', 404)
            path = resolved
            require(path.is_relative_to(self.packs) and path.is_file(), 'UNSAFE_SOURCE_PATH', 404)
            with path.open('rb') as stream:
                data = stream.read(limit + 1)
            require(len(data) <= limit, 'SOURCE_TOO_LARGE', 413)
            if self.expected_files is not None:
                relative = path.relative_to(self.root).as_posix()
                require(self.expected_files.get(relative) == hashlib.sha256(data).hexdigest(),
                        'SOURCE_IDENTITY_CHANGED_RESTART', 409)
            return data
        except (OSError, RuntimeError):
            raise BridgeError('SOURCE_UNAVAILABLE', 404) from None

    def catalog(self) -> dict:
        data = decode(self._bytes(self.packs / 'catalog.json', 65536), 65536)
        require(type(data) is dict and type(data.get('courses')) is list
                and len(data['courses']) <= 256, 'INVALID_CATALOG')
        for cid in data['courses']:
            identifier(cid)
        require(len(set(data['courses'])) == len(data['courses']), 'DUPLICATE_COURSE')
        return data

    def manifest(self, course_id: str) -> dict:
        identifier(course_id)
        require(course_id in self.catalog()['courses'], 'COURSE_NOT_FOUND', 404)
        data = decode(self._bytes(self.packs / course_id / 'manifest.json', 524288), 524288)
        require(type(data) is dict and data.get('course_id') == course_id, 'MANIFEST_IDENTITY')
        identifier(data.get('book_id')); identifier(data.get('book_version_id'), version=True)
        require(type(data.get('sections')) is list and len(data['sections']) <= 10000, 'INVALID_MANIFEST')
        ids = [identifier(s.get('id')) for s in data['sections'] if isinstance(s, dict)]
        require(len(ids) == len(data['sections']) and len(set(ids)) == len(ids), 'DUPLICATE_SECTION')
        return data

    def snapshot(self, course_id: str, section_id: str) -> tuple[dict, dict]:
        identifier(section_id)
        manifest = self.manifest(course_id)
        require(section_id in {s['id'] for s in manifest['sections']}, 'SECTION_NOT_FOUND', 404)
        section = decode(self._bytes(self.packs / course_id / 'sections' / (section_id + '.json'), 4194304), 4194304)
        require(type(section) is dict and section.get('id') == section_id, 'SECTION_IDENTITY')
        require(canonical(manifest) == canonical(self.manifest(course_id)), 'SOURCE_CHANGED_DURING_READ', 409)
        return manifest, section

    def project(self, selection: Selection) -> dict:
        return project(*self.snapshot(selection.course_id, selection.section_id), selection)
