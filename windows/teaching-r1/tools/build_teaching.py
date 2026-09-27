#!/usr/bin/env python3
"""Compile authored teaching sidecars. Never mutate textbook/source/study files.

References identify relevant source topics, NOT an assertion that a newly authored
answer occurs in the textbook. No network, model calls, or stochastic generation.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'web' / 'data'
DROP = {'whitespace', 'page_header', 'running_header', 'page_number',
        'toc_ocr_evidence', 'table_of_contents', 'cover', 'frontmatter',
        'bibliography', 'reference', 'references', 'source_metadata',
        'chapter', 'chapter_title', 'chapter_opening', 'section', 'section_title',
        'subsection', 'subsection_title', 'subheading', 'heading', 'index_entry'}
CATEGORIES = {
    'definition': '定义与概念', 'concept': '定义与概念',
    'theorem': '定理与命题', 'lemma': '定理与命题',
    'proposition': '定理与命题', 'corollary': '定理与命题',
    'equation': '公式与关系', 'formula': '公式与关系',
    'proof': '证明与推导', 'example': '例题与说明',
    'figure': '图表', 'image': '图表', 'table': '图表',
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text(r: dict) -> str:
    return str(r.get('text') or r.get('latex') or '') + ' '.join(
        (str(p.get('text') or p.get('latex') or '') if isinstance(p, dict) else str(p)) for p in (r.get('parts') or []))

def write_changed(path: Path, obj: dict) -> None:
    data = (json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)

def compile_book(meta: dict) -> dict:
    bid = meta['id']
    path = DATA / (bid + '.json')
    book = json.loads(path.read_text())
    source = ROOT / 'content' / 'teaching' / (bid + '.json')
    authored = json.loads(source.read_text())
    if authored.get('book_id') != bid or authored.get('schema') != 'book-authored-teaching-v1':
        raise ValueError('Authored book identity mismatch: ' + bid)
    sections = {s['id']: s for s in book['sections']}
    byid = {r['id']: r for r in book['records']}
    units, solved, ids = [], [], set()
    for original in authored['units']:
        u = copy.deepcopy(original)
        if u['id'] in ids:
            raise ValueError('Duplicate unit: ' + u['id'])
        ids.add(u['id'])
        if not u['sections'] or any(sid not in sections for sid in u['sections']):
            raise ValueError('Unresolved section in ' + u['id'] + ': ' + repr(u['sections']))
        # Keep real existing references from EACH exact declared section.
        refs = []
        for sid in u['sections']:
            rr = [byid[rid] for rid in sections[sid].get('record_ids', []) if rid in byid]
            ranked = sorted(rr, key=lambda r: (
                r.get('body_visible') is False,
                r.get('type') in DROP,
                r.get('quality_tier') == 'C_MACHINE_DRAFT',
                not bool(text(r).strip()),
            ))
            for r in ranked[:3]:
                refs.append({'record_id': r['id'], 'section_id': sid,
                             'pdf_pages': r.get('source_pdf_pages', []),
                             'quality_tier': r.get('quality_tier', 'INDEX_OR_LEGACY'),
                             'relation': 'topic_locator_not_answer_evidence'})
        if not refs:
            raise ValueError('No actual topic references for ' + u['id'])
        u['source_refs'] = refs
        u['source_book_sha256'] = sha(path)
        u['origin'] = 'AI_AUTHORED_SUPPLEMENT'
        u['independent_expert_review'] = False
        for n, p in enumerate(u.pop('problems'), 1):
            if len(p['steps']) < 2 or not all(p.get(k, '').strip() for k in ('stem', 'hint', 'answer', 'pitfall')):
                raise ValueError('Incomplete worked answer in ' + u['id'])
            gid = 'teaching-v1:' + u['id'] + ':' + str(n)
            solved.append({**p, 'id': gid, 'unit_id': u['id'],
                           'section': u['sections'][0], 'section_ids': u['sections'],
                           'origin': 'authored_worked_problem',
                           'source_question': p['stem'],
                           'record_ids': list(dict.fromkeys(r['record_id'] for r in refs)),
                           'anchor_id': refs[0]['record_id'], 'source_refs': refs,
                           'answer_status': 'worked_reference_not_textbook_standard_answer',
                           'independent_expert_review': False})
        u['problem_ids'] = [p['id'] for p in solved if p['unit_id'] == u['id']]
        units.append(u)
    review = {}
    for sid, section in sections.items():
        groups = {}
        for rid in section.get('record_ids', []):
            r = byid.get(rid)
            if not r or r.get('body_visible') is False or r.get('type') in DROP:
                continue
            if r.get('type') in {'exercise', 'exercise_group', 'problem', 'question'}:
                continue
            if not text(r).strip() and not r.get('images'):
                continue
            kind = CATEGORIES.get(r.get('type'), '知识论述与补充')
            groups.setdefault(kind, []).append(rid)
        review[sid] = groups
    covered = sorted({sid for u in units for sid in u['sections']})
    return {'schema': 'book-teaching-sidecar-v1', 'book_id': bid,
            'source_book_sha256': sha(path), 'authored_source_sha256': sha(source),
            'source_boundary': 'Topic references locate related material; worked problems are newly authored, not textbook answers.',
            'whole_book_authored_complete': False,
            'index_only_source': meta.get('index_only', False),
            'units': units, 'solved': solved, 'review_by_section': review,
            'coverage': {'authored_units': len(units), 'worked_problems': len(solved),
                         'authored_sections': len(covered), 'authored_section_ids': covered,
                         'total_source_sections': len(sections),
                         'review_source_records': len({rid for g in review.values() for rr in g.values() for rid in rr}),
                         'review_source_complete_for_included_visible_records': True,
                         'whole_book_knowledge_acceptance': False}}

def main() -> None:
    cat = json.loads((DATA / 'catalog.json').read_text())
    result = {'schema': 'book-teaching-build-v1', 'build': cat['build_id'], 'books': []}
    for meta in cat['books']:
        compiled = compile_book(meta)
        target = DATA / (meta['id'] + '.teaching.json')
        write_changed(target, compiled)
        result['books'].append({'book_id': meta['id'], **compiled['coverage'],
                                'sidecar_sha256': sha(target),
                                'source_book_sha256': compiled['source_book_sha256']})
    result['authored_units'] = sum(b['authored_units'] for b in result['books'])
    result['worked_problems'] = sum(b['worked_problems'] for b in result['books'])
    result['authored_sections'] = sum(b['authored_sections'] for b in result['books'])
    result['review_source_records'] = sum(b['review_source_records'] for b in result['books'])
    write_changed(ROOT / 'verification' / 'teaching_compilation.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'books'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
