from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web';DATA=WEB/'data';OUT=ROOT/'verification'/'projection_integrity.json'
issues=[];stats={'books':0,'records':0,'sections':0,'practice_groups':0,'review_groups':0,'correction_refs':0,'formula_refs':0,'table_refs':0,'visual_table_refs':0,'image_refs':0}

def issue(book,kind,detail): issues.append({'book':book,'kind':kind,'detail':detail})
def exists_url(src):
    return isinstance(src,str) and src.startswith('/') and (WEB/src.lstrip('/')).is_file()

cat=json.loads((DATA/'catalog.json').read_text(encoding='utf-8'))
book_ids=[b['id'] for b in cat['books']]
if len(book_ids)!=len(set(book_ids)): issue('_catalog','duplicate_book_ids',book_ids)
if len(book_ids)!=7: issue('_catalog','book_count',len(book_ids))
if cat.get('app_version')!='1.0.0-rc6-dev': issue('_catalog','app_version',cat.get('app_version'))

for bi in cat['books']:
    bid=bi['id']; stats['books']+=1
    b=json.loads((DATA/f'{bid}.json').read_text(encoding='utf-8'))
    recs=b.get('records',[]); stats['records']+=len(recs)
    byid={r.get('id'):r for r in recs}
    if None in byid: issue(bid,'missing_record_id',True)
    if len(byid)!=len(recs): issue(bid,'duplicate_record_ids',len(recs)-len(byid))
    if len(recs)!=bi.get('record_count'): issue(bid,'catalog_record_count',{'catalog':bi.get('record_count'),'actual':len(recs)})
    correction_ids={str(c.get('id') or c.get('correction_id')) for c in b.get('corrections',[]) if c.get('id') or c.get('correction_id')}
    formula_ids={str(f.get('id')) for f in b.get('formulas',[]) if f.get('id')}
    table_ids=set((b.get('tables') or {}).keys())
    page_max=int(bi.get('pages') or 0)

    for r in recs:
        rid=r.get('id')
        for cid in r.get('correction_ids') or []:
            stats['correction_refs']+=1
            if str(cid) not in correction_ids: issue(bid,'unresolved_correction',{'record':rid,'ref':cid})
        for fid in r.get('formula_refs') or []:
            stats['formula_refs']+=1
            if str(fid) not in formula_ids: issue(bid,'unresolved_formula',{'record':rid,'ref':fid})
        for tref in r.get('table_refs') or []:
            stats['table_refs']+=1
            if not str(tref).lower().endswith('.json'): issue(bid,'non_json_table_ref',{'record':rid,'ref':tref})
            elif tref not in table_ids: issue(bid,'unresolved_table',{'record':rid,'ref':tref})
        vrefs=r.get('visual_table_refs') or []
        if vrefs and not (r.get('images') or r.get('source_image')):
            issue(bid,'visual_table_without_projected_image',{'record':rid,'refs':vrefs})
        for vref in vrefs:
            stats['visual_table_refs']+=1
            if not re.search(r'\.(png|jpe?g|webp|gif|svg)$',str(vref),re.I): issue(bid,'bad_visual_table_ref',{'record':rid,'ref':vref})
        for src in list(r.get('images') or []) + ([r.get('source_image')] if r.get('source_image') else []):
            stats['image_refs']+=1
            if not exists_url(src): issue(bid,'missing_record_image',{'record':rid,'src':src})
        for pg in r.get('source_pdf_pages') or []:
            try: n=int(pg)
            except Exception: issue(bid,'non_numeric_page',{'record':rid,'page':pg}); continue
            if page_max and not 1<=n<=page_max: issue(bid,'page_out_of_range',{'record':rid,'page':n,'max':page_max})

    for pg,pmeta in (b.get('pages') or {}).items():
        try: n=int(pg)
        except Exception: issue(bid,'bad_page_key',pg); continue
        if page_max and not 1<=n<=page_max: issue(bid,'page_map_out_of_range',{'page':n,'max':page_max})
        for src in pmeta.get('images') or []:
            stats['image_refs']+=1
            if not exists_url(src): issue(bid,'missing_page_image',{'page':n,'src':src})

    for tkey,t in (b.get('tables') or {}).items():
        for src in t.get('images') or []:
            stats['image_refs']+=1
            if not exists_url(src): issue(bid,'missing_table_image',{'table':tkey,'src':src})

    sections=b.get('sections') or []; stats['sections']+=len(sections)
    for sec in sections:
        sid=sec.get('id')
        for rid in sec.get('record_ids') or []:
            if rid not in byid: issue(bid,'section_missing_record',{'section':sid,'record':rid})
        for field in ('practice_groups','review_groups'):
            for g in sec.get(field) or []:
                stats[field]+=1
                for rid in g.get('record_ids') or []:
                    if rid not in byid: issue(bid,'group_missing_record',{'section':sid,'group':g.get('id'),'record':rid})

