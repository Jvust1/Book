"""Reproducible archive-backed HTTP/TestModel acceptance; no external network.

Requires both review checkouts on PYTHONPATH, the existing hash-locked SDK, and
--r6-root pointing to the verified local r6 archive. Reports contain identities,
counts and fixed error codes, never cookies, private notes or textbook bodies.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
from http.client import HTTPConnection
import json
from pathlib import Path
import socket
import threading
from book_mygpt_selection.contract import Selection, digest
from book_mygpt_selection.host import Application, Server


def run(root: Path) -> dict:
    app = Application(root)
    server = Server(app)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    checks, examples, cookie = [], [], ''
    def call(method, path, value=None, expected=200, headers=None, raw=None):
        base = {'Origin': app.origin, 'Sec-Fetch-Site': 'same-origin', 'X-Book-Companion': '1'}
        if cookie:base['Cookie']=cookie
        if method=='POST':base['Content-Type']='application/json'
        if headers:base.update(headers)
        body=raw if raw is not None else json.dumps(value,ensure_ascii=False).encode() if value is not None else None
        connection=HTTPConnection('127.0.0.1',server.server_port,timeout=10)
        try:
            connection.request(method,path,body=body,headers=base)
            result=connection.getresponse();blob=result.read();status=result.status;out=dict(result.getheaders())
        finally:connection.close()
        assert status==expected,(method,path,status,blob[:200])
        assert out.get('Cache-Control')=='no-store'
        assert 'Access-Control-Allow-Origin' not in out
        checks.append({'method':method,'path':path.split('?')[0],'status':status})
        return (json.loads(blob) if blob and out.get('Content-Type','').startswith('application/json') else blob),out
    try:
        for path in ('/reader/','/reader/reader.js','/companion/bridge.js','/companion/projection.js','/companion/bridge.css','/api/reader/catalog'):
            call('GET',path)
        call('GET','/favicon.ico',expected=204)
        call('GET','/api/companion/status',expected=403)
        call('GET','/reader/../../SECURITY_POLICY.md',expected=404)
        call('POST','/api/reader/state/course/section/learn',{},expected=404)
        call('POST','/api/reader/export',{},expected=404)
        call('OPTIONS','/api/companion/authorize',expected=405)
        call('POST','/api/companion/authorize',{},expected=403,headers={'Origin':'https://untrusted.invalid'})
        call('POST','/api/companion/authorize',{},expected=403,headers={'Host':'localhost:'+str(server.server_port)})
        call('POST','/api/companion/authorize',{},expected=403,headers={'X-Book-Companion':''})
        call('POST','/api/companion/authorize',{},expected=403,headers={'Sec-Fetch-Site':'cross-site'})
        call('POST','/api/companion/authorize',{},expected=415,headers={'Content-Type':'text/plain'})
        call('POST','/api/companion/authorize',expected=413,raw=b' '*8193)
        call('POST','/api/companion/authorize',expected=422,raw=b'{"duplicate":1,"duplicate":2}')
        call('POST','/api/companion/authorize',{'provider':'external'},expected=422)
        data,headers=call('POST','/api/companion/authorize',{})
        assert data['receiver']['responder_invocations']==0
        assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
        cookie=headers['Set-Cookie'].split(';')[0]
        seq=data['session']['last_sequence']
        found={}
        for cid in app.reader.catalog()['courses']:
            manifest=app.reader.manifest(cid)
            for meta in manifest['sections']:
                _,section=app.reader.snapshot(cid,meta['id'])
                base=dict(course_id=cid,book_id=manifest['book_id'],book_version_id=manifest['book_version_id'],section_id=meta['id'],representation='display')
                for record in section['records']:
                    for layer,lid in [('source',None)]+([('completion',record['source_completion']['id'])] if record.get('source_completion') else [])+[('correction',c['id']) for c in record.get('corrections',[]) if c.get('record_id')==record['id']]:
                        if layer in found:continue
                        selection=base|dict(record_id=record['id'],layer=layer,layer_id=lid,portion='body')
                        try:payload=app.reader.project(Selection.parse(selection))
                        except ValueError:continue
                        found[layer]=(selection,digest(payload))
                for group in section.get('practice_groups',[]):
                    if not group.get('derived_guidance'):continue
                    for portion in ('hint','solution'):
                        kind='derived_'+portion
                        if kind in found:continue
                        selection=base|dict(record_id=group['anchor_id'],layer='derived',layer_id=group['id'],portion=portion)
                        try:payload=app.reader.project(Selection.parse(selection))
                        except ValueError:continue
                        found[kind]=(selection,digest(payload))
                if len(found)==5:break
            if len(found)==5:break
        assert len(found)==5,found.keys()
        for number,(kind,(selection,sha)) in enumerate(found.items(),1):
            seq+=1
            ticket,_=call('POST','/api/companion/select',dict(selection=selection,expected_sha256=sha,sequence=seq,request_id='select-'+str(number)))
            result,_=call('POST','/api/companion/explain',dict(ticket=ticket,request_id='explain-'+str(number)))
            assert result['state']=='complete' and result['context']['evidence_kind']=='ARCHIVE_BACKED_READONLY'
            assert result['reply']['backend']=='PYDANTIC_AI_TESTMODEL' and result['paid_provider_calls']==0
            assert not result['reply']['teaching_quality_validated']
            cached,_=call('POST','/api/companion/explain',dict(ticket=ticket,request_id='explain-'+str(number)))
            assert cached==result
            examples.append({'kind':kind,'selection':selection,'source_sha256':sha,'backend':result['reply']['backend']})
        assert app.receiver.responder_invocations==5
        selection,sha=found['source'];seq+=1
        ticket,_=call('POST','/api/companion/select',dict(selection=selection,expected_sha256=sha,sequence=seq,request_id='last-select'))
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='explain-1'),expected=409)
        forged=deepcopy(ticket);forged['mac']='0'*64
        call('POST','/api/companion/explain',dict(ticket=forged,request_id='forged'),expected=409)
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='private',note='do not export'),expected=422)
        call('POST','/api/companion/cancel',dict(request_id='early-cancel'))
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='early-cancel'),expected=409)
        seq+=1
        call('POST','/api/companion/select',dict(selection=selection,expected_sha256='0'*64,sequence=seq,request_id='stale-view'),expected=409)
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='invalidated'),expected=409)
        seq+=1
        ticket,_=call('POST','/api/companion/select',dict(selection=selection,expected_sha256=sha,sequence=seq,request_id='fresh-again'))
        seq+=1;call('POST','/api/companion/clear',dict(sequence=seq,request_id='clear'))
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='cleared'),expected=409)
        call('POST','/api/companion/clear',dict(sequence=seq-1,request_id='old-clear'),expected=409)
        state,_=call('GET','/api/reader/state/'+selection['course_id']+'/'+selection['section_id']+'/learn')
        assert state['readonly_companion_host'] and state['answers']=={} and state['note']==''
        call('GET','/api/reader/section/'+selection['course_id']+'/'+selection['section_id'])
        for extra in ('Host: '+app.host+'\r\n', 'Transfer-Encoding: chunked\r\n'):
            with socket.create_connection(('127.0.0.1',server.server_port),timeout=3) as sock:
                sock.sendall(('GET /reader/ HTTP/1.1\r\nHost: '+app.host+'\r\n'+extra+'\r\n').encode())
                response=sock.recv(1024);assert b' 400 ' in response.split(b'\r\n')[0]
            checks.append({'raw_negative':extra.split(':')[0],'status':400})
        before,_=call('GET','/api/companion/status')
        assert before['unexpected_server_errors']==0 and before['receiver']['responder_invocations']==5
        call('POST','/api/companion/revoke',{})
        call('GET','/api/companion/status',expected=403)
        call('POST','/api/companion/explain',dict(ticket=ticket,request_id='revoked'),expected=403)
        assert app.errors==0
        return {'scope':'archive-backed Book, real loopback HTTP, actual Pydantic AI TestModel; NOT browser/Android acceptance',
                'identity':app.identity,'checks':checks,'checks_passed':len(checks),'examples':examples,
                'receiver':app.receiver.status(),'unexpected_server_errors':app.errors,'bound_address':server.server_address[0],
                'studyrecord_imported':any(x.startswith('app.study') for x in __import__('sys').modules)}
    finally:
        server.shutdown();server.server_close();worker.join(timeout=3)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--r6-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.r6_root);assert result['studyrecord_imported'] is False
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':result['checks_passed'],'actual_testmodel_calls':result['receiver']['responder_invocations'],'paid_calls':0}))
