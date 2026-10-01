#!/usr/bin/env python3
"""Apply explicit, source-hash-bound HTML corrections without overwriting originals.

A patch author, not this program, must inspect the cited scan evidence. This
program verifies identities and limits changes; it does not certify semantics.
No network access, OCR, implicit text cleanup, or main-repository mutation.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_child(root: Path, relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('Unsafe relative path')
    dest = (root / p).resolve()
    if not dest.is_relative_to(root.resolve()):
        raise ValueError('Path escapes source root')
    return dest


def patch_document(original: dict, operations: list[dict], evidence: set[str]) -> tuple[dict, list[dict]]:
    doc = copy.deepcopy(original)
    blocks = doc.get('blocks', [])
    ids = [b.get('id') for b in blocks]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Missing or duplicate original block IDs')
    log = []
    retired_ids = set()
    for op in operations:
        refs = op.get('evidence_ids', [])
        if not refs or not set(refs) <= evidence:
            raise ValueError('Missing or unknown source evidence')
        action = op['op']
        index = {b['id']: i for i, b in enumerate(blocks)}
        if action == 'replace':
            bid = op['block_id']
            b = blocks[index[bid]]
            if digest(b['html'].encode()) != op['expected_html_sha256']:
                raise ValueError('Original HTML hash mismatch')
            if not isinstance(op.get('html'), str) or not op['html'].strip():
                raise ValueError('Replacement HTML must be nonempty')
            before = b['html']
            b['html'] = op['html']
            b['plain'] = BeautifulSoup(b['html'], 'html.parser').get_text(' ', strip=True)
            if 'kind' in op:
                b['kind'] = op['kind']
            # Derived reader fields would otherwise describe the OLD body.
            for key in list(b):
                if key.startswith('reader_'):
                    del b[key]
            b['evidence_patch'] = {'evidence_ids': refs, 'reason': op['reason'],
                                   'historical_source_quality_retained': True}
            log.append({'op': action, 'block_id': bid, 'before_html_sha256': digest(before.encode()),
                        'after_html_sha256': digest(b['html'].encode()), 'evidence_ids': refs,
                        'reason': op['reason']})
        elif action == 'insert_after':
            after = op['after_block_id']
            b = copy.deepcopy(op['block'])
            if not isinstance(b.get('id'), str) or not b['id'] or b['id'] in index:
                raise ValueError('Invalid inserted block ID')
            if not isinstance(b.get('html'), str) or not b['html'].strip():
                raise ValueError('Inserted HTML must be nonempty')
            b['plain'] = BeautifulSoup(b['html'], 'html.parser').get_text(' ', strip=True)
            b['evidence_patch'] = {'evidence_ids': refs, 'reason': op['reason']}
            blocks.insert(index[after] + 1, b)
            log.append({'op': action, 'block_id': b['id'], 'after_block_id': after,
                        'after_html_sha256': digest(b['html'].encode()), 'evidence_ids': refs,
                        'reason': op['reason']})
        elif action == 'retire_duplicate':
            bid, kept = op['block_id'], op['duplicate_of_block_id']
            if bid == kept:
                raise ValueError('A duplicate cannot designate itself')
            b, reference = blocks[index[bid]], blocks[index[kept]]
            if digest(b['html'].encode()) != op['expected_html_sha256']:
                raise ValueError('Duplicate HTML identity mismatch')
            normalize = lambda value: ''.join(BeautifulSoup(value, 'html.parser').get_text().split())
            removed_text, kept_text = normalize(b['html']), normalize(reference['html'])
            if not removed_text or removed_text not in kept_text:
                raise ValueError('Declared duplicate text is not present in kept block')
            doc.setdefault('retired_duplicate_blocks', []).append({
                'original_block': copy.deepcopy(b), 'duplicate_of_block_id': kept,
                'evidence_ids': refs, 'reason': op['reason']})
            blocks.pop(index[bid]); retired_ids.add(bid)
            log.append({'op': action, 'block_id': bid, 'duplicate_of_block_id': kept,
                        'before_html_sha256': digest(b['html'].encode()),
                        'exact_nonspace_text_retained_in_kept_block': True,
                        'archived_original_block': True, 'evidence_ids': refs, 'reason': op['reason']})
        elif action == 'archive_source_artifact':
            # Explicit, evidence-bound retirement only. This is never a heuristic filter.
            bid = op['block_id']
            b = blocks[index[bid]]
            category = op.get('artifact_kind')
            if category not in {'running_header', 'decorative_ocr', 'overlapping_transcription'}:
                raise ValueError('Unapproved source-artifact category')
            if digest(b['html'].encode()) != op.get('expected_html_sha256'):
                raise ValueError('Source-artifact HTML identity mismatch')
            retained = op.get('retained_by')
            if (not isinstance(retained, list) or not retained or
                    any(not isinstance(x, str) or x not in index or x == bid for x in retained) or
                    len(set(retained)) != len(retained)):
                raise ValueError('A live, distinct retained anchor is required')
            if not isinstance(op.get('source_comparison'), str) or not op['source_comparison'].strip():
                raise ValueError('Explicit source comparison is required')
            if not isinstance(op.get('reason'), str) or not op['reason'].strip():
                raise ValueError('Explicit retirement reason is required')
            aliases = doc.setdefault('anchor_aliases', {})
            if not isinstance(aliases, dict):
                raise ValueError('Anchor aliases must be a dictionary')
            if bid in aliases and aliases[bid] != retained[0]:
                raise ValueError('Existing anchor alias conflict')
            aliases[bid] = retained[0]
            entry = {'original_block': copy.deepcopy(b), 'retained_by': list(retained),
                     'artifact_kind': category, 'source_comparison': op['source_comparison'],
                     'evidence_ids': refs, 'reason': op['reason'],
                     'before_html_sha256': digest(b['html'].encode())}
            doc.setdefault('retired_source_artifacts', []).append(entry)
            blocks.pop(index[bid]); retired_ids.add(bid)
            log.append({k: copy.deepcopy(v) for k, v in entry.items() if k != 'original_block'} | {
                'op': action, 'block_id': bid, 'archived_original_block': True,
                'automatic_semantic_equivalence_claimed': False})
        elif action == 'move_after':
            bid, after = op['block_id'], op['after_block_id']
            if bid == after:
                raise ValueError('Cannot move a block after itself')
            b = blocks.pop(index[bid])
            index = {x['id']: i for i, x in enumerate(blocks)}
            blocks.insert(index[after] + 1, b)
            log.append({'op': action, 'block_id': bid, 'after_block_id': after,
                        'evidence_ids': refs, 'reason': op['reason']})
        else:
            raise ValueError('Unsupported patch operation')
    final_ids = [b['id'] for b in blocks]
    if len(final_ids) != len(set(final_ids)) or not set(ids) <= (set(final_ids) | retired_ids):
        raise AssertionError('Original block identity lost')
    for item in log:
        if item['op'] == 'archive_source_artifact':
            if not set(item['retained_by']) <= set(final_ids):
                raise ValueError('Retirement target must remain live after all operations')
    replaced = {x['block_id'] for x in log if x['op'] == 'replace'}
    original_map = {b['id']: b for b in original['blocks']}
    for b in blocks:
        if b['id'] in original_map and b['id'] not in replaced and b != original_map[b['id']]:
            raise AssertionError('Unapproved original block changed')
    return doc, log


def apply_patch(source_root: Path, scan_pdf: Path, spec_path: Path, destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError('Use a new version directory; no overwrite permitted')
    if destination.resolve().is_relative_to(source_root.resolve()):
        raise ValueError('Destination must be outside original source root')
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    if spec.get('schema') != 'book-evidence-patch-v1':
        raise ValueError('Unsupported patch schema')
    if digest(scan_pdf.read_bytes()) != spec['source_scan_sha256']:
        raise ValueError('Scan identity mismatch')
    evidence = set(spec['evidence_ids'])
    if len(evidence) != len(spec['evidence_ids']):
        raise ValueError('Duplicate evidence IDs')
    changes = []; prepared = []; seen = set()
    for change in spec['documents']:
        path = safe_child(source_root, change['file'])
        if path in seen:
            raise ValueError('Duplicate document specification')
        seen.add(path)
        raw = path.read_bytes()
        if digest(raw) != change['expected_json_sha256']:
            raise ValueError('Source document identity mismatch')
        original = json.loads(raw)
        if original['id'] != change['document_id']:
            raise ValueError('Document ID mismatch')
        doc, log = patch_document(original, change['operations'], evidence)
        doc['finalized'] = False
        doc['content_revision'] = spec['revision']
        doc['source_record_ids'] = [b['id'] for b in doc['blocks']]
        previous_provenance = copy.deepcopy(original.get('evidence_patch_provenance'))
        doc['evidence_patch_provenance'] = {
            'parent_json_sha256': digest(raw), 'source_scan_sha256': spec['source_scan_sha256'],
            'patch_spec_sha256': digest(spec_path.read_bytes()),
            'source_pdf_and_tex_fields_role': 'historical parent identities, not rebuilt output identities',
            'academic_acceptance': False, 'review_scope': change['review_scope'],
            'previous_patch_provenance': previous_provenance}
        doc['academic_review'] = {'status': 'PARTIAL_SOURCE_VISUAL_CORRECTION',
                                  'full_academic_acceptance': False,
                                  'previous_review': original.get('academic_review')}
        for key in list(doc):
            if key.startswith('reader_'):
                del doc[key]
        encoded = (json.dumps(doc, ensure_ascii=False, indent=2) + '\n').encode()
        prepared.append((change['file'], raw, encoded))
        changes.append({'document_id': doc['id'], 'before_json_sha256': digest(raw),
                        'after_json_sha256': digest(encoded), 'original_blocks': len(original['blocks']),
                        'updated_blocks': len(doc['blocks']), 'operations': log})
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='.evidence-patch-', dir=destination.parent))
    try:
        # Frozen originals and the working source are different subtrees.
        for relative, raw, encoded in prepared:
            for tree, data in [('source_original', raw), ('source', encoded)]:
                p = safe_child(tmp / tree, relative); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
        assets = source_root / 'document-assets'
        if assets.is_dir():
            for p in assets.rglob('*'):
                if p.is_symlink():
                    raise ValueError('Symlink asset rejected')
            shutil.copytree(assets, tmp / 'source' / 'document-assets')
        result = {'schema': 'book-evidence-patch-result-v1', 'revision': spec['revision'],
                  'source_scan_sha256': spec['source_scan_sha256'], 'documents': changes,
                  'originals_overwritten': False, 'semantic_acceptance': False}
        (tmp / 'patch_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        tmp.rename(destination)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_root', type=Path); p.add_argument('scan_pdf', type=Path)
    p.add_argument('spec', type=Path); p.add_argument('destination', type=Path)
    a = p.parse_args()
    print(json.dumps(apply_patch(a.source_root,a.scan_pdf,a.spec,a.destination), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