stats['catalog_records']=sum(int(b.get('record_count',0)) for b in cat['books'])
stats['catalog_total_records']=cat.get('total_records')
if stats['records']!=cat.get('total_records'): issue('_catalog','total_records',{'catalog':cat.get('total_records'),'actual':stats['records']})

# r3 release-safety regressions: resolve the old blocking content-review set without
# silently promoting unverified machine text into authoritative facts.
pf=json.loads((DATA/'public_finance_intro_2e_2024.json').read_text(encoding='utf-8'))
pf_by={r['id']:r for r in pf['records']}
image_only=[r for r in pf['records'] if r.get('reading_layer')=='source_image_only_table']
visual=[r for r in pf['records'] if r.get('reading_layer')=='source_visual_transcription']
if len(image_only)!=59: issue('public_finance_intro_2e_2024','r3_image_only_table_count',len(image_only))
if len(visual)<7: issue('public_finance_intro_2e_2024','r3_visual_source_table_count',len(visual))
for r in image_only:
    if r.get('numeric_use_eligible') is not False or r.get('authoritative_for_automated_qa') is not False or '原表图像为权威阅读层' not in (r.get('text') or ''):
        issue('public_finance_intro_2e_2024','r3_unverified_table_exposed',r.get('id'))
fe=json.loads((DATA/'financial-economics-ten-lectures.json').read_text(encoding='utf-8'))
fe_draft=[r for r in fe['records'] if r.get('quality_tier')=='C_MACHINE_DRAFT']
if len(fe_draft)!=3591: issue('financial-economics-ten-lectures','r3_ocr_auxiliary_count',len(fe_draft))
for r in fe_draft:
    if r.get('authoritative_for_automated_qa') is not False or r.get('release_completion_scope')!='AUXILIARY_NONBLOCKING':
        issue('financial-economics-ten-lectures','r3_ocr_authority_leak',r.get('id'))
for bid in ['functional_analysis_2e_jiang_sun','mathematical_physics_equations_4e']:
    o=json.loads((DATA/(bid+'.json')).read_text(encoding='utf-8'))
    if o.get('manifest',{}).get('completion',{}).get('release_source_layer_gate')!='PASS_WITH_DERIVED_EXCLUDED':
        issue(bid,'r3_source_release_gate',o.get('manifest',{}).get('completion',{}))
    if o.get('manifest',{}).get('completion',{}).get('whole_book_mathematical_acceptance') is not False:
        issue(bid,'r3_false_math_truth_claim',True)

media=json.loads((DATA/'media_manifest.json').read_text(encoding='utf-8'))
stats['media_manifest_entries']=len(media) if isinstance(media,list) else len(media.get('files',media))
# Regression assertions for the 16 rc1 projection gaps.
pf_corr={str(c.get('id') or c.get('correction_id')) for c in pf.get('corrections',[]) if c.get('id') or c.get('correction_id')}
required_pf={f'PF-R2-TABLE_{t}-P0{p}' for t in ['3_3','4_1','9_2','10_2','10_3'] for p in [1,2]}
missing=sorted(required_pf-pf_corr)
if missing: issue('public_finance_intro_2e_2024','rc2_missing_source_verified_events',missing)
cce=json.loads((DATA/'contemporary-china-economy.json').read_text(encoding='utf-8'))
for rid in ['contemporary-china-economy_p0213_o00303','contemporary-china-economy_p0213_o00304','contemporary-china-economy_p0213_o00305','contemporary-china-economy_p0213_o00306','contemporary-china-economy_p0213_o00307','contemporary-china-economy_p0213_o00310']:
    r=next((x for x in cce['records'] if x.get('id')==rid),None)
    if not r or not r.get('visual_table_refs') or r.get('table_refs'):
        issue('contemporary-china-economy','rc2_visual_table_normalization',{'record':rid,'visual_table_refs':None if not r else r.get('visual_table_refs'),'table_refs':None if not r else r.get('table_refs')})

out={'schema':'book_projection_integrity_v1','app_version':cat.get('app_version'),'build_id':cat.get('build_id'),'stats':stats,'issues':issues,'passed':0 if issues else 1,'failed':len(issues)}
OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
if issues: raise SystemExit(1)
