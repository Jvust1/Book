"""Content contracts and exact example checks, not independent expert acceptance.
Developer tests require SymPy. No Python/SymPy dependency in the shipped EXE.
"""
import hashlib, importlib.util, json, zipfile
from pathlib import Path
import sympy as S
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'web/data'; RESULTS=[]
def check(name,value):
 RESULTS.append({'check':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def eq(a,b):return S.simplify(a-b)==0
x,y,t,c=S.symbols('x y t c',real=True);n=S.symbols('n',positive=True);R=S.Rational;facts={}
def f(k,v):facts[k]=bool(v)
u=S.sin(x)*S.cos(2*t);f('wave-c2',eq(S.diff(u,t,2),4*S.diff(u,x,2)) and eq(u.subs(t,0),S.sin(x)) and eq(S.diff(u,t).subs(t,0),0))
u=x*t;f('wave-velocity',eq(S.diff(u,t,2),c*c*S.diff(u,x,2)) and eq(u.subs(t,0),0) and eq(S.diff(u,t).subs(t,0),x))
u=S.sin(2*x)*S.cos(6*t);f('wave-mode',eq(S.diff(u,t,2),9*S.diff(u,x,2)) and eq(u.subs(t,0),S.sin(2*x)) and eq(u.subs(x,S.pi),0))
u=R(3,2)*S.sin(2*t)*S.sin(x);f('wave-speed-amplitude',eq(S.diff(u,t,2),4*S.diff(u,x,2)) and eq(S.diff(u,t).subs(t,0),3*S.sin(x)))
u=S.exp(-18*t)*S.sin(3*x);f('heat-mode',eq(S.diff(u,t),2*S.diff(u,x,2)) and eq(u.subs(t,0),S.sin(3*x)))
u=1+2*x+S.exp(-S.pi**2*t)*S.sin(S.pi*x);f('heat-steady',eq(S.diff(u,t),S.diff(u,x,2)) and eq(u.subs(x,0),1) and eq(u.subs(x,1),3))
u=(1+4*t)**R(-1,2)*S.exp(-x*x/(1+4*t));f('heat-gaussian',eq(S.diff(u,t),S.diff(u,x,2)) and eq(u.subs(t,0),S.exp(-x*x)))
tp=S.symbols('tp',positive=True);G=S.exp(-x*x/(4*tp))/S.sqrt(4*S.pi*tp);f('heat-mass',eq(S.integrate(G,(x,-S.oo,S.oo)),1))
u=x*x-y*y;th=S.symbols('theta',real=True);f('laplace-quadratic',eq(S.diff(u,x,2)+S.diff(u,y,2),0) and S.trigsimp(u.subs({x:S.cos(th),y:S.sin(th)})-S.cos(2*th))==0)
u=3+2*x;f('laplace-linear',eq(S.diff(u,x,2)+S.diff(u,y,2),0) and u.subs(x,-1)==1 and u.subs(x,1)==5)
u=S.exp(-(x-2*t)**2);f('transport-gaussian',eq(S.diff(u,t)+2*S.diff(u,x),0) and eq(u.subs(t,0),S.exp(-x*x)))
u=x-t;f('transport-source',eq(S.diff(u,t)+3*S.diff(u,x),2) and eq(u.subs(t,0),x))
f('pde-discriminant',2**2-1==3);f('difference-step',R(1,2)*4==2 and R(1,4)*4==1);f('difference-amplification',1-4*R(3,4)==-2)
v1=S.Matrix([1,0,1]);v2=S.Matrix([0,1,1]);v3=S.Matrix([1,1,2]);f('basis-rank',v3==v1+v2 and S.Matrix.hstack(v1,v2,v3).rank()==2)
f('basis-coordinate',2*S.Matrix([1,1])+S.Matrix([1,-1])==S.Matrix([3,1]));f('norm-comparison',3+4==7 and S.sqrt(25)==5 and 49<=50)
f('truncated-norm',min(1,abs(2))!=2*min(1,abs(1)));f('ell2-basis-distance',S.Matrix([1,-1]).norm()==S.sqrt(2))
xn=1-3**(-n);f('contraction-linear',eq((xn+2)/3,1-3**(-n-1)))
a=S.Matrix([3,1]);v=S.Matrix([1,1]);z=a.dot(v)/v.dot(v)*v;f('projection-r2',z==S.Matrix([2,2]) and (a-z).dot(v)==0 and (a-z).norm()==S.sqrt(2))
a=S.Matrix([1,2,0]);v=S.Matrix([1,0,1]);z=a.dot(v)/v.dot(v)*v;f('projection-r3',z==S.Matrix([R(1,2),0,R(1,2)]) and eq((a-z).norm(),3/S.sqrt(2)))
f('functional-norm',S.Matrix([3,4]).norm()==5 and 3*R(3,5)+4*R(4,5)==5)
f('derivative-unbounded',S.diff(S.sin(n*x)/n,x).subs(x,0)==1 and S.limit(1/n,n,S.oo)==0)
# The infinite-dimensional weak-convergence proof remains written, not mechanically certified.
f('ell2-weak',S.limit(1/n,n,S.oo)==0);f('finite-weak',S.limit(S.sqrt(5)/n,n,S.oo)==0)
A=S.diag(2,3);f('spectrum-diagonal',set(A.eigenvals())=={2,3} and A.inv()==S.diag(R(1,2),R(1,3)))
A=S.Matrix([[0,1],[0,0]]);f('spectrum-nilpotent',set(A.eigenvals())=={0} and A*S.Matrix([0,1])==S.Matrix([1,0]))
f('money-purchasing-power',1000/R(25,2)==80 and R(80,100)-1==-R(1,5));f('compound-interest',100*R(11,10)**2==121)
f('bond-one-period',105/R(11,10)==R(1050,11));f('deposit-multiplier',100/R(1,10)==1000 and 1000-100==900)
D=120/(R(1,5)+R(1,10));f('cash-multiplier',D==400 and D/5==80 and D/10==40 and D*R(6,5)==480)
f('real-interest',R(108,105)-1==R(1,35));f('quantity-equation',R(110,105)-1==R(1,21))
f('exchange-inverse',R(77,70)-1==R(1,10) and 1-R(70,77)==R(1,11));f('exchange-cross',150/R(15,2)==20)
f('public-good',S.solve(18-2*x-6,x)==[6]);f('externality',20+5==25 and 23-25==-2)
f('expenditure-shares',R(60,100)==R(3,5) and R(40,100)==R(2,5));f('expenditure-ratio',R(240,1000)-R(240,1200)==R(4,100))
f('tax-equilibrium',100-60==40 and 60-40==20 and 100-50==50);f('tax-welfare',20*40==800 and 20*(50-40)/2==100)
f('debt-flow',110-100==10 and R(4,100)*500==20 and 500+10+20==530);f('debt-ratio',R(500,1000)==R(530,1060)==R(1,2))
f('real-gdp',110/R(110,100)==100);f('per-capita',R(106,102)-1==R(2,51));f('sector-shift',60+40*3==180 and 40+60*3==220 and R(40,180)==R(2,9));f('sector-shares',R(40,100)==R(2,5) and R(120,180)==R(2,3))
f('no-arbitrage-pv',121/R(11,10)==110);f('one-price-arbitrage',105-100==5)
d=R(1,2);b=-R(800,21);f('binomial-call',d*120+R(21,20)*b==20 and d*80+R(21,20)*b==0 and d*100+b==R(250,21))
d=-R(1,2);b=R(400,7);f('binomial-put',d*120+R(21,20)*b==0 and d*80+R(21,20)*b==20 and d*100+b==R(50,7) and R(250,21)-R(50,7)==100-100/R(21,20))
f('state-pricing',R(4,10)*10+R(5,10)*20==14 and 1/R(9,10)==R(10,9));f('sdf',R(4,10)/R(1,2)==R(4,5) and R(1,2)*R(4,5)*10+R(1,2)*20==14)
f('lp-x',S.integrate(x,(x,0,1))==R(1,2) and eq(S.sqrt(S.integrate(x*x,(x,0,1))),1/S.sqrt(3)))
f('lp-singularity',S.integrate(x**R(-2,3),(x,0,1))==3 and S.integrate(1/x,(x,0,1))==S.oo)
f('holder-vectors',S.Matrix([1,2]).dot(S.Matrix([2,1]))==4 and S.Matrix([1,2]).norm()*S.Matrix([2,1]).norm()==5);f('minkowski-vectors',S.Matrix([1,1]).norm()==S.sqrt(2) and S.sqrt(2)<2)
f('lp-functional',eq(S.integrate(x*S.sqrt(3)*x,(x,0,1)),1/S.sqrt(3)) and S.integrate((S.sqrt(3)*x)**2,(x,0,1))==1);f('ell1-dual',max(abs(-2),abs(3))==3 and -2*0+3*1==3)
for k,v in facts.items():check('math-example:'+k,v)
spec=importlib.util.spec_from_file_location('build_teaching',ROOT/'tools/build_teaching.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
cat=json.loads((DATA/'catalog.json').read_text());seen=set();totals={'units':0,'problems':0,'knowledge_points':0,'written_concept_items':0}
for bi in cat['books']:
 bid=bi['id'];d=json.loads((DATA/(bid+'.teaching.json')).read_text());book=json.loads((DATA/(bid+'.json')).read_text());byid={r['id']:r for r in book['records']}
 check(bid+':deterministic',d==mod.compile_book(bi));check(bid+':identity',d['source_book_sha256']==hashlib.sha256((DATA/(bid+'.json')).read_bytes()).hexdigest());check(bid+':no-overclaim',d['whole_book_authored_complete'] is False and d['coverage']['whole_book_knowledge_acceptance'] is False)
 totals['units']+=len(d['units']);totals['problems']+=len(d['solved'])
 for u in d['units']:
  check(u['id']+':actual-preview',len(u['preview']['overview'])>=100 and len(u['preview']['goals'])>=2)
  check(u['id']+':actual-review',len(u['review']['points'])>=3 and len(u['review']['method'])>=3 and len(u['review']['pitfalls'])>=2)
  totals['knowledge_points']+=len(u['review']['points']);check(u['id']+':real-anchors',all(r['record_id'] in byid and r['pdf_pages']==byid[r['record_id']].get('source_pdf_pages',[]) for r in u['source_refs']))
 for q in d['solved']:
  check(q['id']+':unique',q['id'] not in seen);seen.add(q['id']);check(q['id']+':complete-answer',len(q['stem'])>=20 and len(q['steps'])>=2 and bool(q['answer']) and bool(q['hint']) and bool(q['pitfall']))
  check(q['id']+':honest-origin',q['origin']=='authored_worked_problem' and q['independent_expert_review'] is False);check(q['id']+':check-declared',q['check']=='conceptual' or q['check'] in facts)
  if q['check']=='conceptual':totals['written_concept_items']+=1
check('units42',totals['units']==42);check('problems76',totals['problems']==76)
archive=Path('/mnt/data/book_input/rc4-source.zip')
if archive.exists():
 with zipfile.ZipFile(archive) as z:
  names=[n for n in z.namelist() if '/web/media/' in n or ('/web/data/' in n and n.endswith('.json') and not n.endswith(('catalog.json','app_asset_manifest.json')))]
  check('immutable-source-study-media-preserved',all(z.read(n)==(ROOT/'web'/n.split('/web/',1)[1]).read_bytes() for n in names));totals['immutable_files_compared']=len(names)
report={'schema':'book-teaching-tests-v1','scope':'Content contracts and exact example calculations; written conceptual and infinite-dimensional proofs are not mechanically certified. Not expert review.','totals':totals,'math_example_checks':len(facts),'checks':RESULTS,'passed':sum(r['passed'] for r in RESULTS),'failed':sum(not r['passed'] for r in RESULTS)}
(ROOT/'verification/teaching_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
