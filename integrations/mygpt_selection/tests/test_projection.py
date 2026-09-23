"""Synthetic unit inputs, not copied textbook content."""
import copy
import json
from pathlib import Path
import pytest
from book_mygpt_selection.contract import Selection, BridgeError, project, canonical, digest, FileReader

@pytest.fixture
def inputs():
    m={'course_id':'course','book_id':'book','book_version_id':'book@v1','sections':[{'id':'s'}]}
    r={'id':'r','section_id':'s','kind':'paragraph','title':'Synthetic example','parts':[{'kind':'text','text':'raw','render_text':'display'},{'kind':'math','latex':'x','render_latex':'x^{2}','display':True}]}
    return m, {'id':'s','records':[r], 'practice_groups':[]}

def selector(**changes):
    return Selection.parse(dict(course_id='course',book_id='book',book_version_id='book@v1',section_id='s',record_id='r',layer='source',layer_id=None,portion='body',representation='display',**{}) | changes)

def test_display_is_not_silently_raw(inputs):
    p=project(*inputs,selector())
    assert p['parts']==[{'kind':'text','text':'display'},{'kind':'math','latex':'x^{2}','display':True}]
    raw=project(*inputs,selector(representation='raw'))
    assert digest(raw)!=digest(p)
    assert raw['parent_sources']==p['parent_sources']
    assert 'raw' in canonical(raw).decode()

@pytest.mark.parametrize('field,value',[('note','private'),('answers',{}),('model','paid'),('explicit',True)])
def test_private_or_invented_fields_rejected(field,value):
    with pytest.raises(BridgeError):selector(**{field:value})

@pytest.mark.parametrize('field,value',[('course_id','../private'),('record_id',''),('layer','unknown'),('representation','html'),('portion','solution'),('layer_id','extra')])
def test_invalid_selection_rejected(field,value):
    with pytest.raises(BridgeError):selector(**{field:value})

def test_current_identity_and_duplicate_records_fail_closed(inputs):
    m,s=inputs
    with pytest.raises(BridgeError):project(m,s,selector(book_version_id='book@stale'))
    s['records'].append(copy.deepcopy(s['records'][0]))
    with pytest.raises(BridgeError):project(m,s,selector())

def test_content_is_allowlisted_not_raw_record_dump(inputs):
    m,s=inputs;s['records'][0]['note']='SECRET';s['records'][0]['raw']={'credentials':'SECRET'}
    s['records'][0]['parts'].append({'kind':'image','src':'private.png'})
    p=project(m,s,selector())
    assert 'SECRET' not in canonical(p).decode()
    assert 'private.png' not in canonical(p).decode()
    assert 'NON_TEXT_PARTS_EXCLUDED' in p['warnings']

def test_real_formula_prime_identifier_is_not_a_path(inputs):
    m,s=inputs;s['records'][0]['id']="ch02-eq-2.35'"
    assert project(m,s,selector(record_id="ch02-eq-2.35'"))['selection']['record_id']=="ch02-eq-2.35'"
    with pytest.raises(BridgeError):selector(record_id='../secret')

def add_correction(inputs):
    m,s=inputs;r=s['records'][0]
    c={'id':'correction-1','course_id':'course','section_id':'s','record_id':'r',
       'confidence':'HIGH','presentation':'prefer_corrected','status':'CHECKED_BY_ASSISTANT',
       'evidence_status':'SCOPED_EVIDENCE_CHECKED','source_preserved':True,'check_ids':['test-1'],
       'original_title':r['title'],'original_parts':copy.deepcopy(r['parts']),
       'corrected_parts':[{'kind':'text','text':'AI correction, not official'}]}
    r['corrections']=[c];return c

def test_correction_is_explicit_not_source_and_checks_parent_identity(inputs):
    c=add_correction(inputs)
    p=project(*inputs,selector(layer='correction',layer_id='correction-1'))
    assert p['origin']=='AI_CORRECTION_NOT_TEXTBOOK_NOT_OFFICIAL_ERRATUM'
    assert p['parts'][0]['text'].startswith('AI correction')
    assert project(*inputs,selector())['parts'][0]['text']=='display'
    c['original_parts'][0]['text']='different'
    with pytest.raises(BridgeError):project(*inputs,selector(layer='correction',layer_id='correction-1'))

@pytest.mark.parametrize('field,value',[('confidence','LOW'),('source_preserved',False),('check_ids',[]),('course_id','other'),('section_id','other'),('record_id','other'),('evidence_status','UNVERIFIED'),('original_title','other')])
def test_ineligible_correction_not_exported(inputs,field,value):
    c=add_correction(inputs);c[field]=value
    with pytest.raises(BridgeError):project(*inputs,selector(layer='correction',layer_id='correction-1'))

