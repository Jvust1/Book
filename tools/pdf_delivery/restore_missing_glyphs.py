#!/usr/bin/env python3
"""Restore only explicitly approved missing source glyphs at unchanged coordinates.

This is a visible PDF correction, not a confidentiality redaction. Clipped vector
forms may retain non-visible source-page resources. Never use for secret removal.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re
from pathlib import Path
import fitz
from audit_v5_glyphs import lines_of, compare_pages

def has_glyph(page: fitz.Page, target: dict, tolerance: float=.05) -> bool:
    return any(c['c']==target['c'] and abs(c['origin'][0]-target['origin'][0])<=tolerance and abs(c['origin'][1]-target['origin'][1])<=tolerance for line in lines_of(page) for c in line['chars'])

def isolated_source_glyph(src: fitz.Document, page_index: int, glyph: dict) -> int:
    """An explicit font/CID instruction avoids overlapping editorial source text.

    Both Unicode/origin and bounding box of the isolated glyph must match the
    approved original. No font program is written to disk or redistributed.
    Only horizontal, black, unrotated source text is supported by this route.
    """
    instruction = glyph['font_isolation']
    xref = int(instruction['font_xref'])
    cid = str(instruction['cid_hex'])
    if not re.fullmatch(r'[0-9A-Fa-f]{4}', cid):
        raise ValueError('Only explicit two-byte Identity-H CID supported')
    if src.xref_get_key(xref, 'Encoding')[1] != '/Identity-H':
        raise ValueError('Source font must use Identity-H')
    sx, sy = float(instruction['x_font_size']), float(instruction['y_font_size'])
    if not 0 < sx < 200 or not 0 < sy < 200:
        raise ValueError('Invalid source font scale')
    width, height = src[page_index].rect.width, src[page_index].rect.height
    page = src.new_page(width=width, height=height)
    src.xref_set_key(page.xref, 'Resources', f'<< /Font << /Approved {xref} 0 R >> >>')
    x, y = map(float, glyph['origin'])
    stream = (f'q\nBT\n/Approved 1 Tf\n{sx:.10f} 0 0 {sy:.10f} {x:.10f} {height-y:.10f} Tm\n<{cid}> Tj\nET\nQ\n').encode()
    cx = src.get_new_xref(); src.update_object(cx, '<< >>'); src.update_stream(cx, stream); page.set_contents(cx)
    chars = [c for line in lines_of(page) for c in line['chars']]
    if len(chars) != 1 or not has_glyph(page, glyph) or any(abs(a-b) > .05 for a,b in zip(chars[0]['bbox'],glyph['bbox'])):
        raise ValueError('Isolated font/CID glyph differs from approved source')
    return page.number

def restore(source: Path, cleaned: Path, output: Path, spec: dict) -> dict:
    if output.resolve() in (source.resolve(),cleaned.resolve()):raise ValueError('Refusing to overwrite input')
    if output.exists():raise FileExistsError(output)
    a=source.read_bytes();b=cleaned.read_bytes()
    for raw,key in ((a,'source_sha256'),(b,'v5_sha256')):
        if hashlib.sha256(raw).hexdigest()!=spec[key]:raise ValueError(f'{key} mismatch')
    with fitz.open(stream=a,filetype='pdf') as src,fitz.open(stream=b,filetype='pdf') as dst:
        if len(src)!=len(dst):raise ValueError('Page count mismatch')
        regions=[]
        for patch in spec['patches']:
            pi=patch['page']-1
            if src[pi].rect!=dst[pi].rect:raise ValueError('Page geometry mismatch')
            for c in patch['glyphs']:
                if not has_glyph(src[pi],c):raise ValueError('Approved glyph not present in source')
                if has_glyph(dst[pi],c):raise ValueError('Glyph already present; refusing duplicate restoration')
                rect=fitz.Rect(c['bbox']);rect.x0-=.02;rect.x1+=.02;rect.y0-=.1;rect.y1+=.1
                if 'font_isolation' in c:
                    isolated = isolated_source_glyph(src, pi, c)
                    dst[pi].show_pdf_page(dst[pi].rect,src,isolated,overlay=True)
                else:
                    dst[pi].show_pdf_page(rect,src,pi,clip=rect,keep_proportion=False,overlay=True)
                regions.append({'page':pi+1,'char':c['c'],'bbox':list(rect),'origin':c['origin'], 'method':'isolated-source-font-CID' if 'font_isolation' in c else 'source-vector-clip'})
        output.parent.mkdir(exist_ok=True,parents=True)
        # Refuse unexpected neighboring glyphs before publishing the candidate.
        with fitz.open(stream=b,filetype='pdf') as baseline:
            for i in range(len(dst)):
                expected=sum(len(p['glyphs']) for p in spec['patches'] if p['page']==i+1)
                diff=compare_pages(baseline[i],dst[i])
                if diff['removed_position_glyphs'] or diff['added_position_glyphs'] != expected:
                    raise ValueError('Restoration changes unapproved glyphs')
        dst.save(output,garbage=4,deflate=True)
    with fitz.open(output) as out:
        for patch in spec['patches']:
            for c in patch['glyphs']:
                if not has_glyph(out[patch['page']-1],c):raise AssertionError('Restoration did not survive save/reopen')
    return {'id':spec['id'],'output':output.name,'restored_glyphs':len(regions),'regions':regions,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,
            'scope':'approved-visible-glyphs-only; not academic verification; no input overwritten'}

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('cleaned',type=Path);p.add_argument('spec',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(restore(a.source,a.cleaned,a.output,json.loads(a.spec.read_text())),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
