/* Authored learning content is a separate layer; source facts and study history stay intact. */
'use strict';
const teachingViews = new Map();
function teachingView(b) {
  if (!teachingViews.has(b.book_id)) teachingViews.set(b.book_id, {scope:'section',category:'all',query:'',offset:0});
  return teachingViews.get(b.book_id);
}
const priorTeachingLoad = loadBook;
loadBook = async function(id) {
  const b = await priorTeachingLoad(id);
  if (!b.teachingLoaded) {
    b.study.solved = [];
    try {
      const t = await req('/data/'+encodeURIComponent(id)+'.teaching.json');
      if (t.schema!=='book-teaching-sidecar-v1' || t.book_id!==id || !Array.isArray(t.units) || !Array.isArray(t.solved)) throw Error('讲解层身份不匹配');
      b.teaching=t;b.study.solved=t.solved;
      for (const p of t.solved) b.studyById.set(p.id,p);
    } catch(e) { b.teachingError=e.message; }
    b.teachingLoaded=true;
  }
  return b;
};
const priorTeachingStudyView = studyView;
studyView = function(b,mode) {
  const v=priorTeachingStudyView(b,mode);
  if (!v.teachingInitialized) {v.kind=mode==='review'?'knowledge':'solved';v.teachingInitialized=true;}
  return v;
};
const priorOriginName=originName;
originName=function(g){return g.origin==='authored_worked_problem'?'配套原创题 · 含参考解答':priorOriginName(g)};
const priorGroupSource=groupSource;
groupSource=function(g,b){return g.origin==='authored_worked_problem'?'<div class="prose problem-stem">'+richText(g.stem)+'</div>':priorGroupSource(g,b)};
function teachingRefs(u,b) {
  const refs=u.source_refs||[],seen=new Set();
  const links=refs.filter(r=>{const k=r.section_id;if(seen.has(k))return false;seen.add(k);return true});
  return '<details class="teaching-refs"><summary>对应教材主题与来源位置</summary><p class="muted">这些位置用于定位相关主题，不表示下方原创题或参考解答出自原书。原始转录质量标记保持不变。</p>'+links.map(r=>'<button data-action="context" data-id="'+esc(r.record_id)+'">'+esc(safeSectionText(b.sections.find(s=>s.id===r.section_id)||{id:r.section_id}))+' · PDF '+esc((r.pdf_pages||[]).join(', '))+' ↗</button>').join('')+'</details>';
}
function teachingPicker(b,selected='') {
  const units=b.teaching?.units||[];
  return '<label class="teaching-picker">精讲主题 <select id="teaching-topic" aria-label="选择精讲主题"><option value="">当前目录对应主题</option>'+units.map(u=>'<option value="'+esc(u.id)+'" '+(selected===u.id?'selected':'')+'>'+esc(u.title)+'</option>').join('')+'</select></label>';
}
function teachingUnitPreview(u,b) {
  return '<article class="teaching-lesson" data-teaching-unit="'+esc(u.id)+'"><div class="eyebrow">精简导学 / 配套编写</div><h2>'+esc(u.title)+'</h2><div class="prose preview-explanation">'+richText(u.preview.overview)+'</div><div class="teaching-grid"><section><h3>先备知识</h3><ul>'+u.preview.prerequisites.map(t=>'<li>'+richText(t)+'</li>').join('')+'</ul></section><section><h3>学完要会什么</h3><ul>'+u.preview.goals.map(t=>'<li>'+richText(t)+'</li>').join('')+'</ul></section></div><section class="preview-core"><h3>先抓住这条核心知识</h3><h4>'+esc(u.review.points[0].title)+'</h4><div class="prose">'+richText(u.review.points[0].body)+'</div></section><div class="row"><button class="primary" data-action="mode" data-mode="learn">进入教材完整学习 →</button><button data-action="study-knowledge">查看知识整理</button><button data-action="study-unit-practice" data-unit="'+esc(u.id)+'">练习本主题 · '+u.problem_ids.length+' 题</button></div>'+teachingRefs(u,b)+'</article>';
}
function teachingUnitReview(u,b,open=true) {
  return '<details class="teaching-lesson review-lesson" data-teaching-unit="'+esc(u.id)+'" '+(open?'open':'')+'><summary><span>'+esc(u.title)+'</span><small>'+u.review.points.length+' 项知识 · '+u.problem_ids.length+' 道配套题</small></summary><div class="review-lesson-body">'+u.review.points.map((p,i)=>'<section class="knowledge-point"><div class="knowledge-number">'+String(i+1).padStart(2,'0')+'</div><div><h3>'+esc(p.title)+'</h3><div class="prose">'+richText(p.body)+'</div></div></section>').join('')+'<section class="review-method"><h3>遇到题目怎样下手</h3><ol>'+u.review.method.map(x=>'<li>'+richText(x)+'</li>').join('')+'</ol></section><section class="review-pitfalls"><h3>易错点与适用边界</h3><ul>'+u.review.pitfalls.map(x=>'<li>'+richText(x)+'</li>').join('')+'</ul></section><div class="row"><button class="primary" data-action="study-unit-practice" data-unit="'+esc(u.id)+'">用 '+u.problem_ids.length+' 道有解答题检验</button><button data-action="mode" data-mode="learn">回教材完整学习</button></div>'+teachingRefs(u,b)+'</div></details>';
}
function topicUnits(b,s,all=false) {return (b.teaching?.units||[]).filter(u=>all||u.sections.includes(s.id))}
function missingTeaching(b,s) {
  const n=b.teaching?.coverage.authored_units||0;
  return '<div class="teaching-gap"><h3>本节还没有专门编写的精简讲解</h3><p>本书已有 '+n+' 个精讲主题。可在上方选择主题，或在复习页查看本节教材知识记录；未编写部分不会显示为完成。</p>'+(b.teachingError?'<p>讲解层读取失败：'+esc(b.teachingError)+'</p>':'')+'<button data-action="study-knowledge-all">查看本书全部精讲与知识汇总</button></div>';
}
const priorTeachingPreview=previewHTML;
previewHTML=function(b,s,rr) {
  const units=topicUnits(b,s),old=priorTeachingPreview(b,s,rr);
  // Keep the existing checklist/note controls, but do not substitute them for the lesson.
  const personal=old.split('</section>')[0]+'</section>';
  const status='<p class="teaching-boundary">配套讲解与教材原文分层保存；本版有 '+(b.teaching?.coverage.authored_units||0)+' 个精讲主题，不等于全书逐节精讲完成。</p>';
  return teachingPicker(b)+status+(units.length?units.map(u=>teachingUnitPreview(u,b)).join(''):missingTeaching(b,s))+personal;
};
function sourceReviewEntries(b,s,v) {
  const sections=v.scope==='all'?b.sections:[s],seen=new Set(),rows=[];
  for(const sec of sections) for(const [category,ids] of Object.entries(b.teaching?.review_by_section?.[sec.id]||{})) {
    for(const id of ids) {
      if(seen.has(id))continue;seen.add(id);
      const r=b.byId.get(id);if(!r)continue;
      if(v.category!=='all'&&category!==v.category)continue;
      const str=(r.title||'')+' '+(r.text||'')+' '+(r.latex||'')+' '+(r.parts||[]).map(p=>typeof p==='string'?p:p.text||p.latex||'').join(' ');
      if(v.query&&!str.toLowerCase().includes(v.query.toLowerCase()))continue;
      rows.push({r,category,section:sec});
    }
  }
  return rows;
}
function teachingKnowledgeHTML(b,s) {
  const v=teachingView(b),units=topicUnits(b,s,v.scope==='all'),allRows=sourceReviewEntries(b,s,v);
  const max=Math.max(0,Math.floor((allRows.length-1)/20)*20);v.offset=Math.min(max,v.offset);
  const cats=['all','定义与概念','定理与命题','公式与关系','证明与推导','例题与说明','知识论述与补充','图表'];
  const top='<section class="teaching-hub"><div class="eyebrow">EXAM REVIEW / 知识速查</div><h2>把知识串起来，再用题目检验。</h2><p>定义、结论、适用条件、解题方法与易错点集中整理。没有考试大纲或真题依据时，不声称某知识“必考”或有确定分值。</p><div class="filters">'+[['section','当前节'],['all','全书']].map(([k,t])=>'<button data-action="study-knowledge-scope" data-value="'+k+'" class="'+(v.scope===k?'active':'')+'">'+t+'</button>').join('')+'<button data-action="study-review-drill">进入回忆 / 错题复习</button></div>'+teachingPicker(b)+'<p class="teaching-boundary">精讲已覆盖本书 '+(b.teaching?.coverage.authored_sections||0)+' / '+b.sections.length+' 个来源目录条目（包括前置页和索引条目，不能当作正文完成率）。下方教材记录汇总与精讲分开，不把自动汇总冒充人工穷尽的考试知识体系。</p></section>';
  const lessons=units.length?units.map((u,i)=>teachingUnitReview(u,b,i===0||v.scope==='section')).join(''):missingTeaching(b,s);
  const sources='<section class="source-review-hub"><h2>教材知识汇总 · 来源整理</h2><p>按定义、定理、公式、论述等类型集中查看已有可见记录，正文不改写。转录草稿、索引及证明均保留原质量提示。'+(info(b.book_id).index_only?'本书此区是结构索引，不是完整定理证明。':'')+'</p><div class="knowledge-filters"><label>类别 <select id="knowledge-category" aria-label="知识类别">'+cats.map(k=>'<option value="'+k+'" '+(k===v.category?'selected':'')+'>'+(k==='all'?'全部类别':k)+'</option>').join('')+'</select></label><label>检索 <input id="knowledge-query" type="search" aria-label="检索知识点" value="'+esc(v.query)+'" placeholder="定义、条件、符号或关键词"></label><button data-action="study-knowledge-find">筛选</button><button data-action="study-knowledge-clear">重置</button></div><p class="muted">'+allRows.length+' 条来源记录；每页20条，可逐页展开，不因展示长度而丢弃后续记录。</p></section>';
  const rows=allRows.slice(v.offset,v.offset+20).map(({r,category,section})=>'<details class="source-knowledge"><summary><span class="tag">'+esc(category)+'</span><span>'+esc((r.title||r.text||r.latex||TYPES[r.type]||'来源条目').replace(/\s+/g,' ').slice(0,120))+'</span></summary><div class="source-knowledge-body"><p class="muted">'+esc(safeSectionText(section))+' · PDF '+esc((r.source_pdf_pages||[]).join(', '))+'</p>'+rHTML(r,{actions:false})+'<button data-action="context" data-id="'+esc(r.id)+'">查看教材上下文 ↗</button></div></details>').join('');
  const pager='<div class="pager"><button data-action="study-knowledge-prev" '+(v.offset===0?'disabled':'')+'>← 上一页</button><span>'+(allRows.length?v.offset+1:0)+'–'+Math.min(v.offset+20,allRows.length)+' / '+allRows.length+'</span><button data-action="study-knowledge-next" '+(v.offset+20>=allRows.length?'disabled':'')+'>下一页 →</button></div>';
  return top+lessons+sources+(rows||'<p class="empty">当前范围没有匹配的记录。可重置筛选或切换全书。</p>')+pager;
}
const priorTeachingLearning=learningHTML;
learningHTML=function(b,s,mode){
  const v=studyView(b,mode),ss=getSession(b,mode);
  if(mode==='review'&&v.kind==='knowledge'&&ss?.status!=='active')return teachingKnowledgeHTML(b,s);
  return (mode==='review'?'<div class="row"><button data-action="study-knowledge">← 返回知识整理</button></div>':'')+priorTeachingLearning(b,s,mode);
};
const priorTeachingGroupCard=studyGroupCard;
studyGroupCard=function(g,b){
  if(g.origin!=='authored_worked_problem')return priorTeachingGroupCard(g,b);
  return '<article class="studycard worked-problem" data-group="'+esc(g.id)+'"><div class="cardlabel">'+originName(g)+'</div><h3>'+esc(g.title)+'</h3>'+groupSource(g,b)+'<p class="muted">含提示、'+g.steps.length+' 步解答、最终答案与易错点。先作答，再展开答案。</p><div class="row"><button class="primary" data-action="study-one" data-id="'+esc(g.id)+'">开始作答</button>'+studyContextButton(g)+'</div>'+attemptHistory(g,b)+'</article>';
};
const priorTeachingSession=sessionHTML;
sessionHTML=function(b,s,mode,session){
  const id=session.queue[session.index],g=b.studyById.get(id);
  if(g?.origin!=='authored_worked_problem')return priorTeachingSession(b,s,mode,session);
  const answered=Object.hasOwn(session.results,id),revealed=!!session.revealed[id],done=Object.keys(session.results).length;
  return '<section class="session-top"><div><div class="eyebrow">WORKED PRACTICE / '+(session.index+1)+' OF '+session.queue.length+'</div><h2>先独立作答，再逐步核对。</h2><p>已自评 '+done+' / '+session.queue.length+' · 配套原创题</p></div><div class="row"><button data-action="study-pause">暂停并保存</button><button data-action="study-finish">结束本轮</button></div><progress value="'+done+'" max="'+session.queue.length+'"></progress></section><section class="studycard session-card" data-group="'+esc(g.id)+'"><h3>'+esc(g.title)+'</h3>'+groupSource(g,b)+'<details class="problem-hint"><summary>只看提示</summary><div class="prose">'+richText(g.hint)+'</div></details><label class="answer-label" for="session-answer">我的解答 <small>自动保存到本机</small></label><textarea id="session-answer" data-study-draft="1" '+(answered?'readonly':'')+' placeholder="写出条件、公式、计算或证明步骤；支持 LaTeX。">'+esc(session.drafts[id]||'')+'</textarea><div class="row"><button data-action="study-preview-answer">排版预览</button><button class="primary" data-action="study-reveal">'+(revealed?'收起参考解答':'查看分步解答与答案')+'</button>'+studyContextButton(g)+'</div>'+(revealed?'<section class="answer-source source-flow worked-solution"><p class="teaching-boundary">配套编写的参考解答，不是原书标准答案。提供完整推导，尚未经过独立专家逐题终验；自评不会自动认证掌握程度。</p><h3>分步解答</h3><ol class="solution-steps">'+g.steps.map(x=>'<li><div class="prose">'+richText(x)+'</div></li>').join('')+'</ol><div class="final-answer"><h3>最终答案</h3><div class="prose">'+richText(g.answer)+'</div></div><h3>易错提醒</h3><div class="prose">'+richText(g.pitfall)+'</div></section>':'')+'<div class="self-rating"><p>'+(answered?'本轮自评已保存；重新练习会保留历史。':'核对完整解答后自评；不会的题可进入错题复习。')+'</p><div class="row">'+[['0','还不会'],['1','需复习'],['2','已理解']].map(([v,t])=>'<button data-action="study-rate" data-value="'+v+'" '+(!revealed||answered?'disabled':'')+'>'+t+'</button>').join('')+'</div></div>'+attemptHistory(g,b)+'</section><div class="pager"><button data-action="study-prev" '+(session.index===0?'disabled':'')+'>← 上一题</button><span>'+(session.index+1)+' / '+session.queue.length+'</span><button class="primary" data-action="study-next">'+(session.index+1===session.queue.length?'完成本轮':'下一题 →')+'</button></div>';
};
const priorTeachingAction=studyAction;
studyAction=async function(el){
  const a=el.dataset.action,b=state.currentBook;
  if(!b||!['study-knowledge','study-knowledge-all','study-knowledge-scope','study-knowledge-find','study-knowledge-clear','study-knowledge-prev','study-knowledge-next','study-review-drill','study-unit-practice'].includes(a))return priorTeachingAction(el);
  await flushStudy();
  if(a==='study-unit-practice'){
    const u=b.teaching.units.find(x=>x.id===el.dataset.unit);if(!u)return;
    const active=getSession(b,'practice');
    // Reuse the existing history-preserving session transition.
    await startSession(u.problem_ids.map(id=>b.studyById.get(id)),'practice',false,50);
    routeTo({...state.route,mode:'practice'});return;
  }
  const v=teachingView(b);
  if(a==='study-knowledge'||a==='study-knowledge-all'){
    const ss=getSession(b,'review');
    if(ss?.status==='active')await mutate(p=>{ST.personalBook(p,b.book_id).sessions.review.status='paused'});
    studyView(b,'review').kind='knowledge';
    if(a.endsWith('-all'))v.scope='all';
    routeTo({...state.route,mode:'review'});return redrawStudy();
  }
  if(a==='study-review-drill'){studyView(b,'review').kind='recall';return redrawStudy()}
  if(a==='study-knowledge-scope'){v.scope=el.dataset.value;v.offset=0}
  if(a==='study-knowledge-find'){v.query=$('#knowledge-query').value.trim();v.category=$('#knowledge-category').value;v.offset=0}
  if(a==='study-knowledge-clear'){v.query='';v.category='all';v.offset=0}
  if(a==='study-knowledge-prev'||a==='study-knowledge-next')v.offset=Math.max(0,v.offset+(a.endsWith('next')?20:-20));
  return redrawStudy();
};
document.addEventListener('change',e=>{
  const b=state.currentBook;if(!b)return;
  if(e.target.id==='teaching-topic'&&e.target.value){
    const u=b.teaching.units.find(x=>x.id===e.target.value);if(!u)return;
    teachingView(b).scope='section';teachingView(b).offset=0;
    routeTo({...state.route,section:u.sections[0],offset:0,record:null});
  }
  if(e.target.id==='knowledge-category'){teachingView(b).category=e.target.value;teachingView(b).offset=0;redrawStudy().catch(e=>toast(e.message))}
});
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.id==='knowledge-query'){e.preventDefault();act($('[data-action="study-knowledge-find"]')).catch(e=>toast(e.message))}});
// Newly expanded source formulas also get a typesetting pass.
document.addEventListener('toggle',e=>{if(e.target.open&&e.target.matches('.source-knowledge,.review-lesson,.problem-hint'))typeset(e.target)},true);
const priorTeachingLibrary=libraryHTML;
libraryHTML=function(){return priorTeachingLibrary().replace('r1 完整包 + r2 修订层','学习 r2 · 42 个主题 / 76 道配套题').replace('主动回忆 · 以教材核对','知识速查 · 按条件整理')};
window.__bookTest={...window.__bookTest,loadBook,teachingViews,teachingView,topicUnits,sourceReviewEntries,studyView};
// Learning UI starts boot after all extensions are installed.
