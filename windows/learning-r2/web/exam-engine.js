/* Local self-assessment practice, not a secure/proctored exam or auto-grader. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./study-engine.js'):root.BookStudy);if(typeof module==='object'&&module.exports)module.exports=api;else root.BookExam=api;})(globalThis,function(ST){
  'use strict';
  const MODES=['quick','wrong','chapter'];
  function ready(q){return q.origin!=='index_lookup'&&!!((q.steps?.length&&q.answer)||(q.worked_solution?.steps?.length&&q.worked_solution.answer));}
  function priority(c,now){return c?.rating===0?0:c?.rating===1?1:Number.isFinite(c?.due)&&c.due<=now?2:c?.rating===undefined?3:4;}
  function select(qs,cards,bid,mode,chapter,limit=10,now=Date.now()){
    if(!MODES.includes(mode)||!Number.isFinite(limit)||limit<1)throw Error('考试选项无效');
    const seen=new Set();let list=qs.filter(q=>ready(q)&&!seen.has(q.id)&&seen.add(q.id));
    if(mode==='chapter')list=list.filter(q=>(q.chapter_ids||[]).includes(chapter));
    if(mode==='wrong')list=list.filter(q=>[0,1].includes(cards[bid+'::'+q.id]?.rating));
    if(mode!=='chapter')list.sort((a,b)=>priority(cards[bid+'::'+a.id],now)-priority(cards[bid+'::'+b.id],now));
    return list.slice(0,Math.min(50,Math.floor(limit)));
  }
  function create(ids,id,now,mode,chapter,minutes=20){
    if(!MODES.includes(mode)||!ids.length||!Number.isFinite(now)||!Number.isFinite(minutes)||minutes<1||minutes>180)throw Error('考试会话参数无效');
    return {...ST.makeSession(ids,id,now,false,50),mode:'practice',exam:{kind:mode,chapter_id:chapter||'',feedback:mode==='chapter'?'after_submit':'immediate',deadline:mode==='chapter'?now+minutes*60000:null},submitted_at:null};
  }
  function expired(s,now=Date.now()){return !!s.exam&&s.submitted_at===null&&Number.isFinite(s.exam.deadline)&&now>=s.exam.deadline;}
  function canReveal(s){return !s.exam||s.exam.feedback!=='after_submit'||s.submitted_at!==null;}
  function submit(s,now=Date.now()){
    if(!s.exam||s.submitted_at!==null)return s;
    s.submitted_at=now;s.submitted_answers={...s.drafts};s.unanswered=s.queue.filter(id=>!String(s.drafts[id]||'').trim()).length;s.updated_at=now;s.index=0;s.status='active';return s;
  }
  return {ready,select,priority,create,expired,canReveal,submit};
});
