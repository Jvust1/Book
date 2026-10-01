#!/usr/bin/env python3
"""Source-preserving A4 reflow for an explicit, supported HTML document schema.

Original block HTML, not reader-cleanup replacements, is used. Source prose,
answer provenance, quality limitations and citations are never regex-deleted.
Unsupported HTML and off-root/external assets fail closed.
"""
from __future__ import annotations
import argparse, collections, hashlib, html, json, re, os
from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from weasyprint import HTML, default_url_fetcher
from weasyprint.text.fonts import FontConfiguration

ALLOWED_TAGS={'p','strong','b','em','i','span','div','h1','h2','h3','h4','h5','h6','blockquote','img','br','sup','sub','ul','ol','li','table','thead','tbody','tr','th','td'}
MODE_NAMES={'learn':'学习','preview':'预习','review':'复习','practice':'刷题'}

def nonspace(text: str) -> str:
    return re.sub(r'\s+','',text)

def cjk_counter(text: str) -> collections.Counter:
    return collections.Counter(c for c in text if '\u3400' <= c <= '\u9fff' or '\U00020000'<=c<='\U0003134f')

def asset_path(src: str, root: Path) -> Path:
    parsed=urlparse(src)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError(f'External/qualified asset rejected: {src}')
    rel=unquote(parsed.path).lstrip('/')
    # Absolute references are legacy document-assets URLs, never filesystem paths.
    if not rel.startswith('document-assets/'):
        raise ValueError(f'Asset outside document-assets: {src}')
    path=(root/rel).resolve()
    if not path.is_relative_to((root/'document-assets').resolve()):
        raise ValueError(f'Asset traversal rejected: {src}')
    if not path.is_file():raise FileNotFoundError(path)
    return path

