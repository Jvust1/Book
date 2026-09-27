/* Book study workflow. Pure state transitions; no network or textbook synthesis. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BookStudy = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const DAY = 86400000;
  const clone = v => JSON.parse(JSON.stringify(v));
  const obj = v => v !== null && typeof v === 'object' && !Array.isArray(v);
  const stable = v => Array.isArray(v) ? '['+v.map(stable).join(',')+']' : obj(v) ? '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}' : JSON.stringify(v);
  function personalBook(state, bid) {
    const b = state.books[bid] || (state.books[bid] = {});
    const st = b.study || (b.study = {});
    st.previews ||= {}; st.sessions ||= {}; st.sessionHistory ||= [];
    return st;
  }
  function makeSession(ids, id, now, random=false, limit=20) {
    const queue=[...new Set(ids)];
    if (random) { // deterministic local shuffle; not a randomized experiment.
      let seed=2166136261;
      for (const c of id) seed=Math.imul(seed^c.charCodeAt(0),16777619)>>>0;
      for(let i=queue.length-1;i>0;i--) {seed=(Math.imul(seed,1664525)+1013904223)>>>0;const j=seed%(i+1);[queue[i],queue[j]]=[queue[j],queue[i]];}
    }
    return {id,queue:queue.slice(0,Math.max(1,Math.min(50,limit))),index:0,started_at:now,updated_at:now,status:'active',drafts:{},results:{},revealed:{}};
  }
  function rating(old, value, now) {
    if(![0,1,2].includes(value)||!Number.isFinite(now)) throw Error('自评参数不正确');
    const days=value===0?0:value===1?1:Math.min(120,Math.max(3,(Number(old.interval)||1)*2));
    return {rating:value,wrong:value===0,interval:days,due:now+(value===0?10*60000:days*DAY),self_assessment:true,updated_at:new Date(now).toISOString()};
  }
  function recordAttempt(state, bid, group, answer, value, attemptId, now, sessionId=null) {
    const key=bid+'::'+group.id,old=state.cards[key]||{};
    const attempts=[...(old.attempts||[])];
    if(attempts.some(a=>a.id===attemptId))return old;
    attempts.push({id:attemptId,answer,rating:value,self_assessment:true,at:new Date(now).toISOString(),session_id:sessionId});
    const card={...old,...rating(old,value,now),book_id:bid,record_id:group.anchor_id||group.record_ids[0]||'',group_id:group.id,origin:group.origin,answer,attempts};
    state.cards[key]=card;return card;
  }
  function groups(study, kind, section, scope, cards, bid, now=Date.now()) {
    let list=kind==='solved'?(study.solved||[]):kind==='source'?study.questions:kind==='lookup'?study.lookups:study.recalls;
    if(scope==='due'||scope==='wrong')list=[...(study.solved||[]),...study.questions,...study.recalls];
    const seen=new Set();list=list.filter(g=>{if(seen.has(g.id))return false;seen.add(g.id);return true});
    if(scope==='section')list=list.filter(g=>g.section===section||(g.section_ids||[]).includes(section));
    if(scope==='due')list=list.filter(g=>Number.isFinite(cards[bid+'::'+g.id]?.due)&&cards[bid+'::'+g.id].due<=now);
    if(scope==='wrong')list=list.filter(g=>cards[bid+'::'+g.id]?.wrong===true);
    if(scope==='unseen')list=list.filter(g=>cards[bid+'::'+g.id]?.rating===undefined);
    if(scope==='due')list.sort((a,b)=>cards[bid+'::'+a.id].due-cards[bid+'::'+b.id].due);
    return list;
  }
  function validate(state, allowedBooks=null) {
    if(!obj(state)||state.schema!=='book-personal-state-v1')throw Error('不是 Book 的学习数据');
    for(const k of ['settings','books','notes','bookmarks','cards'])if(!obj(state[k]))throw Error('备份字段格式不正确：'+k);
    if(Object.keys(state).some(k=>!['schema','settings','books','notes','bookmarks','cards'].includes(k)))throw Error('备份含未支持的顶层字段');
    function walk(v,d=0) {if(d>20)throw Error('备份嵌套过深');if(v&&typeof v==='object')for(const[k,x]of Object.entries(v)){if(['__proto__','constructor','prototype'].includes(k))throw Error('备份含不安全字段');walk(x,d+1)}}
    walk(state);
    for(const [bid,v]of Object.entries(state.books)) {
      if(!obj(v))throw Error('教材学习状态不正确');
      if(allowedBooks&&!allowedBooks.includes(bid))throw Error('备份含本版未收录的教材');
      if(v.study!==undefined) {
        if(!obj(v.study))throw Error('学习流程状态不正确');
        for(const k of ['previews','sessions'])if(v.study[k]!==undefined&&!obj(v.study[k]))throw Error('学习流程字段不正确');
        if(v.study.sessionHistory!==undefined&&!Array.isArray(v.study.sessionHistory))throw Error('历史练习格式不正确');
        for(const s of [...Object.values(v.study.sessions||{}),...(v.study.sessionHistory||[])]) {
          if(!obj(s)||typeof s.id!=='string'||!Array.isArray(s.queue)||s.queue.length>50||s.queue.some(x=>typeof x!=='string')||!Number.isInteger(s.index)||s.index<0||s.index>s.queue.length||!obj(s.drafts)||!obj(s.results)||!obj(s.revealed))throw Error('练习会话格式不正确');
          if(Object.values(s.drafts).some(x=>typeof x!=='string')||Object.values(s.results).some(x=>![0,1,2].includes(x))||Object.values(s.revealed).some(x=>typeof x!=='boolean')||!['active','paused','finished'].includes(s.status))throw Error('练习会话字段内容不正确');
          if(s.exam!==undefined){
            const e=s.exam;
            if(!obj(e)||!['quick','wrong','chapter'].includes(e.kind)||typeof e.chapter_id!=='string'||!['immediate','after_submit'].includes(e.feedback)||e.feedback!==(e.kind==='chapter'?'after_submit':'immediate')||!(e.deadline===null||Number.isFinite(e.deadline))||e.kind==='chapter'&&!Number.isFinite(e.deadline)||!(s.submitted_at===null||Number.isFinite(s.submitted_at)))throw Error('考试会话格式不正确');
            if(s.submitted_at!==null&&(!obj(s.submitted_answers)||Object.values(s.submitted_answers).some(x=>typeof x!=='string')||!Number.isInteger(s.unanswered)||s.unanswered<0||s.unanswered>s.queue.length))throw Error('交卷记录不正确');
          }
        }
        for(const p of Object.values(v.study.previews||{}))if(!obj(p)||p.note!==undefined&&typeof p.note!=='string'||p.checked!==undefined&&!obj(p.checked))throw Error('预习记录格式不正确');
      }
    }
    for(const k of ['notes','bookmarks','cards'])for(const v of Object.values(state[k])){
      if(!obj(v))throw Error('学习条目格式不正确');
      for(const f of ['text','answer','book_id','record_id'])if(v[f]!==undefined&&typeof v[f]!=='string')throw Error('学习条目文本格式不正确');
      if(v.rating!==undefined&&![0,1,2].includes(v.rating))throw Error('自评字段不正确');
      if(v.attempts!==undefined&&(!Array.isArray(v.attempts)||v.attempts.some(a=>!obj(a)||typeof a.id!=='string'||typeof a.answer!=='string'||![0,1,2].includes(a.rating))))throw Error('答题历史格式不正确');
    }
    if(new TextEncoder().encode(JSON.stringify(state)).length>5*1024*1024)throw Error('学习数据超过 5 MB，请先导出备份');
    return state;
  }
  function preserveNote(s,key,value) {
    // Compare actual values, not a lossy hash. Reimporting is idempotent.
    const equal=n=>n.book_id===value.book_id&&n.record_id===value.record_id&&n.text===value.text;
    if(Object.values(s.notes).some(equal))return;
    let dest=key,n=1;while(Object.hasOwn(s.notes,dest))dest=key+'::import-'+n++;
    s.notes[dest]=clone(value);
  }
  function merge(local, incoming) {
    validate(local);validate(incoming);const s=clone(local),p=incoming;
    for(const[id,v]of Object.entries(p.notes))preserveNote(s,id,v);
    for(const[id,v]of Object.entries(p.bookmarks))if(!Object.hasOwn(s.bookmarks,id))s.bookmarks[id]=clone(v);
    for(const[id,v]of Object.entries(p.cards)) {
      if(!Object.hasOwn(s.cards,id)){s.cards[id]=clone(v);continue}
      const dst=s.cards[id];
      if(v.answer&&v.answer!==dst.answer)preserveNote(s,id+'::import-answer',{book_id:v.book_id||id.split('::')[0],record_id:v.record_id||'',text:'导入的作答副本：\n'+v.answer,updated_at:v.updated_at||''});
      const merged=[...(dst.attempts||[])];
      for(const a of v.attempts||[]) {
        if(merged.some(x=>stable(x)===stable(a)))continue;
        if(merged.some(x=>x.id===a.id)) {
          let n=1,id=a.id+'::import-'+n;while(merged.some(x=>x.id===id))id=a.id+'::import-'+ ++n;
          const aa={...clone(a),id,imported_original_id:a.id};
          if(!merged.some(x=>x.imported_original_id===a.id&&x.answer===a.answer&&x.rating===a.rating&&x.at===a.at))merged.push(aa);
        }else merged.push(clone(a));
      }
      if(merged.length)dst.attempts=merged;
    }
    for(const[bid,v]of Object.entries(p.books)) {
      if(!Object.hasOwn(s.books,bid)){s.books[bid]=clone(v);continue}
      if(!v.study)continue;
      const st=personalBook(s,bid);
      for(const[sid,pv]of Object.entries(v.study.previews||{})) {
        if(!st.previews[sid]){st.previews[sid]=clone(pv);continue}
        const cur=st.previews[sid];cur.checked={...(pv.checked||{}),...(cur.checked||{})};
        if(pv.note&&pv.note!==cur.note)preserveNote(s,bid+'::preview-'+sid,{book_id:bid,record_id:pv.anchor_id||'',text:'导入的预习笔记：\n'+pv.note,updated_at:pv.updated_at||''});
      }
      for(const[mode,ss]of Object.entries(v.study.sessions||{})) {
        if(!st.sessions[mode])st.sessions[mode]=clone(ss);
        else if(stable(st.sessions[mode])!==stable(ss)&&!st.sessionHistory.some(h=>stable(h)===stable(ss)))st.sessionHistory.push(clone(ss));
      }
      for(const ss of v.study.sessionHistory||[])if(!st.sessionHistory.some(h=>stable(h)===stable(ss)))st.sessionHistory.push(clone(ss));
    }
    return validate(s);
  }
  return {clone,stable,personalBook,makeSession,rating,recordAttempt,groups,validate,merge};
});
