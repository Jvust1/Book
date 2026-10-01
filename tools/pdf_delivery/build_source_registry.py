#!/usr/bin/env python3
"""Link recovered reading documents to v5 PDF manifests, without asserting content equality.

Read-only inputs. The output contains metadata and hashes, never textbook paragraphs.
Requires PyMuPDF solely to independently count pages of archived source PDFs.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

BOOKS = {
    'fa': 'functional_analysis_2e_jiang_sun',
    'pde': 'mathematical_physics_equations_4e',
    'fe': 'financial-economics-ten-lectures',
    'pf': 'public_finance_intro_2e_2024',
    'ce': 'contemporary-china-economy',
    'mf': 'monetary-finance-3e',
}
MODES = {'学习': 'learn', '预习': 'preview', '复习': 'review', '刷题': 'practice'}
EXPECTED_COUNTS = {'fa': 21, 'pde': 29, 'fe': 41, 'pf': 60, 'ce': 45, 'mf': 57}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive_path(url: str) -> str:
    """Accept only local archive paths, rejecting traversal and opaque external URLs."""
    if not isinstance(url, str) or not url:
        raise ValueError('empty resource path')
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or parts.query or parts.fragment:
        raise ValueError(f'not a plain local path: {url!r}')
    decoded = unquote(parts.path)
    if '\\' in decoded or '\x00' in decoded or decoded.startswith('//'):
        raise ValueError('ambiguous path separator')
    relative = decoded[1:] if decoded.startswith('/') else decoded
    segments = relative.split('/')
    if not relative or any(s in ('', '.', '..') or ':' in s for s in segments):
        raise ValueError('unsafe archive path')
    return relative


def candidate_key(code: str, name: str) -> tuple[str, int, str] | None:
    """Only explicit individual mode folders qualify; combined books never do."""
    p = PurePosixPath(archive_path(name))
    if len(p.parts) != 2 or p.parts[0] not in MODES:
        return None
    match = re.match(r'^(\d+)_', p.name)
    if not match or p.suffix.lower() != '.pdf':
        return None
    return code, int(match[1]), MODES[p.parts[0]]


class ImageSources(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == 'img':
            value = dict(attrs).get('src')
            if value:
                self.sources.append(value)


def image_sources(html: str) -> list[str]:
    parser = ImageSources()
    parser.feed(html)
    return parser.sources


def load_candidates(root: Path) -> tuple[dict, list]:
    index: dict[tuple, list] = collections.defaultdict(list)
    manifests = []
    for code in BOOKS:
        for kind in ('teaching', 'learn'):
            path = root / code / (kind + '.json')
            raw = path.read_bytes()
            obj = json.loads(raw)
            identity = {'path': path.relative_to(root).as_posix(), 'sha256': sha(raw),
                        'bytes': len(raw), 'title': obj.get('title', obj.get('book', {}).get('title'))}
            manifests.append(identity)
            for item in obj['files']:
                key = candidate_key(code, item['file'])
                if key is not None:
                    if (kind == 'learn') != (key[2] == 'learn'):
                        raise ValueError('mode and manifest kind disagree')
                    index[key].append({**item, 'manifest': identity,
                                       'derived_from': obj.get('derived_from', {})})
    return index, manifests


def build_registry(archive: Path, manifests_root: Path) -> dict:
    import fitz
    candidates, manifests = load_candidates(manifests_root)
    rows, global_assets, missing_assets = [], set(), set()
    counts, source_failures, structural_errors = collections.Counter(), [], []
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive member names')
        name_set = set(names)
        for name in sorted(names):
            if not (name.startswith('documents/') and name.endswith('.json')):
                continue
            raw = zf.read(name)
            doc = json.loads(raw)
            if not isinstance(doc, dict) or doc.get('schema') != 'book-reflow-document-v1':
                continue
            match = re.fullmatch(r'(fa|pde|fe|pf|ce|mf)-(\d+)-(learn|preview|review|practice)', doc['id'])
            if not match:
                raise ValueError(f'unrecognized document id: {doc["id"]!r}')
            code, number, mode = match.groups()
            key = (code, int(number), mode)
            if doc['book_id'] != BOOKS[code] or doc['chapter'] != int(number) or doc['mode'] != mode:
                raise ValueError(f'document identity conflict: {doc["id"]}')
            counts[code] += 1
            source = doc['source_pdf']
            member = archive_path(source['url'])
            payload = zf.read(member)
            with fitz.open(stream=payload, filetype='pdf') as pdf:
                pages = len(pdf)
            pdf_ok = len(payload) == source['bytes'] and sha(payload) == source['sha256'] and pages == source['pages']
            if not pdf_ok:
                source_failures.append(doc['id'])
            target = candidates.get(key, [])
            if len(target) == 1:
                selected = target[0]
                level = 'UNIQUE_BOOK_CHAPTER_MODE_MANIFEST_CANDIDATE'
                if selected['sha256'] == source['sha256']:
                    level = 'SOURCE_PDF_SHA_EQUALS_V5_MANIFEST_SHA'
            else:
                selected = None
                level = 'NO_CANDIDATE' if not target else 'AMBIGUOUS_CANDIDATES'
                structural_errors.append({'id': doc['id'], 'candidate_count': len(target)})
            assets, invalid = set(), set()
            kinds, inherited_quality = collections.Counter(), collections.Counter()
            image_blocks = editable_false = changed_reader_blocks = 0
            for block in doc['blocks']:
                kinds[block.get('kind', 'unknown')] += 1
                q = block.get('source', {}).get('quality')
                if q:
                    inherited_quality[q] += 1
                editable_false += block.get('editable') is False
                html = block.get('html', '')
                reader = block.get('reader_html', html)
                changed_reader_blocks += reader != html
                refs = set(image_sources(html) + image_sources(reader))
                image_blocks += bool(refs)
                for ref in refs:
                    try:
                        assets.add(archive_path(ref))
                    except ValueError:
                        invalid.add(ref)
            missing = sorted(assets - name_set)
            missing_assets.update(missing)
            global_assets.update(assets)
            prior_full_sha = source.get('full_source', {}).get('sha256')
            derived_sha = (selected or {}).get('derived_from', {}).get('v4_full_pdf_sha256')
            rows.append({
                'id': doc['id'], 'book_code': code, 'book_id': doc['book_id'],
                'book_title': doc['book_title'], 'chapter': int(number), 'title': doc['title'], 'mode': mode,
                'historical_json': {'path': name, 'sha256': sha(raw), 'bytes': len(raw)},
                'historical_source_pdf': {**source, 'archive_path': member, 'actual_pages': pages,
                                          'bytes_sha256_and_pages_verified': pdf_ok},
                'v5_candidate': selected, 'candidate_count': len(target), 'matching_level': level,
                'same_page_count': bool(selected and pages == selected['pages']),
                'explicit_v4_full_source_lineage_hash_match': bool(prior_full_sha and prior_full_sha == derived_sha),
                'v5_actual_pdf_download_and_comparison': 'NOT_PERFORMED_BY_THIS_REGISTRY',
                'content_equivalence': 'NOT_ESTABLISHED', 'academic_reverification': False,
                'blocks': {'count': len(doc['blocks']), 'kinds': dict(kinds), 'editable_false': editable_false,
                           'image_bearing': image_blocks, 'changed_reader_html': changed_reader_blocks,
                           'inherited_quality_labels_not_reverified': dict(inherited_quality)},
                'assets': {'img_src_paths': sorted(assets), 'unique_count': len(assets),
                           'svg_count': sum(s.lower().endswith('.svg') for s in assets),
                           'missing_paths': missing, 'external_or_invalid_img_src': sorted(invalid)},
            })
    if dict(counts) != EXPECTED_COUNTS:
        structural_errors.append({'actual_counts': dict(counts), 'expected_counts': EXPECTED_COUNTS})
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        structural_errors.append({'duplicate_document_ids': True})
    return {
        'schema': 'book-v7-historical-to-v5-registry-v1',
        'scope': '1.3.0-final-r2 historical 253 documents; not the later Windows 1.3.1 249-document baseline',
        'manifest_count': len(manifests), 'manifests': manifests,
        'summary': {
            'documents': len(rows), 'books': len(counts), 'by_book': dict(sorted(counts.items())),
            'by_mode': dict(collections.Counter(r['mode'] for r in rows)),
            'matching_levels': dict(collections.Counter(r['matching_level'] for r in rows)),
            'same_page_count': sum(r['same_page_count'] for r in rows),
            'explicit_v4_lineage_hash_match': sum(r['explicit_v4_full_source_lineage_hash_match'] for r in rows),
            'original_source_pdf_verified': len(rows) - len(source_failures),
            'original_source_pdf_failures': source_failures, 'structural_errors': structural_errors,
            'unique_img_src_assets': len(global_assets), 'missing_img_src_assets': sorted(missing_assets),
            'external_or_invalid_img_src': sum(len(r['assets']['external_or_invalid_img_src']) for r in rows),
            'image_bearing_blocks': sum(r['blocks']['image_bearing'] for r in rows),
            'editable_false_blocks': sum(r['blocks']['editable_false'] for r in rows),
            'content_equivalent_documents_claimed': 0,
        }, 'documents': rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('manifests', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    registry = build_registry(args.archive, args.manifests)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = registry['summary']
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return int(bool(summary['structural_errors'] or summary['original_source_pdf_failures']
                    or summary['missing_img_src_assets'] or summary['external_or_invalid_img_src']))


if __name__ == '__main__':
    raise SystemExit(main())
