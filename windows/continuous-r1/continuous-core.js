/* Continuous document planning: pure functions, no source mutation, no I/O. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.BookContinuous = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const excluded = new Set(['whitespace','page_header','running_header','page_number','toc_ocr_evidence']);
  const visible = r => !!r && typeof r.id === 'string' && r.body_visible !== false && !excluded.has(r.type);
  const asText = value => typeof value === 'string' ? value : '';
  function recordText(r) {
    return [r.title,r.text,r.latex,...(r.parts || []).map(p=>typeof p==='string'?p:p.text||p.latex)].map(asText).join('\n');
  }
  function recordGroups(book, allowIds=null) {
    const byId = new Map((book.records || []).map(r=>[r.id,r]));
    const seen = new Set(), groups = [];
    function take(ids, section) {
      const records=[];
      for (const id of ids || []) {
        const r=byId.get(id);
        if (seen.has(id) || !visible(r) || (allowIds && !allowIds.has(id))) continue;
        seen.add(id); records.push(r);
      }
      if(records.length) groups.push({section, records});
    }
    for (const section of book.sections || []) take(section.record_ids, section);
    // Never silently omit visible records which are not registered in the TOC.
    take((book.records||[]).map(r=>r.id), {id:'__unassigned_records',title:'其他来源正文',record_ids:[]});
    return groups;
  }
  function paginate(groups, {maxRecords=24,maxCharacters=9000}={}) {
    if(!Number.isInteger(maxRecords)||maxRecords<1||!Number.isFinite(maxCharacters)||maxCharacters<1) throw Error('Invalid pagination bounds');
    const pages=[];
    for (const {section, records} of groups) {
      let chunk=[],size=0;
      function emit() {
        if(!chunk.length)return;
        pages.push({kind:'source',key:'source:'+section.id+':'+chunk[0].id,section,records:chunk,
          title:section.title||section.id,text:chunk.map(recordText).join('\n')});
        chunk=[];size=0;
      }
      for(const r of records) {
        const n=recordText(r).length;
        if(chunk.length && (chunk.length>=maxRecords || size+n>maxCharacters))emit();
        chunk.push(r);size+=n;
      }
      emit(); // A long record stays complete; it is NEVER sliced or ellipsized.
    }
    return pages;
  }
  function reviewIds(teaching) {
    const ids=new Set();
    for(const categories of Object.values(teaching?.review_by_section||{}))
      for(const list of Object.values(categories))for(const id of list)ids.add(id);
    return ids;
  }
  function buildPlan(book, mode, {indexOnly=false,layer='learning',practiceKind='solved'}={}) {
    const teaching=book.teaching||{units:[],solved:[]};
    let pages=[];
    if(mode==='learn' && indexOnly && layer!=='index') {
      pages=(book.translations||[]).map((t,i)=>({kind:'translation',key:'translation:'+i,translation:t,index:i,
        title:'中文学习层 · 第 '+(i+1)+' 批',text:t.text||'',section:null}));
    } else if(mode==='learn')pages=paginate(recordGroups(book));
    else if(mode==='preview'||mode==='review') {
      pages=(teaching.units||[]).map(u=>({kind:mode,key:mode+':'+u.id,unit:u,title:u.title,
        section:(book.sections||[]).find(s=>s.id===(u.sections||[])[0])||null,
        text:mode==='preview'?[u.title,u.preview.overview,...u.preview.prerequisites,...u.preview.goals,u.review.points[0]?.body].join('\n'):
          [u.title,...u.review.points.map(p=>p.title+'\n'+p.body),...u.review.method,...u.review.pitfalls].join('\n')}));
      if(mode==='review')pages.push(...paginate(recordGroups(book,reviewIds(teaching))));
    } else if(mode==='practice') {
      const questions=practiceKind==='source'?(book.study?.questions||[]):(teaching.solved||[]);
      const seen=new Set();
      pages=questions.filter(g=>{if(seen.has(g.id))return false;seen.add(g.id);return true;}).map(g=>({
        kind:g.origin==='authored_worked_problem'?'worked':'question',key:'question:'+g.id,question:g,
        section:(book.sections||[]).find(s=>s.id===g.section)||null,title:g.title||'教材题目',
        text:[g.title,g.stem,g.hint,...g.steps||[],g.answer,g.pitfall,...(g.record_ids||[]).map(id=>recordText((book.records||[]).find(r=>r.id===id)||{}))].map(asText).join('\n')
      }));
    } else throw Error('Unknown continuous mode: '+mode);
    return pages.map((p,index)=>({...p,index}));
  }
  function matches(pages,query) {
    const q=String(query||'').trim().toLocaleLowerCase();
    return q ? pages.filter(p=>(p.text||'').toLocaleLowerCase().includes(q)).map(p=>p.index) : [];
  }
  function normalizePosition(value, pages) {
    if(!value||typeof value!=='object'||typeof value.key!=='string')return null;
    const index=pages.findIndex(p=>p.key===value.key);
    if(index<0)return null;
    return {index,within:Number.isFinite(value.within)?Math.min(1,Math.max(0,value.within)):0};
  }
  return {visible,recordText,recordGroups,paginate,reviewIds,buildPlan,matches,normalizePosition};
});
