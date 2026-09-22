#!/usr/bin/env python3
"""Lossless, source-anchored draft from Book's readable connector extraction.

This is NOT PDF OCR or visual verification. Hard-coded table / exercise-tail
boundaries were inspected in the supplied text, and are guarded by its SHA-256.
No source spelling, data, mathematical assertion, or extraction order is fixed.
"""
from __future__ import annotations
import argparse
import bisect
import collections
import hashlib
import json
import re
from pathlib import Path

BOOK_ID = 'monetary-finance-3e'
SOURCE_STATUS = 'needs_source_review'
PROVENANCE = dict(content_origin='source', extraction_method='connector_best_effort',
                  review_status=SOURCE_STATUS, status=SOURCE_STATUS,
                  source_pdf_pages=[], uncertain=True,
                  uncertain_reason='仅依据连接器文本抽取；尚未与原始扫描页面核对。')
TABLE_RANGES = {
    '3-1': (2700, 2705), '6-1': (6661, 6670), '7-1': (7093, 7101),
    '7-2': (7446, 7451), '7-3': (7659, 7676), '7-4': (7680, 7706),
    '8-1': (8415, 8422), '10-1': (10826, 10853), '13-1': (12888, 12934),
}
# These are explicit, inspected titles immediately after chapter exercises.
SUPPLEMENT_TITLES = {
    '场景消费金融风险分析', '互联网金融', '2019 年金融市场运行情况',
    '中国现代化支付系统的构成', '货币供给的内生性与外生性',
    '我国的国际储备', '“5G+”让金融更智慧', '巴塞尔协议',
}
# Only one-dimensional expressions with explicit operators are converted.
# Superscripts/subscripts absent from extraction are NEVER reconstructed.
SIMPLE_LATEX = {
    'R=Prn': r'R = P r n',
    'F=P（1+rn）': r'F = P(1+rn)',
    '8%/2=4%': r'\frac{8\%}{2} = 4\%',
    '8%/4=2%': r'\frac{8\%}{4} = 2\%',
    '8%/12=0.667%': r'\frac{8\%}{12} = 0.667\%',
    '利率=利息额/借贷本金额': r'\text{利率} = \frac{\text{利息额}}{\text{借贷本金额}}',
    '实际利率=名义利率−物价上涨率': r'\text{实际利率} = \text{名义利率} - \text{物价上涨率}',
    '存款准备金=商业银行在中央银行的存款+库存现金': r'\text{存款准备金} = \text{商业银行在中央银行的存款} + \text{库存现金}',
    '存款准备金=法定准备金+超额准备金': r'\text{存款准备金} = \text{法定准备金} + \text{超额准备金}',
    '基础货币=流通于银行体系外的现金+商业银行的准备金': r'\text{基础货币} = \text{流通于银行体系外的现金} + \text{商业银行的准备金}',
    'K=1/（r+e）': r'K = \frac{1}{r+e}',
    'K=1/（r+e+c）': r'K = \frac{1}{r+e+c}',
    'm=1/（r+e+c）': r'm = \frac{1}{r+e+c}',
    'R=KY/M': r'R = \frac{K Y}{M}',
    '1/P=KY/M': r'\frac{1}{P} = \frac{K Y}{M}',
    'M=PT/V': r'M = \frac{P T}{V}',
    '贷款−存款=现金': r'\text{贷款} - \text{存款} = \text{现金}',
    '贷款必要量=存款必要量+现金必要量': r'\text{贷款必要量} = \text{存款必要量} + \text{现金必要量}',
    '黄金输送点=铸币平价±输送费用': r'\text{黄金输送点} = \text{铸币平价} \pm \text{输送费用}',
}

def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'))+'\n')

