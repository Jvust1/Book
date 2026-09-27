#!/usr/bin/env python3
"""Source-bound chapter knowledge trees and independently versioned worked answers.
No edits to source/study JSON. A record's original quality remains authoritative.
"""
import hashlib,json,re
from collections import Counter
from pathlib import Path
from build_teaching import CATEGORIES,DROP,text,write_changed
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'web/data'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def chapter_for(record):
    c=record.get('chapter_id')
    if c:
        m=re.fullmatch(r'chapter_(\d+)',str(c))
        return 'ch'+m.group(1).zfill(2) if m else str(c)
    # Use explicit structured source IDs only; never infer a chapter from PDF page numbers.
    for obj in [record,record.get('source_anchor') or {}]:
        for key in ['chapter','chapter_number']:
            if obj.get(key):return str(obj[key])
    rid=record.get('id','')
    m=re.search(r'(?:^|_)ch(\d+)_',rid)
    if m:return 'ch'+m.group(1).zfill(2)
    sid=record.get('section_id') or ''
    m=re.match(r'^(\d+)\.',sid)
    if m:return 'lecture-'+m.group(1)
    return 'unmapped'
def chapter_title(c):
    if re.fullmatch(r'ch\d+',c):return '第'+str(int(c[2:]))+'章'
    if c.startswith('lecture-'):return '第'+c[8:]+'讲'
    return {'unmapped':'目录归属待核对','extras':'附属资料','frontmatter':'前置页','intro':'导论','appendix':'附录','backmatter':'附属资料','references':'参考文献','publisher':'出版信息','back_cover':'封底','afterword':'后记','name_translation':'人名译名'}.get(c,c)
def compile_book(meta):
    bid=meta['id'];book=json.loads((DATA/(bid+'.json')).read_text());teaching=json.loads((DATA/(bid+'.teaching.json')).read_text());study=json.loads((DATA/(bid+'.study.json')).read_text())
    by={r['id']:r for r in book['records']};chapters={};sections=[];section_chapters={}
    titles={c['id']:c.get('title',c['id']) for c in book['manifest'].get('chapters',[]) if isinstance(c,dict)}
    for r in book['records']:
        if r.get('type') in {'chapter','chapter_title','chapter_opening'}:
            titles.setdefault(chapter_for(r),r.get('title') or text(r)[:100])
    for s in book['sections']:
        rr=[by[i] for i in s.get('record_ids',[]) if i in by]
        cs=list(dict.fromkeys(chapter_for(r) for r in rr)) or ['unmapped']
        section_chapters[s['id']]=cs
        categories={}
        for r in rr:
            if r.get('body_visible') is False or r.get('type') in DROP or r.get('type') in {'exercise','exercise_group','problem','question'}:continue
            if not text(r).strip() and not r.get('images'):continue
            categories.setdefault(CATEGORIES.get(r.get('type'),'知识论述与补充'),[]).append(r['id'])
        units=[u['id'] for u in teaching['units'] if s['id'] in u['sections']]
        node={'id':s['id'],'title':s['title'],'chapter_ids':cs,'categories':categories,'unit_ids':units,'record_count':sum(map(len,categories.values())),
              'status':'authored_and_source' if units else 'source_tree' if categories else 'source_locator_only'}
        sections.append(node)
        for c in cs:
            chapters.setdefault(c,{'id':c,'title':titles.get(c,chapter_title(c)),'section_ids':[]})['section_ids'].append(s['id'])
    originals_path=ROOT/'content/learning'/(bid+'.answers.json')
    annotations=json.loads(originals_path.read_text()) if originals_path.exists() else []
    questions={q['id']:q for q in study['questions']};answer_map={}
    for a in annotations:
        q=questions[a['question_id']]
        if a['question_id'] in answer_map:raise ValueError('Duplicate answer')
        if not a.get('answer') or len(a.get('steps',[]))<2 or not a.get('method'):raise ValueError('Incomplete answer')
        refs=[{'record_id':rid,'pdf_pages':by[rid].get('source_pdf_pages',[]),'quality_tier':by[rid].get('quality_tier','INDEX_OR_LEGACY')} for rid in q['record_ids']]
        answer_map[a['question_id']]={**a,'origin':'AI_REFERENCE_FOR_ORIGINAL_QUESTION','textbook_official_solution':False,'independent_expert_review':False,'source_refs':refs}
    question_chapters={q['id']:list(dict.fromkeys(c for sid in (q.get('section_ids') or [q['section']]) for c in section_chapters.get(sid,['unmapped']))) for q in study['questions']+teaching['solved']}
    return {'schema':'book-learning-sidecar-v1','book_id':bid,'source_book_sha256':sha(DATA/(bid+'.json')),'chapters':list(chapters.values()),'sections':sections,'original_answers':answer_map,'question_chapters':question_chapters,
            'coverage':{'directory_entries':len(sections),'tree_nodes_with_records':sum(bool(x['record_count']) for x in sections),'authored_entries':sum(bool(x['unit_ids']) for x in sections),'original_answers':len(answer_map),'whole_book_authored_complete':False,'exam_frequency_evidence_count':0},
            'boundary':'Trees organize existing source records, not independently accepted exam syllabi. Unmapped chapter identities stay explicit. Exam emphasis is a suggestion, never historical frequency.'}
def main():
    summary=[]
    for meta in json.loads((DATA/'catalog.json').read_text())['books']:
        obj=compile_book(meta);write_changed(DATA/(meta['id']+'.learning.json'),obj);summary.append({'book_id':meta['id'],**obj['coverage']})
    write_changed(ROOT/'verification/learning_compilation.json',{'books':summary,'directory_entries':sum(x['directory_entries'] for x in summary),'original_answers':sum(x['original_answers'] for x in summary)})
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
