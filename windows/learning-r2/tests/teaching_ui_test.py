"""RC5 actual learning UI tests with the existing Chromium/native-backend bridge.
Cannot certify Windows OS launch or direct-loopback navigation in this runtime.
"""
import json
from playwright.sync_api import sync_playwright
from browser_runtime import ROOT,api,inject
OUT=ROOT/'verification';checks=[]
def check(name,value,detail=None):
 checks.append({'check':name,'passed':bool(value),'detail':detail})
 (OUT/'teaching_ui_tests.json').write_text(json.dumps({'method':'Chromium DOM + exact packaged JS/CSS/JSON + Linux Go HTTP service, test transport bridge','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks)},ensure_ascii=False,indent=2))
 print(('PASS' if value else 'FAIL'),name,flush=True)
 assert value,(name,detail)
sess=api('/api/session')[1];blank={'schema':'book-personal-state-v1','settings':{'fontSize':20,'fontFamily':'song','lineHeight':1.85,'theme':'light'},'books':{},'notes':{},'bookmarks':{},'cards':{}}
assert api('/api/state','POST',{'state':blank,'expected_revision':sess['revision']},{'X-Book-Token':sess['token']})[0]==200
PDE='mathematical_physics_equations_4e'
def click(p,s):p.locator(s).first.click();p.wait_for_timeout(100)
def flush(p):p.evaluate('async()=>{await __bookTest.flushStudy();await __bookTest.state.saveQueue}')
def route(p,book,section,mode):
 flush(p);p.evaluate('r=>__bookTest.routeTo(r)',{'view':'reader','book':book,'section':section,'mode':mode})
 p.wait_for_function('([b,s,m])=>__bookTest.state.currentBook?.book_id===b && __bookTest.state.currentSection?.id===s && __bookTest.state.route.mode===m && !!document.querySelector(".reader")',arg=[book,section,mode]);p.wait_for_timeout(60)
with sync_playwright() as w:
 browser=w.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));inject(page,True)
 route(page,PDE,'ch01_s02','preview')
 check('Preview has actual explanation',len(page.locator('.preview-explanation').inner_text())>100 and '达朗贝尔' in page.locator('.preview-explanation').inner_text())
 check('Preview has learning goals and prerequisites',page.locator('.teaching-grid li').count()>=4)
 check('Preview retains personal note and checklist',page.locator('#preview-note').count()==1 and page.locator('[data-preview-check]').count()==4)
 page.screenshot(path=str(OUT/'rc5-preview.png'),full_page=False)
 click(page,'[data-action=study-knowledge]');page.wait_for_selector('.teaching-hub')
 check('Review opens knowledge rather than recall queue',page.locator('.knowledge-point').count()>=3 and page.locator('#session-answer').count()==0)
 check('Review contains conditions methods and pitfalls','遇到题目怎样下手' in page.locator('.reader').inner_text() and '易错点与适用边界' in page.locator('.reader').inner_text())
 page.screenshot(path=str(OUT/'rc5-review.png'),full_page=False)
 page.locator('#knowledge-category').select_option('公式与关系');page.wait_for_timeout(100)
 check('Source knowledge category filtering',page.locator('.source-knowledge').count()>0 and all('公式与关系' in x for x in page.locator('.source-knowledge>summary').all_inner_texts()))
 click(page,'[data-action=study-unit-practice][data-unit=pde-dalembert]');page.wait_for_selector('#session-answer')
 check('Topic practice starts with actual stem','求' in page.locator('.problem-stem').inner_text() and '正弦初位移' in page.locator('.session-card').inner_text())
 check('Answer hidden before reveal',page.locator('.worked-solution').count()==0 and page.locator('[data-action=study-rate][data-value="0"]').is_disabled())
 page.locator('.problem-hint summary').click();check('Hint opens independently',page.locator('.problem-hint .prose').is_visible() and page.locator('.worked-solution').count()==0)
 page.locator('#session-answer').fill('我的解：u(x,t)=sin(x)cos(2t)');flush(page)
 click(page,'[data-action=study-reveal]');page.wait_for_selector('.worked-solution')
 check('Worked answer has steps and final answer',page.locator('.solution-steps li').count()>=3 and page.locator('.final-answer').count()==1)
 check('New answer is not mislabelled textbook solution','不是原书标准答案' in page.locator('.worked-solution').inner_text())
 page.screenshot(path=str(OUT/'rc5-practice.png'),full_page=False)
 click(page,'[data-action=study-rate][data-value="0"]');flush(page)
 native=api('/api/state')[1]['state'];cards=list(native['cards'].values());check('Solved attempt persists authorship and source',len(cards)==1 and cards[0]['origin']=='authored_worked_problem' and cards[0]['wrong'] and cards[0]['answer'].startswith('我的解'))
 click(page,'[data-action=study-finish]');click(page,'[data-action=study-scope][data-value=wrong]');check('Solved problem enters wrong list',page.locator('.worked-problem').count()==1)
 click(page,'[data-action=study-one]');check('Retry has blank draft and retained history',page.locator('#session-answer').input_value()=='' and '我的解' in page.locator('.attempt-history').text_content())
 click(page,'[data-action=study-pause]')
 route(page,PDE,'front_cover','preview');check('Unwritten section labelled rather than faked',page.locator('.teaching-gap').count()==1 and '还没有专门编写' in page.locator('.teaching-gap').inner_text())
 route(page,PDE,'ch01_s02','review');check('Knowledge still accessible after solving',page.locator('.teaching-hub').count()==1)
 click(page,'[data-action=study-review-drill]');click(page,'[data-action=study-scope][data-value=wrong]');check('Review wrong queue includes solved problems',page.locator('.worked-problem').count()==1)
 # Check all new lessons and all new solutions in the actual production renderers.
 rendering=page.evaluate('''async()=>{
   const errors=[],counts={units:0,problems:0};const box=document.createElement('div');box.id='render-verification';document.body.append(box);
   for(const meta of state.catalog.books){const b=await loadBook(meta.id);state.currentBook=b;
     for(const u of b.teaching.units){box.innerHTML=teachingUnitPreview(u,b)+teachingUnitReview(u,b,true);await typeset(box);counts.units++;if(box.querySelector('[data-mjx-error],mjx-merror'))errors.push('unit:'+u.id);MathJax.typesetClear([box]);}
     for(const q of b.study.solved){const ss=ST.makeSession([q.id],'render',0);ss.revealed[q.id]=true;box.innerHTML=sessionHTML(b,b.sections.find(s=>s.id===q.section),'practice',ss);await typeset(box);counts.problems++;if(box.querySelector('[data-mjx-error],mjx-merror'))errors.push('problem:'+q.id);if(box.querySelectorAll('.solution-steps li').length<2)errors.push('steps:'+q.id);MathJax.typesetClear([box]);}
   }box.remove();return{...counts,errors};}''')
 check('All 42 lessons and 76 answers render without TeX error',rendering['units']==42 and rendering['problems']==76 and not rendering['errors'],rendering)
 route(page,PDE,'ch01_s02','preview');page.set_viewport_size({'width':390,'height':844})
 check('Mobile 20px preview fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'))
 page.screenshot(path=str(OUT/'rc5-mobile.png'),full_page=False)
 page.evaluate('async()=>{await mutate(s=>{s.settings.fontSize=72;s.settings.theme="dark"})}');page.wait_for_timeout(50)
 check('Mobile 72px preview fits viewport',page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'))
 check('No new uncaught JS errors',not errors,errors)
 browser.close()