def tidy(s):
    """Remove layout spaces between Chinese characters only for title comparison."""
    return re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', s.strip())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source_bytes = args.input.read_bytes()
    original_text = source_bytes.decode('utf-8')
    raw = original_text.replace('\r\n', '\n')
    digest = hashlib.sha256(source_bytes).hexdigest()
    expected_digest = 'a9a7a6566e5be116278643cdf8ba70403b4138c5b338b9974206541fb7395939'
    if digest != expected_digest:
        raise SystemExit('Source SHA-256 differs: inspected line boundaries must be reviewed.')
    lines = raw.splitlines(keepends=True)
    if len(raw) != 512239 or len(lines) != 14826:
        raise SystemExit('Source version differs: inspected line boundaries must be reviewed.')
    offsets, offset = [], 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)
    crlf_positions, normal_offset = [], 0
    for original_line in original_text.splitlines(keepends=True):
        normalized_line = original_line.replace('\r\n','\n')
        if original_line.endswith('\r\n'):
            crlf_positions.append(normal_offset+len(normalized_line)-1)
        normal_offset += len(normalized_line)
    out = args.output
    for d in ['source', 'chapters', 'blocks', 'tables', 'images', 'qc', 'indexes']:
        (out/d).mkdir(parents=True, exist_ok=True)
    (out/'source'/'connector-readable.txt').write_bytes(source_bytes)
    (out/'source'/'connector-readable-lf.txt').write_text(raw,encoding='utf-8')
    
    toc, toc_sections = [], []
    for i, line in enumerate(lines[:117]):
        m = re.match(r'第\s*(\d+)\s*章\s*(.*?)·+\s*(\d+)', line)
        sm = re.match(r'(\d+\.\d+)\s*(.*?)·+\s*(\d+)', line)
        if m:
            toc.append(dict(chapter_id=f'ch{int(m[1]):02d}', number=int(m[1]),
                            title=tidy(m[2]), toc_printed_page=int(m[3]),
                            toc_source_line=i+1, sections=[]))
        elif sm:
            sec = dict(number=sm[1], title=tidy(sm[2]), toc_printed_page=int(sm[3]),
                       toc_source_line=i+1)
            toc[-1]['sections'].append(sec)
            toc_sections.append(sec)
    assert len(toc) == 14 and len(toc_sections) == 56
    chapters = []
    for i, line in enumerate(lines[117:], 117):
        m = re.fullmatch(r'第\s*(\d+)\s*章\s*(.+?)\s*', line)
        if m:
            n = int(m[1])
            assert tidy(m[2]) == toc[n-1]['title']
            chapters.append(dict(**toc[n-1], source_char_start=offsets[i], source_line_start=i+1))
    assert [c['number'] for c in chapters] == list(range(1, 15))
    appendix_start = raw.rfind('附 418')
    assert appendix_start > chapters[-1]['source_char_start']
    bounds = [c['source_char_start'] for c in chapters]
    for i, ch in enumerate(chapters):
        ch['source_char_end'] = bounds[i+1] if i+1 < len(bounds) else appendix_start

    header_patterns = []
    for ch in chapters:
        title = '[ \\t]*'.join(re.escape(c) for c in ch['title'])
        header_patterns.append(rf'第[ \t]*{ch["number"]}[ \t]*章[ \t]*{title}[ \t]+\d{{1,3}}')
    header_patterns += [r'(?<!\d)\d{1,3}[ \t]+货币金融学',
                        r'附[ \t]+418', r'附[ \t]*录[ \t]+\d{3}',
                        r'目[ \t]*录[ \t]+[ivx]+', r'[ivx]+[ \t]+货币金融学']
    header_rx = re.compile('|'.join(header_patterns))

    def region_at(pos):
        if pos >= appendix_start:
            return 'appendix'
        k = bisect.bisect_right(bounds, pos)-1
        return chapters[k]['chapter_id'] if k >= 0 else 'frontmatter'

    tokens, page_anchors = [], []
    printed, anchor = None, None
    for i, line in enumerate(lines):
        pieces, at = [], 0
        for m in header_rx.finditer(line):
            if m.start() > at:
                pieces.append((at, m.start(), 'text'))
            pieces.append((m.start(), m.end(), 'page_header'))
            at = m.end()
        if at < len(line):
            pieces.append((at, len(line), 'text'))
        for start, end, kind in pieces:
            txt = line[start:end]
            a, b = offsets[i]+start, offsets[i]+end
            ambiguous_header = kind != 'page_header' and bool(re.search(r'\d{4,}[ \t]+货币金融学',txt))
            if ambiguous_header:
                # E.g. 1979322: do not guess which digits belong to body vs page.
                printed, anchor = None, None
            if kind == 'page_header':
                if re.match(r'\d+', txt):
                    printed = int(re.match(r'\d+', txt)[0])
                else:
                    m = re.search(r'(\d+)$', txt)
                    printed = int(m[1]) if m else None
                anchor = f'anchor_{len(page_anchors)+1:04d}'
                page_anchors.append(dict(id=anchor, printed_page=printed,
                    printed_page_roman=(re.search(r'[ivx]+', txt)[0] if printed is None else None),
                    pdf_page=None, source_char_start=a, source_char_end=b,
                    source_line=i+1, text=txt, evidence='explicit_running_header_in_connector_text',
                    **PROVENANCE))
            tok = dict(id=f'raw_{len(tokens)+1:05d}', char_start=a, char_end=b,
                       line_start=i+1, line_end=i+1, raw_text=txt,
                       offset_basis='source/connector-readable-lf.txt; Unicode code points; zero-based half-open',
                       original_char_start=a+bisect.bisect_left(crlf_positions,a),
                       original_char_end=b+bisect.bisect_left(crlf_positions,b),
                       kind=kind if kind == 'page_header' else ('whitespace' if not txt.strip() else 'text'),
                       chapter_id=region_at(a), printed_page=printed,
                       printed_page_anchor_id=anchor,
                       ambiguous_merged_header_digits=ambiguous_header)
            tokens.append(tok)
    assert tokens[0]['char_start'] == 0 and tokens[-1]['char_end'] == len(raw)
    assert all(a['char_end'] == b['char_start'] for a,b in zip(tokens, tokens[1:]))
    assert ''.join(t['raw_text'] for t in tokens) == raw
    jsonl(out/'source'/'raw-spans.jsonl', tokens)
    jsonl(out/'source'/'printed-page-anchors.jsonl', page_anchors)
    
    by_line = collections.defaultdict(list)
    for t in tokens:
        by_line[t['line_start']].append(t)
    table_line_map = {n: key for key,(a,b) in TABLE_RANGES.items() for n in range(a,b+1)}
    table_token_ids = {t['id'] for t in tokens if t['line_start'] in table_line_map
                       and t['kind'] != 'page_header'}
    blocks, active, section, subsection, exercise_mode = [], [], None, None, False
    current_chapter = None
    exercise_number = None
    quality = []

    def make_block(ts, typ, **extra):
        if not ts:
            return
        visible = [t['raw_text'].strip() for t in ts if t['raw_text'].strip()]
        if typ in ('equation_candidate','table','frontmatter','page_header','layout_label','column_marker'):
            text = '\n'.join(visible)
        else:
            text = ''
            for v in visible:
                # Keep word boundaries when an English token wraps across lines.
                sep = ' ' if text and re.search(r'[A-Za-z]$', text) and re.match('[A-Za-z]',v) else ''
                text += sep + v
        b = dict(book_id=BOOK_ID, chapter_id=ts[0]['chapter_id'], section_id=section,
                 subsection_id=subsection, type=typ, title=None, text=text,
                 raw_text=''.join(t['raw_text'] for t in ts), latex=None,
                 image_refs=[], table_refs=[], source_spans=[dict(raw_span_id=t['id'],
                   char_start=t['char_start'], char_end=t['char_end'],
                   line_start=t['line_start'], line_end=t['line_end']) for t in ts],
                 printed_pages=sorted({t['printed_page'] for t in ts if t['printed_page'] is not None}),
                 printed_page_anchor_ids=list(dict.fromkeys(t['printed_page_anchor_id'] for t in ts if t['printed_page_anchor_id'])),
                 normalization='trim_line_edges_and_join_prose_lines; no spelling or data corrections',
                 **PROVENANCE)
        b.update(extra)
        blocks.append(b)
        return b

    def flush():
        nonlocal active, exercise_number
        if active:
            typ = 'exercise' if exercise_number is not None else 'paragraph'
            if typ == 'exercise':
                b = make_block(active, typ, number=str(exercise_number), exercise_group='思考题',
                               sub_questions=[], answer=None, solution=None,
                               answers_in_extraction=None)
                b['question'] = re.sub(r'^\d+\.\s*', '', b['text'])
            else:
                make_block(active,typ)
        active, exercise_number = [], None

    def boundary(typ, t, **extra):
        flush()
        return make_block([t],typ,**extra)

    seen_tables = set()
    for t in tokens:
        s, ch = t['raw_text'].strip(), t['chapter_id']
        if ch != current_chapter:
            flush()
            current_chapter, section, subsection, exercise_mode = ch, None, None, False
        if t['kind'] == 'page_header':
            # Keep page metadata separate while allowing prose / questions to span pages.
            make_block([t], 'page_header', body_visible=False)
            continue
        if ch in ('frontmatter', 'appendix'):
            flush()
            make_block([t], 'frontmatter' if ch == 'frontmatter' else 'appendix_fragment', body_visible=bool(s))
            continue
        if t['id'] in table_token_ids:
            flush()
            key = table_line_map[t['line_start']]
            if key not in seen_tables:
                seen_tables.add(key)
                start,end = TABLE_RANGES[key]
                ts = [x for n in range(start,end+1) for x in by_line[n] if x['kind'] != 'page_header']
                make_block(ts, 'table', title=ts[0]['raw_text'].strip(), table_number=key,
                           table_refs=[f'tables/table-{key}.json'])
            continue
        if not s:
            # Blank physical lines are preserved, without inventing semantic text.
            make_block([t], 'whitespace', body_visible=False)
            continue
        if re.fullmatch(r'第\s*\d+\s*章\s*.+',s):
            exercise_mode=False
            boundary('chapter_title',t,title=tidy(s))
            continue
        m=re.fullmatch(r'(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\s+(.+)',s)
        if m and int(m[1].split('.')[0])==int(ch[2:]) and len(m[2])<65 and not re.search('[。；，]',m[2]) and (m[1].count('.')==2 or m[1] in {x['number'] for x in toc_sections}):
            flush()
            exercise_mode=False
            if m[1].count('.')==1:
                section,subsection=m[1],None
            else:
                subsection=m[1]
            make_block([t], 'section_title' if m[1].count('.')==1 else 'subsection_title',
                       title=tidy(s),number=m[1])
            continue
        if s == '思考题':
            flush();exercise_mode=True;section=None;subsection=None
            make_block([t],'exercise_group',title=s, scope='chapter')
            continue
        if s in SUPPLEMENT_TITLES or re.match(r'^附录\s*\d+\s',s):
            flush();exercise_mode=False;section=None;subsection=None
            make_block([t], 'supplement_title',title=s, scope='chapter')
            continue
        if exercise_mode:
            m=re.match(r'^(\d+)\.\s*',s)
            if m:
                flush();exercise_number=int(m[1]);active=[t]
            else:
                active.append(t)
            continue
        if re.fullmatch(r'专栏\s*\d+-\d+', s):
            # Text extractor often emits a box label after its actual prose.
            boundary('column_marker',t,title=s,number=re.search(r'\d+-\d+',s)[0],
                     column_body_block_ids=[], layout_association_status='unresolved')
            continue
        if s in ('学习目标', '知识点摘要'):
            boundary('layout_label',t,title=s,layout_association_status='unresolved')
            continue
        if re.match(r'^图\s*\d+-\d+\s',s) and len(s)<65 and not re.search('[，。；]',s):
            num=re.search(r'\d+-\d+',s)[0]
            boundary('figure',t,title=s,figure_number=num, original_image_path=None,
                     image_asset_status='missing_original_pdf_access')
            continue
        if s in SIMPLE_LATEX:
            boundary('equation',t,latex=SIMPLE_LATEX[s],original_expression=s,
                     conversion_rule='explicit_single_line_operators_only',mathematical_review_status='not_reviewed')
            continue
        if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', s):
            boundary('note',t)
            continue
        if re.match(r'^资料来源[：:]',s):
            boundary('reference',t)
            continue
        if re.fullmatch(r'[—─－-]{3,}',s):
            boundary('layout_separator',t,body_visible=False)
            continue
        # Unambiguous visible numbering; heading rank remains a draft inference.
        if re.match(r'^\d+[.．]\s*',s) and len(s)<48 and not re.search('[。；？?，]',s):
            boundary('numbered_heading',t,title=s)
            continue
        if re.match(r'^(?:\d+[）)]|[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)',s) and len(s)<50 and not re.search('[。；？?，]',s):
            boundary('minor_heading',t,title=s)
            continue
        is_math = bool(re.search(r'[\ue000-\uf8ff]',s)) or (len(s)<100 and bool(re.search(r'[=＝]',s)))
        is_math = is_math or (len(s)<35 and not re.search(r'[\u4e00-\u9fff]',s) and bool(re.search(r'[A-Za-z0-9+×÷∞∑∫→]',s)))
        if is_math:
            boundary('equation_candidate',t,mathematical_review_status='needs_original_layout')
            continue
        if active and (re.search(r'[。！？?!；;][”’）)]?$',active[-1]['raw_text'].strip()) or
                       re.match(r'^(?:（\d+）|第[一二三四五六七八九十]+[，、])',s)):
            flush()
        active.append(t)
    flush()
    blocks.sort(key=lambda b:b['source_spans'][0]['char_start'])
    chapter_counts=collections.Counter()
    for order,b in enumerate(blocks,1):
        chapter_counts[b['chapter_id']]+=1
        b['id']=f'{BOOK_ID}_{b["chapter_id"]}_{chapter_counts[b["chapter_id"]]:05d}'
        b['order']=order
        if b['type']=='paragraph':
            b['paragraph_boundaries_verified']=False
        if b['type']=='exercise':
            if not re.match(r'^\d+\.',b['text']):
                raise AssertionError('Exercise lacks a source number')
    token_usage=collections.Counter(s['raw_span_id'] for b in blocks for s in b['source_spans'])
    assert token_usage==collections.Counter(t['id'] for t in tokens), 'Raw token omission or duplication'
    jsonl(out/'blocks'/'all.jsonl',blocks)

    # Tables: preserve every raw line, expose columns only where boundaries are explicit.
    table_objects=[]
    for b in [b for b in blocks if b['type']=='table']:
        key=b['table_number']; a,z=TABLE_RANGES[key]
        tlines=[''.join(t['raw_text'] for t in by_line[n] if t['kind']!='page_header').strip() for n in range(a,z+1)]
        obj=dict(id=f'table-{key}',number=key,title=tlines[0],raw_lines=tlines,
                 columns=[], rows=[], cells_complete=False, layout_status='needs_source_review',
                 original_image_path=None,source_block_id=b['id'],source_spans=b['source_spans'],
                 printed_pages=b['printed_pages'], **PROVENANCE)
        if key=='3-1':
            obj['columns']=tlines[1].split()
            obj['rows']=[v.split() for v in tlines[2:]]
            obj['cells_complete']=all(len(r)==2 for r in obj['rows'])
        elif key in ('7-2','7-4'):
            obj['columns']=['货币','1 月','2 月','3 月'] if key=='7-2' else ['项目','2020.01','2020.02','2020.03','2020.04']
            width=len(obj['columns'])-1
            nr=re.compile(r'[−-]?\d+(?: \d{3})*\.\d+')
            for ln in tlines[2:]:
                if ln.startswith('资料来源'): continue
                nums=list(nr.finditer(ln))
                if len(nums)==width:
                    obj['rows'].append([ln[:nums[0].start()].strip()]+[m[0] for m in nums])
                elif not nums:
                    obj['rows'].append([ln]+[None]*width)
                else:
                    obj.setdefault('unresolved_rows',[]).append(ln)
            obj['cells_complete']=not obj.get('unresolved_rows')
            obj['empty_cell_meaning']='null仅表示抽取无数字，不能视为0；需原PDF确认空白单元格。'
            obj['numeric_representation']='source_strings_preserve_grouping_spaces'
        elif key=='8-1':
            obj['columns']=['资产','负债']
            obj['rows']=[['1. 货币准备','6. 现金流通量'],
                         ['2. 对财政的贷款与透支','7. 财政及财政性存款'],
                         ['3. 对金融机构的贷款与贴现','8. 金融机构的存款'],
                         ['4. 有价证券',None],['5. 金银、外汇等储备资产',None],['资产合计','负债合计']]
            obj['cells_complete']=True
            obj['empty_cell_meaning']='null仅表示抽取无对应内容，需原PDF确认。'
        elif key=='10-1':
            obj['columns']=['年份_1','金额_1','年份_2','金额_2','年份_3','金额_3']
            pair_rx=re.compile(r'(19\d{2}|20\d{2})\s+([−-]?\d+(?: \d{3})*\.\d+)')
            obj['records']=[]
            for ln in tlines[2:]:
                if ln=='续表' or ln.startswith('资料来源'):continue
                pairs=list(pair_rx.finditer(ln))
                if not pairs:
                    obj.setdefault('unresolved_rows',[]).append(ln);continue
                row=[]
                for m in pairs:
                    row.extend([m[1],m[2]])
                    obj['records'].append({'year':m[1],'amount_source':m[2]})
                obj['rows'].append(row+[None]*(6-len(row)))
            obj['cells_complete']=not obj.get('unresolved_rows') and len(obj['records'])==70
            obj['unit']='亿美元'
            obj['row_order']='connector_row_order; records not silently resorted'
        table_objects.append(obj)
        dump(out/'tables'/f'table-{key}.json',obj)
    table_lookup={t['source_block_id']:t for t in table_objects}
    
    # Quality queue is localised, carries raw evidence, and does not alter source content.
    def issue(typ,reason,b=None,**extras):
        obj=dict(id=f'qc_{len(quality)+1:05d}',type=typ,reason=reason,status=SOURCE_STATUS,
                 resolution=None, source_pdf_pages=[], content_origin='source',
                 extraction_method='connector_best_effort')
        if b:
            obj.update(block_id=b['id'], chapter_id=b['chapter_id'], printed_pages=b['printed_pages'],
                       source_spans=b['source_spans'],raw_evidence=b['raw_text'])
        obj.update(extras);quality.append(obj)
    issue('source_pdf_unavailable','原PDF下载返回403，未取得页面图像；全部抽取须来源核对，PDF物理页码未建立。')
    issue('appendix_missing_body','全书附录仅剩418–423页的残缺页眉；正文/图表均不可用，不能标记附录完成。',
          printed_pages=list(range(418,424)),source_char_start=appendix_start,source_char_end=len(raw))
    for b in blocks:
        if b['type']=='figure':
            issue('missing_original_figure','仅保留图题，原图未提取，图内数据/轴标/布局尚不可核。',b)
        if b['type']=='table':
            tb=table_lookup[b['id']]
            issue('table_layout_review','须与原表核对行列、合并单元格、符号和数值；原图未获取。',b,
                  cells_parsed=tb['cells_complete'])
        if b['type']=='equation_candidate':
            issue('formula_or_layout_candidate','公式/图内标签/表格片段候选：字符或版式不足以可靠重建LaTeX，原文保留。',b)
        if b['type']=='equation':
            issue('latex_source_review','仅按显式一维运算符转换；仍须确认扫描原文与数学正确性。',b)
        if re.search(r'[\ue000-\uf8ff\ufffd]', b['raw_text']):
            issue('unmapped_or_replacement_glyph','存在字体私用区字符或替代字符，不能凭上下文猜写。',b)
        if b['type'] in ('column_marker','layout_label'):
            issue('floating_layout_label','连接器将侧栏/学习标签与正文顺序混排；保留原顺序，标签与内容关联未确认。',b)
        if re.search(r'\d{4,}[ \t]+货币金融学',b['raw_text']):
            issue('merged_page_header_digits','正文数字与页眉数字相连，不能可靠分割，保留原串并暂停后续印刷页归属直到下一明确页眉。',b)
    # Visible mathematical conflicts are raised as checks, never corrected in source.
    for fragment,reason in [
        ('10÷100×100%=20%', '同句称准备率10%，但括号算式等号右侧20%疑冲突；确认教材原印/抽取错误后另存correction层。'),
        ('货币乘数 m=（C+R）÷（C +D）','货币乘数表达式与相邻定义可能冲突，需核原式及符号上下标。'),
        ('明，内生变量决定外生变量','内生/外生变量表述可能自相矛盾；先核教材原文。'),
    ]:
        hits=[b for b in blocks if fragment in b['raw_text'] or fragment in b['text']]
        for b in hits:issue('source_mathematical_or_logical_conflict',reason,b)
    jsonl(out/'qc'/'uncertain.jsonl',quality)

    # Searchable semantic indexes; no AI learning material is added.
    for typ,name in [('exercise','exercises'),('figure','figures'),('column_marker','columns'),('equation','equations')]:
        jsonl(out/'indexes'/f'{name}.jsonl',[b for b in blocks if b['type']==typ])
    jsonl(out/'indexes'/'formula-candidates.jsonl',[b for b in blocks if b['type']=='equation_candidate'])
    sections=[b for b in blocks if b['type'] in ('section_title','subsection_title')]
    jsonl(out/'indexes'/'headings.jsonl',[b for b in blocks if b.get('title')])
    matched_sections={b.get('number') for b in sections if b['type']=='section_title'}
    section_report=[]
    for sec in toc_sections:
        hits=[b for b in sections if b.get('number')==sec['number']]
        section_report.append(dict(**sec,body_block_ids=[b['id'] for b in hits],
                                   body_heading_present=len(hits)==1))
    dump(out/'qc'/'toc-coverage.json',dict(toc_chapters=14,body_chapters=len(chapters),
         toc_sections=56,body_sections=len(matched_sections),sections=section_report,
         status='source_text_structure_checked_not_pdf_verified'))

    by_chapter=collections.defaultdict(list)
    for b in blocks:by_chapter[b['chapter_id']].append(b)
    for region,bs in by_chapter.items():
        jsonl(out/'blocks'/f'{region}.jsonl',bs)
        md=['<!-- content_origin: source; extraction_method: connector_best_effort; status: needs_source_review; source_pdf_pages: [] -->',
            '> 连接器文本结构化初稿，未与原始扫描页核对。原文字符完整另存，公式/图表/版式疑点见 qc；本章不标记完成。','']
        if region=='appendix':
            md+=['# 附录（抽取内容缺失）','', '> 已见 418–423 页残缺页眉，无可用附录正文，需取回原 PDF 补录。','']
        elif region=='frontmatter':md+=['# 封面、出版信息与目录（原抽取顺序）','']
        for b in bs:
            if b.get('body_visible') is False or b['type'] in ('whitespace','page_header','layout_separator'):continue
            typ=b['type'];text=b['text']
            span=b['source_spans']
            md.append(f'<!-- {b["id"]}; raw_chars: {span[0]["char_start"]}-{span[-1]["char_end"]}; lines: {span[0]["line_start"]}-{span[-1]["line_end"]}; printed_pages: {b["printed_pages"]} -->')
            if typ=='chapter_title':md.append('# '+b['title'])
            elif typ in ('section_title','exercise_group','supplement_title'):md.append('## '+(b['title'] or text))
            elif typ in ('subsection_title','numbered_heading'):md.append('### '+(b['title'] or text))
            elif typ=='minor_heading':md.append('#### '+text)
            elif typ=='exercise':md.append(f'### 思考题 {b["number"]}\n\n'+b['question'])
            elif typ=='equation':md.append('\\[\n'+b['latex']+'\n\\]\n\n<details><summary>抽取原文（待核对）</summary>\n\n```text\n'+b['raw_text'].strip()+'\n```\n</details>')
            elif typ=='equation_candidate':md.append('```text\n'+text+'\n```\n\n> 待核对：公式或版式片段，暂不猜写 LaTeX。')
            elif typ=='figure':md.append('**'+text+'**\n\n> 原书图片待提取；本处保留图题及来源锚点。')
            elif typ=='table':
                tb=table_lookup[b['id']]
                md.append('**'+tb['title']+'**')
                if tb['cells_complete']:
                    md.append('\n| '+' | '.join(tb['columns'])+' |\n| '+' | '.join(['---']*len(tb['columns']))+' |')
                    md.extend('| '+' | '.join('' if v is None else str(v).replace('|','\\|') for v in row)+' |' for row in tb['rows'])
                    md.append('\n> 表格基于抽取文字恢复，空单元格与数字须回原表确认。')
                    md.append('\n<details><summary>表格抽取原行（含注释与资料来源，待核对）</summary>\n\n```text\n'+'\n'.join(tb['raw_lines'][1:])+'\n```\n</details>')
                else:md.append('\n```text\n'+'\n'.join(tb['raw_lines'][1:])+'\n```\n\n> 行列/合并单元格待核对，暂保留原行。')
            elif typ in ('column_marker','layout_label'):md.append('**'+text+'**\n\n> 原抽取位置；标签对应的正文边界尚未确认。')
            else:md.append(text)
            md.append('')
        (out/'chapters'/f'{region}.md').write_text('\n'.join(md),encoding='utf-8')
    stats=collections.Counter(b['type'] for b in blocks)
    for ch in chapters:
        bs=by_chapter[ch['chapter_id']]
        ch.update(block_count=len(bs),exercise_count=sum(b['type']=='exercise' for b in bs),
                  markdown=f'chapters/{ch["chapter_id"]}.md',blocks=f'blocks/{ch["chapter_id"]}.jsonl',
                  status=SOURCE_STATUS,whole_chapter_complete=False,
                  printed_pages=sorted({p for b in bs if b.get('body_visible') is not False and b['type'] not in ('page_header','whitespace','layout_separator') for p in b['printed_pages']}),
                  source_pdf_pages=[])
    dump(out/'toc.json',dict(book_id=BOOK_ID,chapters=chapters,appendix=dict(
        title='附录',toc_printed_page=418,observed_header_pages=list(range(418,424)),
        body_present=False,status=SOURCE_STATUS),**PROVENANCE))
    exercise_counts={ch['chapter_id']:ch['exercise_count'] for ch in chapters}
    covered_pages=sorted({p['printed_page'] for p in page_anchors if p['printed_page'] is not None})
    missing_headers=[p for p in range(1,424) if p not in covered_pages]
    dump(out/'qc'/'missing-pages.json',dict(source_pdf_page_count=None,source_pdf_pages_checked=[],
         source_pdf_page_mapping_complete=False,observed_printed_headers=covered_pages,
         printed_header_numbers_not_observed=missing_headers,
         note='无缺号仅证明连接器有页眉标记，不证明每页正文/图表完整。',
         appendix_body_missing_printed_pages=list(range(418,424))))
    validation=dict(source_sha256=digest,raw_character_count=len(original_text),normalized_character_count=len(raw),raw_byte_count=len(source_bytes),
        raw_line_count=len(lines),raw_span_count=len(tokens),raw_span_contiguous=True,
        normalized_roundtrip_equal=True,original_bytes_preserved=True,
        original_newline_form='LF' if not crlf_positions else 'CRLF',
        raw_roundtrip_equal=(raw.encode('utf-8')==source_bytes),semantic_token_coverage_exactly_once=True,
        chapters_14_present=len(chapters)==14,sections_56_present=len(matched_sections)==56,
        exercise_group_count=stats['exercise_group'],exercise_count=stats['exercise'],
        exercises_by_chapter=exercise_counts,figure_count=stats['figure'],table_count=stats['table'],
        table_cells_parsed_count=sum(t['cells_complete'] for t in table_objects),
        column_marker_count=stats['column_marker'],latex_equation_count=stats['equation'],
        formula_candidate_count=stats['equation_candidate'],block_count=len(blocks),
        block_type_counts=dict(stats),qc_issue_count=len(quality),
        whole_book_complete=False,full_page_visual_verification=False,
        structured_review_complete=False,
        mechanical_structure_checks_complete=True,
        targeted_pdf_issues_resolved=False,mathematical_review_status='unreviewed_with_flagged_conflicts')
    dump(out/'qc'/'validation.json',validation)
    manifest=dict(schema_version='book-connector-draft-1.0',book_id=BOOK_ID,title='货币金融学',edition='第3版',
        authors=['张红伟（主编）','邓奇志（副主编）'],publisher='科学出版社',publication_date='2021-10',
        isbn='978-7-03-069842-1',language='zh-CN',source_type='connector_readable_text_of_pdf',
        pdf_source_layout_status='unverified',
        source_file='source/connector-readable.txt',original_pdf_file=None,pdf_page_count=None,
        source_sha256=digest,source_character_count=len(original_text),normalized_character_count=len(raw),source_line_count=len(lines),
        normalized_source_file='source/connector-readable-lf.txt',
        source_span_offset_basis='normalized LF text, Unicode code points, zero-based half-open',
        newline_normalization='CRLF to LF only; original bytes preserved separately',
        printed_page_offset=None,source_pdf_pages=[],
        chapters=chapters,content_origin='source',extraction_method='connector_best_effort',
        status=SOURCE_STATUS,whole_book_complete=False,extracted_text_preservation_complete=True,
        extracted_text_partition_complete=True,mechanical_structure_checks_complete=True,
        structured_review_complete=False,targeted_pdf_issues_resolved=False,
        full_page_visual_verification=False,mathematical_review_status='not_completed',
        original_figures_complete=False,appendix_complete=False,
        counts=dict(stats),text_normalization='raw unchanged; derived prose line joins are tentative',
        unresolved_limitations=['原PDF下载403；物理页码未知','附录418–423无正文',
            '原图未取得；图内内容未恢复','复杂公式/表格/浮动专栏标签需版式证据',
            '全部抽取需要来源核对，页眉连续不代表整书完整'],
        provenance_layers={'source':'本目录仅为原书连接器抽取及可追溯格式化','correction':None,'ai_generated':None})
    dump(out/'manifest.json',manifest)
    report=f'''# 《货币金融学》第3版结构化初稿质检报告

本批次保全连接器返回的全部 {len(raw):,} 个 Unicode 字符（{len(source_bytes):,} 字节）、{len(lines):,} 行。**这不是全书完成稿**：原 PDF 下载受阻，正文/图片/公式未经扫描页面验真，附录缺少正文。

## 当前成果

- 14 章、目录 56 节均在主体定位；每章独立 Markdown、JSONL，并保留封面/出版信息/目录/末尾附录残片。
- {len(blocks):,} 个带来源字符区间、行号、印刷页眉锚点的内容块。
- {stats['exercise_group']} 个思考题组，{stats['exercise']} 道逐题记录；答案、解析均为 null，没有编造答案。
- {stats['figure']} 个图题、{stats['table']} 个编号表、{stats['column_marker']} 个专栏标签索引。
- {sum(t['cells_complete'] for t in table_objects)} 个表可按文字中明确边界恢复行列；其余保留原行，全部待原表核验。
- {stats['equation']} 个一维显式表达式转为 LaTeX，同时保留原表达；{stats['equation_candidate']} 个公式/版式候选进入待核队列。
- QC 队列 {len(quality)} 项，记录原文、字符区间和块号。原图没有获取，未生成替代图片。

## 忠实性与可追溯性

`source/connector-readable.txt` 按输入字节复制；`source/connector-readable-lf.txt` 是只作 CRLF→LF 的规范化文本，本次输入本身为 LF，因此两文件字节相同。`source/raw-spans.jsonl` 连续分区覆盖 LF 文本每一个字符，无空隙、无重叠。所有 raw span 恰好由一个结构块引用，能完全重建 LF 文本。`char_start/end` 以 LF 文本的 Unicode 码点计数；`original_char_start/end` 以原字节文件解码后的 Unicode 码点计数，两者都不是字节偏移或 JavaScript UTF-16 偏移。

正文只合并可能因排版产生的换行，不做错字、数字、符号修订。由于连接器无段落版式，段落边界仍是初稿推断。页眉独立保留为元数据，跨页题目/段落可引用不连续 raw span。专栏与“学习目标/知识点摘要”标签常被抽取在其正文之后，故不擅自重排或猜测归属。

来源印刷页只来自可见页眉；PDF 物理页全部留空。`toc_printed_page` 是目录印刷页引用，和正文实见页眉分字段保存。页眉覆盖不能证明页面正文完整。

## 明确缺失和风险

1. 原 PDF 未取得，无法建立物理页到印刷页映射、裁切原图或确认公式上下标/分式。
2. 全书附录印刷 418–423 页只有残缺页眉，没有可用正文；不视作空白原书页面。
3. 字体私用区符号、断裂公式、复杂表格/图内标签都保留原串，未凭上下文猜写。
4. 部分货币乘数和百分比算式及内生/外生变量表述有可见冲突，已入 QC，未静默修正原书。
5. 侧栏、学习目标和知识点标签存在抽取顺序混排，尚待视觉核验。

## 检查状态

`mechanical_structure_checks_complete=true`；`structured_review_complete=false`；`targeted_pdf_issues_resolved=false`；`full_page_visual_verification=false`；`whole_book_complete=false`。所有来源衍生块状态均为 `needs_source_review`。

## 下次执行

取得同版完整 PDF 后，先验证封面/版权页身份及页数，建立页码映射。按 QC 清单优先回查损坏公式、图表、空附录和侧栏边界，再完成逐页首次录入检查。不要把这一初稿覆盖为已验收数据，不要生成教材原文之外的补写内容。

输入 SHA-256：`{digest}`。
'''
    (out/'qc'/'extraction-report.md').write_text(report,encoding='utf-8')
    (out/'README.md').write_text('# 货币金融学（第3版）连接器文本结构化初稿\n\n'+
        '状态：`needs_source_review`，`whole_book_complete=false`。\n\n'+
        '从 [目录](toc.json)、[各章正文](chapters/)、[质检报告](qc/extraction-report.md) 开始。'+
        '原文位于 `source/connector-readable.txt`，全部内容块位于 `blocks/all.jsonl`。'+
        '索引包含逐题思考题、图题、专栏标记、LaTeX表达与待核公式；表格单独保存在 `tables/`。\n\n'+
        '字符位置引用 `source/connector-readable-lf.txt`，为 Unicode 码点、从0开始的半开区间 `[char_start,char_end)`；行号从1开始。原文件 bytes 另存且保持不变。'+
        'PDF物理页尚未知，印刷页来自明确页眉。未获取原图。章后补充正文和附录残片已保留。\n',encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
