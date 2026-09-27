/* Pure deterministic lesson selection and self-assessment summaries. No external I/O. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.BookTeachingRelease=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 function hash(text){let h=2166136261;for(const c of String(text)){h^=c.codePointAt(0);h=Math.imul(h,16777619)}return h>>>0}
 function selectExam(units,problems,limit=20,seed=''){
  if(!Array.isArray(units)||!Array.isArray(problems))throw Error('Invalid teaching arrays');
  if(!Number.isInteger(limit)||limit<1||limit>50)throw Error('Question limit must be 1–50');
  const valid=problems.filter(p=>p&&typeof p.id==='string'&&p.origin==='authored_worked_problem'&&typeof p.stem==='string'&&p.stem.trim()&&typeof p.answer==='string'&&p.answer.trim()&&Array.isArray(p.steps)&&p.steps.length>=2);
  const byid=new Map(valid.map(p=>[p.id,p]));const used=new Set();
  // Shuffle topics first and then round-robin. Ten questions cannot all come from one two-question topic.
  const ordered=units.slice().sort((a,b)=>hash(seed+'|unit|'+a.id)-hash(seed+'|unit|'+b.id)||a.id.localeCompare(b.id));
  const buckets=ordered.map(u=>(u.problem_ids||[]).filter(id=>byid.has(id)).sort((a,b)=>hash(seed+'|question|'+a)-hash(seed+'|question|'+b)||a.localeCompare(b)));
  const selected=[];let round=0;
  while(selected.length<limit){let progressed=false;for(const bucket of buckets){const id=bucket[round];if(id&&!used.has(id)){used.add(id);selected.push(byid.get(id));progressed=true;if(selected.length===limit)break}}if(!progressed&&buckets.every(b=>round>=b.length-1))break;round++}
  return selected;
 }
 function summarize(session){
  const queue=[...new Set(session?.queue||[])],results=session?.results||{};let wrong=0,review=0,understood=0;
  for(const id of queue){if(results[id]===0)wrong++;else if(results[id]===1)review++;else if(results[id]===2)understood++}
  const answered=wrong+review+understood;
  return {total:queue.length,answered,unrated:queue.length-answered,wrong,review,understood,self_assessment:true};
 }
 function topicProgress(unit,cards,bid){return summarize({queue:unit.problem_ids||[],results:Object.fromEntries((unit.problem_ids||[]).map(id=>[id,cards?.[bid+'::'+id]?.rating]))})}
 return {hash,selectExam,summarize,topicProgress};
});