def preserved_blocks(document: dict, asset_root: Path) -> tuple[list[str],dict]:
    if document.get('schema')!='book-reflow-document-v1':raise ValueError('Unsupported source schema')
    parts=[];plain=[];assets=[];ids=[]
    for block in document['blocks']:
        blockid=block.get('id')
        if not isinstance(blockid,str) or blockid in ids:raise ValueError('Missing/duplicate block ID')
        ids.append(blockid)
        fragment=block.get('html')
        if not isinstance(fragment,str):raise ValueError(f'Block has no HTML: {blockid}')
        soup=BeautifulSoup(fragment,'html.parser')
        before=nonspace(soup.get_text())
        for node in soup.find_all(True):
            if node.name not in ALLOWED_TAGS:raise ValueError(f'Unsupported HTML {node.name}')
            if any(str(a).lower().startswith('on') for a in node.attrs):raise ValueError('Executable HTML attribute rejected')
            retained={}
            if node.name=='img':
                path=asset_path(str(node.get('src','')),asset_root)
                assets.append({'src':str(node['src']),'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
                retained={'src':path.as_uri(),'alt':str(node.get('alt',''))}
            elif node.name in ('td','th'):
                for a in ('colspan','rowspan'):
                    if a in node.attrs:
                        value=int(node[a])
                        if not 1<=value<=100:raise ValueError('Invalid table span')
                        retained[a]=str(value)
            node.attrs=retained
        if nonspace(soup.get_text())!=before:raise AssertionError('Sanitizer changed source text')
        text=soup.get_text();plain.append(text)
        parts.append(f'<section class="block kind-{html.escape(str(block.get("kind","prose")))}" id="{html.escape(blockid,quote=True)}">{soup}</section>')
    return parts,{'block_ids':ids,'block_count':len(ids),'plain':'\n'.join(plain),'assets':assets,
                  'reader_visibility_ignored_to_preserve_source':True,
                  'source_html_text_unchanged':True}

def stylesheet(px: int, header: str) -> str:
    if px not in (10,12,15):raise ValueError('Only declared 10/12/15px sizes are supported')
    safe=header.replace('\\','\\\\').replace('"','\\"')
    return f'''@page {{ size: A4; margin: 18mm 18mm 17mm;
      @top-left {{ content: "{safe}"; font: 8px "Noto Sans CJK SC"; color: #555; }}
      @top-right {{ content: "{px}px · v8r2 排版候选"; font: 8px "Noto Sans CJK SC"; color: #555; }}
      @bottom-left {{ content: "历史源稿保全 · 内容待校读 · 非书宋"; font: 8px "Noto Sans CJK SC"; color: #666; }}
      @bottom-right {{ content: counter(page) " / " counter(pages); font: 9px "DejaVu Sans"; color: #555; }}
    }}
    html {{ font-size:{px}px; }}
    body {{ font-family: "Noto Serif CJK SC", "DejaVu Serif", serif; font-size:{px}px; line-height:1.65; color:#191919; margin:0; overflow-wrap:break-word; }}
    h1,h2,h3,h4,h5,h6 {{ font-family:"Noto Sans CJK SC",sans-serif; line-height:1.4; break-after:avoid; font-weight:700; }}
    h1 {{ font-size:1.7em; margin:1em 0 .7em; }} h2 {{ font-size:1.3em; margin:1.25em 0 .5em; }}
    h3,h4,h5,h6 {{ font-size:1.1em; margin:1em 0 .45em; }}
    p {{ margin:0 0 .65em; orphans:3; widows:3; }}
    strong,b {{ font-weight:700; }}
    img {{ max-width:100%; max-height:230mm; width:auto; height:auto; display:block; margin:.7em auto; object-fit:contain; }}
    blockquote {{ margin: .5em 0 .8em 1.2em; padding-left:.8em; border-left:1px solid #aaa; }}
    table {{ border-collapse:collapse; max-width:100%; }} th,td {{ padding:.3em; border:1px solid #ccc; }}
    tr {{ break-inside:avoid; }}
    .cover-title {{ font-size:1.8em; color:#142d43; margin:0 0 .4em; }}
    .notice {{ font-family:"Noto Sans CJK SC",sans-serif; font-size:.92em; line-height:1.55; padding:.6em .8em; background:#f1f3f5; margin:0 0 1.2em; }}
    .body-start {{ margin:0; }}
    '''

def render_one(document_path: Path, asset_root: Path, output: Path, html_output: Path, px: int) -> dict:
    if output.resolve() == document_path.resolve() or html_output.resolve() == document_path.resolve() or output.resolve() == html_output.resolve():
        raise ValueError('Output paths must not overwrite source or each other')
    if output.exists() or html_output.exists():raise FileExistsError('Output already exists; use a new version directory')
    raw=document_path.read_bytes();doc=json.loads(raw)
    parts,meta=preserved_blocks(doc,asset_root)
    label=MODE_NAMES[doc['mode']];title=str(doc['title']).replace('_',' ')
    header=f"{doc['book_title']} · {label}"
    if any(ord(c)<32 for c in header):raise ValueError('Control characters in running header')
    for asset in meta['assets']:
        absolute=Path(asset['path']).as_uri()
        relative=os.path.relpath(asset['path'], html_output.parent.resolve()).replace(os.sep,'/')
        parts=[part.replace(html.escape(absolute,quote=True),html.escape(relative,quote=True)) for part in parts]
    notice='本稿仅验证同源排版，保留历史正文、已有解答标签和原有疑点；OCR 错字及缺漏尚未全部校正，不是内容终审版。'
    if doc['mode']=='practice':notice+=' 所收参考解答沿用原源稿，不是出版社官方答案。'
    content=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{html.escape(header+' '+title)}</title><style>{stylesheet(px,header)}</style></head><body><h1 class="cover-title">{html.escape(title)} · {label}</h1><div class="notice">{notice}</div><main class="body-start">{''.join(parts)}</main></body></html>'''
    html_output.parent.mkdir(parents=True,exist_ok=True);output.parent.mkdir(parents=True,exist_ok=True)
    html_output.write_text(content,encoding='utf-8')
    root=asset_root.resolve()
    def fetcher(url: str):
        parsed=urlparse(url)
        if parsed.scheme!='file':raise ValueError('Network access disabled')
        path=Path(unquote(parsed.path)).resolve()
        if not path.is_relative_to((root/'document-assets').resolve()):raise ValueError('Off-root resource disabled')
        return default_url_fetcher(url)
    HTML(string=content,base_url=html_output.parent.resolve().as_uri()+'/',url_fetcher=fetcher).write_pdf(output,font_config=FontConfiguration(),pdf_tags=True)
    return {'id':doc['id'],'mode':doc['mode'],'book_title':doc['book_title'],'title':doc['title'],'px':px,'pt':px*.75,'source_json_sha256':hashlib.sha256(raw).hexdigest(),
            'pdf':str(output),'html':str(html_output),'pdf_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'block_count':meta['block_count'],'source_text_nonspace_count':len(nonspace(meta['plain'])),
            'source_text_sha256':hashlib.sha256(nonspace(meta['plain']).encode()).hexdigest(),
            'source_CJK_counts':dict(cjk_counter(meta['plain'])),'assets':meta['assets'],
            'source_html_text_unchanged':True,'academic_acceptance':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('document',type=Path);p.add_argument('asset_root',type=Path);p.add_argument('output',type=Path);p.add_argument('--px',type=int,required=True)
    a=p.parse_args();r=render_one(a.document,a.asset_root,a.output,a.output.with_suffix('.html'),a.px)
    print(json.dumps({k:v for k,v in r.items() if k!='source_CJK_counts'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
