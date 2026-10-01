#!/usr/bin/env python3
"""Conservative glyph-position audit, not a semantic or academic equivalence claim."""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path
import fitz
FLAGS = fitz.TEXTFLAGS_RAWDICT & ~fitz.TEXT_PRESERVE_IMAGES

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def glyph_key(char: dict) -> tuple:
    return (char['c'], *(round(float(v), 2) for v in char['origin']))

def lines_of(page: fitz.Page) -> list[dict]:
    lines = []
    for b in page.get_text('rawdict', flags=FLAGS)['blocks']:
        if b.get('type') != 0: continue
        for line in b['lines']:
            chars = []
            for span in line['spans']:
                for ch in span['chars']:
                    if not ch['c'].isspace():
                        chars.append({**ch, 'font': span['font'], 'size': span['size']})
            if chars:
                lines.append({'chars': chars, 'bbox': line['bbox'], 'text': ''.join(c['c'] for c in chars)})
    return lines

def compare_pages(before: fitz.Page, after: fitz.Page) -> dict:
    old_lines = lines_of(before); new_lines = lines_of(after)
    old = collections.Counter(glyph_key(c) for l in old_lines for c in l['chars'])
    new = collections.Counter(glyph_key(c) for l in new_lines for c in l['chars'])
    missing = old - new; added = new - old
    # Roundoff at a bin boundary is not a deletion. Match remaining same-character
    # positions within 0.05 PDF pt, recording the tolerance explicitly.
    tolerance_matches=0
    by_char=collections.defaultdict(list)
    for key in added: by_char[key[0]].append(key)
    for key in list(missing):
        for target in by_char[key[0]]:
            if missing[key] and added[target] and abs(key[1]-target[1])<=0.050001 and abs(key[2]-target[2])<=0.050001:
                n=min(missing[key],added[target]);missing[key]-=n;added[target]-=n;tolerance_matches+=n
    original_missing = missing.copy();changes=[]
    for line in old_lines:
        chars=[]
        for ch in line['chars']:
            k=glyph_key(ch)
            if missing[k]:missing[k]-=1;chars.append(ch)
        if chars:
            text=''.join(c['c'] for c in chars)
            in_body = line['bbox'][1] > 45 and line['bbox'][3] < before.rect.height-35
            math_font = any(('Math' in c['font'] or 'STIX' in c['font'] or 'Symbol' in c['font']) for c in chars)
            label = ('MARGIN_CHANGE' if not in_body else 'MATH_GLYPH_REMOVAL_CANDIDATE' if math_font else 'SOURCE_OR_TECHNICAL_LINE_CANDIDATE' if any(s in line['text'] for s in ('来源PDF','纸书','结构化','Bookr3','原书脚注')) else 'BODY_TEXT_CHANGE_REVIEW_REQUIRED')
            changes.append({'line':line['text'],'removed':text,'bbox':list(line['bbox']),
                            'removed_bbox':[min(c['bbox'][0] for c in chars),min(c['bbox'][1] for c in chars),max(c['bbox'][2] for c in chars),max(c['bbox'][3] for c in chars)],
                            'label':label,'count':len(chars), 'whole_nonspace_line_removed': len(chars)==len(line['chars'])})
    return {'before_nonspace_glyphs':sum(old.values()),'after_nonspace_glyphs':sum(new.values()),
            'removed_position_glyphs':sum(original_missing.values()),'added_position_glyphs':sum(added.values()),
            'geometry_equal': list(before.rect)==list(after.rect), 'position_tolerance_pt':0.05, 'position_tolerance_matches':tolerance_matches, 'changes':changes}

def audit_document(before: bytes, after: bytes, doc_id: str) -> dict:
    with fitz.open(stream=before,filetype='pdf') as a, fitz.open(stream=after,filetype='pdf') as b:
        if a.page_count != b.page_count:raise ValueError(f'{doc_id}: page counts differ; no index-based comparison permitted')
        pages = [compare_pages(x,y) for x,y in zip(a,b)]
    labels=collections.Counter(c['label'] for p in pages for c in p['changes'])
    return {'id':doc_id,'old_sha256':sha256(before),'v5_sha256':sha256(after),'pages':len(pages),
            'geometry_equal':all(p['geometry_equal'] for p in pages),
            'removed_position_glyphs':sum(p['removed_position_glyphs'] for p in pages),
            'added_position_glyphs':sum(p['added_position_glyphs'] for p in pages),
            'triage_labels':dict(labels),'page_differences':pages,
            'content_equivalence':'NOT_ESTABLISHED','academic_review':False}

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('before',type=Path);ap.add_argument('after',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args(); result=audit_document(args.before.read_bytes(),args.after.read_bytes(),args.before.stem)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return 0
if __name__=='__main__':raise SystemExit(main())
