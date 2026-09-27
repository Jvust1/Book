/* Chapter trees and exam workflows reuse the native store and stable question IDs. */
'use strict';
const EX=BookExam;
const learningLoad=loadBook;
loadBook=async function(id){
  const b=await learningLoad(id);if(b.learningLoaded)return b;
  try{
    const d=await req('/data/'+encodeURIComponent(id)+'.learning.json');
    if(d.schema!=='book-learning-sidecar-v1'||d.book_id!==id)throw Error('学习层身份不匹配');
    b.learning=d;b.learningSections=new Map(d.sections.map(s=>[s.id,s]));
    for(const g of b.studyById.values()){
      g.chapter_ids=d.question_chapters[g.id]||[];
      if(d.original_answers[g.id])g.worked_solution=d.original_answers[g.id];
    }
  }catch(e){b.learningError=e.message;}
  b.learningLoaded=true;return b;
};
function learningNavigation(){return '<div class="learning-nav row"><button data-action="study-tree">章节知识树</button><button data-action="study-exam-hub">考试模式</button><button data-action="study-emphasis">高频知识点 / 建议重点</button></div>';}
function treeHTML(b){
  if(!b.learning)return '<p class="qualitywarn">知识树读取失败：'+esc(b.learningError||'缺少学习层')+'</p>';
  const d=b.learning;
  return '<section class="study-hub"><div class="eyebrow">CHAPTER KNOWLEDGE TREE</div><h2>从章节到知识，再回到来源。</h2><p>'+d.sections.length+' 个目录入口已组织成树。展开定义、定理、公式或论述查看原有记录；配套精讲单独显示。来源整理不等于全书精讲或考试大纲已完成。</p><p class="muted">'+(info(b.book_id).index_only?'本书保留结构索引，不能当成完整原文。':'来源转录的质量提示保持有效。')+' 目录归属不明确的条目单列，不按页码猜测章节。</p><button data-action="study-knowledge">返回知识速查</button></section><div class="knowledge-tree">'+d.chapters.map(c=>'<details class="tree-chapter"><summary>'+esc(c.title)+' <small>'+c.section_ids.length+' 个目录条目</small></summary>'+c.section_ids.map(id=>{
    const n=b.learningSections.get(id);return '<details class="tree-section" data-tree-section="'+esc(id)+'"><summary>'+esc(n.title)+' <small>'+n.record_count+' 条来源 · '+(n.unit_ids.length?n.unit_ids.length+' 个精讲主题':'精讲待补')+'</small></summary><div class="tree-section-body" data-tree-body="'+esc(id)+'"></div></details>';
  }).join('')+'</details>').join('')+'</div>';
}
function treeSectionHTML(b,n){
  const units=n.unit_ids.map(id=>b.teaching.units.find(u=>u.id===id)).filter(Boolean);
  return '<button data-action="study-tree-read" data-section="'+esc(n.id)+'">打开本节预习 →</button>'+units.map(u=>teachingUnitReview(u,b,false)).join('')+Object.entries(n.categories).map(([category,ids])=>'<details class="tree-category"><summary>'+esc(category)+' · '+ids.length+'</summary>'+ids.map(id=>{const r=b.byId.get(id);return '<details class="tree-record" data-tree-record="'+esc(id)+'"><summary>'+esc((r.title||r.text||r.latex||TYPES[r.type]||'来源条目').replace(/\s+/g,' ').slice(0,100))+'</summary><div class="tree-record-body"></div></details>';}).join('')+'</details>').join('')+(!n.record_count?'<p>该条目仅有来源定位或习题索引；尚无可整理的知识正文。</p>':'');
}
function emphasisHTML(b){
  const units=b.teaching?.units||[];
  return '<section class="study-hub"><div class="eyebrow">EXAM EMPHASIS</div><h2>高频知识点：先说明依据。</h2><p>当前没有接入可统计的历年试卷或教师考试大纲，真题频次证据为 0。下列是已编写主题中的建议复习重点，依据核心定义、条件和解题方法整理，不标“必考”或虚构频率。</p><button data-action="study-exam-hub">进入考试模式</button></section>'+units.map(u=>'<details class="emphasis-unit"><summary>'+esc(u.title)+' · 建议重点</summary>'+u.review.points.map(p=>'<h3>'+esc(p.title)+'</h3><div class="prose">'+richText(p.body)+'</div>').join('')+'<h3>方法总结</h3><ol>'+u.review.method.map(x=>'<li>'+richText(x)+'</li>').join('')+'</ol><button data-action="study-unit-practice" data-unit="'+esc(u.id)+'">练本主题</button></details>').join('');
}
function examQuestions(b){return [...b.study.questions,...(b.study.solved||[])].filter(EX.ready);}
function examHubHTML(b){
  const qs=examQuestions(b),ss=getSession(b,'practice'),all=b.learning?.chapters||[];
  const eligible=all.filter(c=>c.id!=='unmapped'&&qs.some(q=>q.chapter_ids.includes(c.id)));
  const weak=EX.select(qs,state.personal.cards,b.book_id,'wrong','',50).length;
  return '<section class="study-hub exam-hub"><div class="eyebrow">EXAM DESK / 本机自测</div><h2>选一轮练习，把知识用起来。</h2><p>当前有 '+qs.length+' 道题可核对参考解答，其中原书题 '+qs.filter(q=>q.origin==='textbook_question').length+' 道。章节测试交卷前隐藏答案，交卷后自行核对；这里不自动判分，也不提供监考。</p>'+
  (ss?.exam?'<div class="resume-session"><span>已有'+(ss.status==='finished'?'已结束':'未完成')+'的'+(ss.exam.kind==='chapter'?'章节测试':'练习')+'，'+ss.queue.length+'题 · 已自评 '+Object.keys(ss.results).length+'题</span>'+(ss.status!=='finished'?'<button data-action="study-exam-resume">继续 / 查看本轮</button>':'')+'</div>':'')+
  '<div class="exam-options"><label>本轮题量 <select id="exam-limit"><option>5</option><option selected>10</option><option>20</option><option>50</option></select></label><label>测试时长 <select id="exam-minutes"><option>10</option><option selected>20</option><option>45</option><option>90</option></select> 分钟</label><label>章节 <select id="exam-chapter">'+eligible.map(c=>'<option value="'+esc(c.id)+'">'+esc(c.title)+'</option>').join('')+'</select></label></div><div class="exam-grid">'+
  '<article><h3>期末速刷</h3><p>优先薄弱、到期、未练题；每题可立即核对参考解答。</p><button class="primary" data-action="study-exam-start" data-kind="quick" '+(!qs.length?'disabled':'')+'>开始速刷</button></article>'+
  '<article><h3>高频知识点</h3><p>查看建议重点与适用条件；暂无真题频次统计。</p><button data-action="study-emphasis">查看重点</button></article>'+
  '<article><h3>错题循环</h3><p>'+weak+' 道可解答的薄弱题（最多显示50）；自评“已理解”后退出薄弱队列，历史保留。</p><button data-action="study-exam-start" data-kind="wrong" '+(!weak?'disabled':'')+'>重练薄弱题</button></article>'+
  '<article><h3>章节测试</h3><p>整章选题、保存草稿、交卷后核对。暂停或关闭窗口不停止计时。</p><button data-action="study-exam-start" data-kind="chapter" '+(!eligible.length?'disabled':'')+'>开始章节测试</button></article></div><p class="muted">新练习会归档上轮会话；不会覆盖旧作答。没有配套解答的原题仍在教材练习页，未被计入以上可解答题量。</p><button data-action="study-learning-back">返回普通练习</button></section>';
}
const learningPreview=previewHTML;
previewHTML=function(b,s,rr){return learningNavigation()+learningPreview(b,s,rr)};
const learningBefore=learningHTML;
learningHTML=function(b,s,mode){
  const v=studyView(b,mode),ss=getSession(b,mode);
  if(ss?.status==='active')return learningNavigation()+sessionHTML(b,s,mode,ss);
  const body=v.learningPane==='tree'?treeHTML(b):v.learningPane==='exam'?examHubHTML(b):v.learningPane==='emphasis'?emphasisHTML(b):learningBefore(b,s,mode);
  return learningNavigation()+body;
};
function originalSolutionHTML(g){const w=g.worked_solution;return '<section class="answer-source source-flow worked-solution"><p class="teaching-boundary">原书题目 · 配套参考解答，非原书标准答案，待独立校核。</p><h3>分步解答</h3><ol class="solution-steps">'+w.steps.map(x=>'<li>'+richText(x)+'</li>').join('')+'</ol><div class="final-answer"><h3>答案与结论</h3>'+richText(w.answer)+'</div><h3>方法总结</h3><ol>'+w.method.map(x=>'<li>'+richText(x)+'</li>').join('')+'</ol><h3>易错点</h3>'+richText(w.pitfall)+'</section>';}
const learningSession=sessionHTML;
sessionHTML=function(b,s,mode,ss){
  const g=b.studyById.get(ss.queue[ss.index]);if(!g)return learningSession(b,s,mode,ss);
  if(ss.exam&&!EX.canReveal(ss)){
    const left=Math.max(0,Math.ceil((ss.exam.deadline-Date.now())/1000));
    return '<section class="session-top"><h2>章节测试 · '+(ss.index+1)+' / '+ss.queue.length+'</h2><p>剩余 <strong data-exam-clock>'+Math.floor(left/60)+':'+String(left%60).padStart(2,'0')+'</strong> · 暂停不停止计时</p><button data-action="study-pause">暂停并保存</button><button data-action="study-exam-submit">交卷并核对</button></section><section class="studycard session-card"><h3>'+esc(g.title)+'</h3>'+groupSource(g,b)+'<label for="session-answer">我的解答</label><textarea id="session-answer" data-study-draft="1">'+esc(ss.drafts[g.id]||'')+'</textarea><p>交卷后显示答案、方法和自评。空白题保留为未作答，不计为正确。</p></section><div class="pager"><button data-action="study-prev" '+(ss.index===0?'disabled':'')+'>上一题</button><span>'+Object.values(ss.drafts).filter(x=>x.trim()).length+' / '+ss.queue.length+' 已填写</span><button data-action="'+(ss.index+1===ss.queue.length?'study-exam-submit':'study-next')+'">'+(ss.index+1===ss.queue.length?'交卷':'下一题')+'</button></div>';
  }
  let html=learningSession(b,s,mode,ss);
  if(g.worked_solution&&ss.revealed[g.id])html=html.replace(/<div class="answer-source source-flow">[\s\S]*?<div class="self-rating">/,originalSolutionHTML(g)+'<div class="self-rating">');
  if(ss.exam&&ss.submitted_at!==null){
    html=html.replace(/<textarea id="session-answer"/,'<textarea readonly id="session-answer"');
    const ratings=Object.values(ss.results);
    html='<section class="exam-summary"><h2>交卷后核对</h2><p>原始作答已锁定；'+ss.unanswered+' 道未作答。已自评 '+ratings.length+' / '+ss.queue.length+'，其中自评已理解 '+ratings.filter(x=>x===2).length+'，薄弱 '+ratings.filter(x=>x<2).length+'。这些不是自动评分或考试成绩。</p><button data-action="study-exam-hub">返回考试工作台</button></section>'+html;
  }
  return html;
};
const learningAction=studyAction;
studyAction=async function(el){
  const a=el.dataset.action,b=state.currentBook;if(!b)return learningAction(el);
  const mode=state.route.mode,ss=getSession(b,mode);
  if(a==='study-exam-submit'){
    await flushStudy();await mutate(p=>{const x=ST.personalBook(p,b.book_id).sessions[mode];if(x?.id!==ss?.id)throw Error('会话已改变');EX.submit(x)});return redrawStudy();
  }
  if(ss?.exam&&!EX.canReveal(ss)&&['study-reveal','study-rate'].includes(a))return;
  if(ss?.exam&&!EX.canReveal(ss)&&(a==='study-finish'||(a==='study-next'&&ss.index+1===ss.queue.length)))return studyAction({dataset:{action:'study-exam-submit'}});
  if(['study-tree','study-exam-hub','study-emphasis','study-learning-back'].includes(a)){
    await flushStudy();const target=a==='study-exam-hub'||a==='study-learning-back'?'practice':'review';
    await mutate(p=>{const x=ST.personalBook(p,b.book_id).sessions[target];if(x?.status==='active')x.status='paused'});
    studyView(b,target).learningPane=({'study-tree':'tree','study-exam-hub':'exam','study-emphasis':'emphasis'})[a]||null;
    routeTo({...state.route,mode:target});return redrawStudy();
  }
  if(a==='study-tree-read'){studyView(b,'review').learningPane=null;routeTo({...state.route,mode:'preview',section:el.dataset.section,offset:0,record:null});return;}
  if(a==='study-exam-start'){
    await flushStudy();const kind=el.dataset.kind,chapter=$('#exam-chapter')?.value||'',limit=Number($('#exam-limit').value),minutes=Number($('#exam-minutes').value);
    if(kind==='chapter'&&(!chapter||chapter==='unmapped'))return toast('请先选择已核定归属的章节');
    const list=EX.select(examQuestions(b),state.personal.cards,b.book_id,kind,chapter,limit);if(!list.length)return toast('当前范围暂无有解答的题目');
    const next=EX.create(list.map(g=>g.id),uid(),Date.now(),kind,chapter,minutes);
    await mutate(p=>{const st=ST.personalBook(p,b.book_id),old=st.sessions.practice;if(old)st.sessionHistory.push(old);st.sessions.practice=next});
    studyView(b,'practice').learningPane=null;routeTo({...state.route,mode:'practice'});return redrawStudy();
  }
  if(a==='study-exam-resume'){
    await flushStudy();await mutate(p=>{const x=ST.personalBook(p,b.book_id).sessions.practice;if(x){x.status='active';if(EX.expired(x))EX.submit(x)}});
    studyView(b,'practice').learningPane=null;return redrawStudy();
  }
  if(['study-knowledge','study-knowledge-all','study-review-drill','study-unit-practice'].includes(a))studyView(b,'review').learningPane=null;
  return learningAction(el);
};
// Prevent a post-submit edit from being queued even through programmatic input events.
const learningInput=bindStudyInput;
bindStudyInput=function(t){const ss=state.currentBook&&getSession(state.currentBook,state.route.mode);if(t.dataset.studyDraft&&ss?.exam&&(ss.submitted_at!==null||EX.expired(ss)))return;return learningInput(t)};
document.addEventListener('toggle',e=>{
  if(!e.target.open||!state.currentBook)return;const b=state.currentBook;
  if(e.target.matches('.tree-section')){const n=b.learningSections.get(e.target.dataset.treeSection),target=e.target.querySelector('.tree-section-body');if(!target.childNodes.length)target.innerHTML=treeSectionHTML(b,n);typeset(target);}
  if(e.target.matches('.tree-record')){const r=b.byId.get(e.target.dataset.treeRecord),target=e.target.querySelector('.tree-record-body');if(!target.childNodes.length)target.innerHTML=rHTML(r,{actions:false})+'<button data-action="context" data-id="'+esc(r.id)+'">查看来源上下文</button>';typeset(target);}
  if(e.target.matches('.emphasis-unit'))typeset(e.target);
},true);
let examTickBusy=false;
setInterval(async()=>{
  const b=state.currentBook,ss=b&&getSession(b,state.route.mode);if(!ss?.exam||ss.submitted_at!==null||ss.status==='finished')return;
  const clock=$('[data-exam-clock]');if(clock){const left=Math.max(0,Math.ceil((ss.exam.deadline-Date.now())/1000));clock.textContent=Math.floor(left/60)+':'+String(left%60).padStart(2,'0');}
  if(EX.expired(ss)&&!examTickBusy){examTickBusy=true;try{await flushStudy();await mutate(p=>{const x=ST.personalBook(p,b.book_id).sessions.practice;if(x?.id===ss.id&&EX.expired(x))EX.submit(x)});await redrawStudy();toast('时间到，已保存并交卷，可核对参考解答')}catch(e){toast('交卷保存失败：'+e.message+'，请重试保存')}finally{examTickBusy=false;}}
},1000);
window.__bookTest={...window.__bookTest,loadBook,EX,examQuestions,treeHTML,treeSectionHTML,examHubHTML,emphasisHTML,sessionHTML,studyAction};
boot();
