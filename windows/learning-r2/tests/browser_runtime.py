"""UI exercise harness. Chromium policy is unchanged.
The managed browser blocks loopback navigation. This bridge runs local packaged
JS/CSS in a Chromium DOM while forwarding fetch to the actual Go HTTP backend.
It does NOT constitute Windows Edge launch, CSP navigation or OS dialog testing.
"""
from pathlib import Path
import json, re, base64, urllib.request, urllib.error, os
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web'
BASE=os.environ.get('BOOK_TEST_BASE','http://127.0.0.1:8877')
def api(path,method='GET',payload=None,headers=None):
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode() if payload is not None else None
    hs={'Origin':BASE};hs.update(headers or {})
    if payload is not None:hs.setdefault('Content-Type','application/json')
    r=urllib.request.Request(BASE+path,data=data,method=method,headers=hs)
    try:resp=urllib.request.urlopen(r,timeout=40)
    except urllib.error.HTTPError as e:resp=e
    raw=resp.read()
    try:b=json.loads(raw)
    except:b=raw
    return resp.status,b,dict(resp.headers)
def backend(url,opt=None):
    opt=opt or {};path=url.removeprefix(BASE)
    if not path.startswith('/') or path.startswith('//') or '\\' in path:raise ValueError('local-only test bridge')
    hs={'Origin':BASE};hs.update(opt.get('headers') or {})
    data=opt.get('body');data=data.encode() if isinstance(data,str) else data
    r=urllib.request.Request(BASE+path,data=data,headers=hs,method=opt.get('method','GET'))
    try:resp=urllib.request.urlopen(r,timeout=40)
    except urllib.error.HTTPError as e:resp=e
    return {'status':resp.status,'body':base64.b64encode(resp.read()).decode(),'headers':dict(resp.headers)}
def webtext(name):
    if os.environ.get('BOOK_TEST_PACKAGED')=='1':
        r=backend('/'+name)
        if r['status']!=200:raise RuntimeError('Packaged resource missing: '+name)
        return base64.b64decode(r['body']).decode('utf-8')
    return (WEB/name).read_text()
def inject(page,images=False):
    page.goto('about:blank')
    page.expose_function('__testBackend',backend)
    html=re.sub(r'<script\b[^>]*>.*?</script>','',webtext('index.html'),flags=re.S)
    html=re.sub(r'<link\b[^>]*>','',html)
    page.set_content(html)
    page.add_style_tag(content=webtext('app.css'))
    page.add_script_tag(content='''window.__failWrites=0;window.fetch=async(url,opt={})=>{
      if(String(url)==='/api/state'&&opt.method==='POST'&&window.__failWrites>0){window.__failWrites--;return new Response(JSON.stringify({error:'SIMULATED_STORAGE_FAILURE'}),{status:503,headers:{'Content-Type':'application/json'}})}
      const r=await window.__testBackend(String(url),opt);return new Response(Uint8Array.from(atob(r.body),c=>c.charCodeAt(0)),{status:r.status,headers:r.headers})};''')
    if images:
        page.add_script_tag(content='''const fix=()=>document.querySelectorAll('img[src^="/"]').forEach(async i=>{if(i.dataset.bridge)return;i.dataset.bridge='1';const u=i.getAttribute('src');i.removeAttribute('src');const r=await __testBackend(u,{});i.src='data:'+(r.headers['Content-Type']||'image/png')+';base64,'+r.body});new MutationObserver(fix).observe(document.body,{childList:true,subtree:true});''')
    for name in ['config.js','vendor/tex-svg.js','study-engine.js','exam-engine.js','app.js','study-ui.js','teaching-ui.js','learning-ui.js']:
        page.add_script_tag(content=webtext(name))
    page.wait_for_selector('.bookcard',timeout=25000)
if __name__=='__main__':
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
        inject(page,True);print('BOOKS',page.locator('.bookcard').count(),'ERRORS',errs)
        page.screenshot(path=str(ROOT/'verification/windows_shelf.png'))
        page.locator('.bookcard button').first.click();page.wait_for_selector('.reader');page.locator('.modes [data-mode=preview]').click();page.wait_for_selector('#preview-note');print('PREVIEW',page.locator('h1').inner_text(),'ERRORS',errs)
        page.screenshot(path=str(ROOT/'verification/windows_preview.png'))
        page.locator('.modes [data-mode=practice]').click();page.wait_for_selector('.study-hub');page.locator('[data-action=study-scope][data-value=all]').click();page.wait_for_selector('[data-action=study-one]');page.locator('[data-action=study-one]').first.click();page.wait_for_selector('#session-answer');print('SESSION',page.locator('.session-top').inner_text(),'ERRORS',errs)
        page.screenshot(path=str(ROOT/'verification/windows_practice.png'));b.close()