def test_duplicate_correction_fails_closed(inputs):
    c=add_correction(inputs);inputs[1]['records'][0]['corrections'].append(copy.deepcopy(c))
    with pytest.raises(BridgeError):project(*inputs,selector(layer='correction',layer_id='correction-1'))

def test_completion_is_separate_and_unknown_origin_rejected(inputs):
    c={'id':'completion-1','origin':'source_visual_transcription_not_generated_proof',
       'parts':[{'kind':'text','text':'Completed source transcription'}]}
    inputs[1]['records'][0]['source_completion']=c
    p=project(*inputs,selector(layer='completion',layer_id='completion-1'))
    assert 'SOURCE_COMPLETION' in p['origin']
    c['origin']='untrusted'
    with pytest.raises(BridgeError):project(*inputs,selector(layer='completion',layer_id='completion-1'))

def add_derived(inputs):
    m,s=inputs;m['sections'].append({'id':'supporting-section'})
    g={'id':'group-1','anchor_id':'r','record_ids':['r'],'title':'Synthetic exercise',
       'derived_guidance':{'source_record_ids':['r'],'source_sections':['supporting-section'],
            'textbook_official_solution':False,'hint_parts':[{'kind':'text','text':'A hint'}],
            'solution_parts':[{'kind':'math','latex':'1+1=2','display':True}]}}
    s['practice_groups']=[g];return g

def test_derived_can_reference_another_known_section_but_only_explicit_portion(inputs):
    add_derived(inputs)
    p=project(*inputs,selector(layer='derived',layer_id='group-1',portion='hint'))
    assert p['parts']==[{'kind':'text','text':'A hint'}]
    assert 'AI_DERIVED' in p['origin']
    assert '1+1' not in canonical(p).decode()

@pytest.mark.parametrize('field,value',[('source_record_ids',[]),('source_sections',['missing']),('textbook_official_solution',True)])
def test_derived_rejects_unbound_sources(inputs,field,value):
    g=add_derived(inputs);g['derived_guidance'][field]=value
    with pytest.raises(BridgeError):project(*inputs,selector(layer='derived',layer_id='group-1',portion='hint'))

@pytest.mark.parametrize('body',[
    b'{"key":1,"key":2}',b'{"key":NaN}',b'{"key":Infinity}',b'\xff',b'{',b'[[]'*4000,
])
def test_strict_json_parser(body):
    from book_mygpt_selection.contract import decode
    with pytest.raises(BridgeError):decode(body)

def test_size_and_unicode_bounds(inputs):
    m,s=inputs
    for value in ['x'*12001,'\ud800']:
        s['records'][0]['parts']=[{'kind':'text','text':value}]
        with pytest.raises(BridgeError):project(m,s,selector())
    s['records'][0]['parts']=[{'kind':'text','text':'x'}]*513
    with pytest.raises(BridgeError):project(m,s,selector())

@pytest.fixture
def files(tmp_path,inputs):
    root=tmp_path/'r6';packs=root/'coursepacks';sec=packs/'course'/'sections';sec.mkdir(parents=True)
    (packs/'catalog.json').write_text(json.dumps({'courses':['course']}))
    (packs/'course'/'manifest.json').write_text(json.dumps(inputs[0]))
    (sec/'s.json').write_text(json.dumps(inputs[1]))
    return FileReader(root),sec/'s.json'

def test_file_reader_is_fresh_not_cache(files):
    reader,path=files
    first=reader.project(selector());s=json.loads(path.read_text());s['records'][0]['parts'][0]['render_text']='new';path.write_text(json.dumps(s))
    assert digest(reader.project(selector()))!=digest(first)

@pytest.mark.parametrize('cid,sid',[('../private','s'),('course','../private'),('missing','s'),('course','missing')])
def test_file_reader_never_escapes_or_guesses(files,cid,sid):
    with pytest.raises(BridgeError):files[0].snapshot(cid,sid)

def test_symlink_escape_is_rejected(files,tmp_path):
    reader,path=files;outside=tmp_path/'private.json';outside.write_text(path.read_text());path.unlink();path.symlink_to(outside)
    with pytest.raises(BridgeError):reader.project(selector())

def test_manifest_changed_between_reads_is_rejected(files,monkeypatch):
    reader,_=files;original=reader.manifest;calls=0
    def changing(cid):
        nonlocal calls
        calls+=1;m=original(cid)
        if calls>1:m['book_version_id']='book@v2'
        return m
    monkeypatch.setattr(reader,'manifest',changing)
    with pytest.raises(BridgeError,match='SOURCE_CHANGED_DURING_READ'):reader.project(selector())
