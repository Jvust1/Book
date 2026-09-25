/* Browser-side independent projection. No network, storage, learner state or model. */
'use strict';
(() => {
  const ID=/^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$/;
  const RID=/^[A-Za-z0-9][A-Za-z0-9_.'-]{0,159}$/;
  const VERSION=/^[A-Za-z0-9][A-Za-z0-9_.@-]{0,159}$/;
  const fields=['course_id','book_id','book_version_id','section_id','record_id','layer','layer_id','portion','representation'];
  function need(ok,code){if(!ok)throw new Error(code);}
  function exact(re,x){return typeof x==='string'&&re.exec(x)?.[0]===x;}
  function plain(x){return x!==null&&typeof x==='object'&&!Array.isArray(x);}
  function string(x,max=12000){need(typeof x==='string'&&Array.from(x).length<=max,'INVALID_OR_OVERSIZED_TEXT');need(!Array.from(x).some(c=>c.codePointAt(0)>=0xD800&&c.codePointAt(0)<=0xDFFF),'INVALID_UNICODE');return x;}
  function canonical(value){
    function sort(x){
      if(Array.isArray(x))return x.map(sort);
      if(plain(x)){const out=Object.create(null);for(const k of Object.keys(x).sort())out[k]=sort(x[k]);return out;}
      need(x===null||typeof x==='boolean'||typeof x==='string'||(typeof x==='number'&&Number.isFinite(x)),'INVALID_JSON');return x;
    }
    return JSON.stringify(sort(value));
  }
  async function digest(value){
    const bytes=new TextEncoder().encode(canonical(value));
    const result=await globalThis.crypto.subtle.digest('SHA-256',bytes);
    return Array.from(new Uint8Array(result),x=>x.toString(16).padStart(2,'0')).join('');
  }
  function selection(x){
    need(plain(x)&&canonical(Object.keys(x).sort())===canonical([...fields].sort()),'INVALID_SELECTION_FIELDS');
    for(const f of ['course_id','book_id','section_id'])need(exact(ID,x[f]),'INVALID_IDENTIFIER');
    need(exact(VERSION,x.book_version_id),'INVALID_IDENTIFIER');
    need(exact(RID,x.record_id),'INVALID_RECORD_IDENTIFIER');
    need(['source','completion','correction','derived'].includes(x.layer),'INVALID_LAYER');
    need(['raw','display'].includes(x.representation),'INVALID_REPRESENTATION');
    if(x.layer==='source')need(x.layer_id===null,'SOURCE_LAYER_ID_FORBIDDEN');
    else need(exact(RID,x.layer_id),'INVALID_RECORD_IDENTIFIER');
    need((x.layer==='derived'?['hint','solution']:['body']).includes(x.portion),'INVALID_PORTION');
    return Object.fromEntries(fields.map(k=>[k,x[k]]));
  }
  function parts(value,representation){
    need(Array.isArray(value)&&value.length<=512,'INVALID_OR_OVERSIZED_PARTS');
    const out=[];let excluded=false,characters=0;
    for(const p of value){
      need(plain(p),'INVALID_PART');let item;
      if(p.kind==='text'){
        const raw=string(p.text);item=representation==='display'&&Object.hasOwn(p,'render_text')?string(p.render_text):raw;
        out.push({kind:'text',text:item});
      }else if(p.kind==='math'){
        const raw=string(p.latex);item=representation==='display'?string(p.render_latex||raw):raw;
        need(p.display===undefined||typeof p.display==='boolean','INVALID_MATH_DISPLAY');
        out.push({kind:'math',latex:item,display:p.display??false});
      }else{excluded=true;continue;}
      characters+=Array.from(item).length;need(characters<=12000,'SELECTION_TOO_LARGE');
    }
    return {parts:out,excluded};
  }
  function corrections(r,m,s){
    const cs=r.corrections||[];need(Array.isArray(cs)&&cs.length<=64,'INVALID_CORRECTIONS');
    return cs.filter(c=>plain(c)&&c.record_id===r.id&&c.course_id===m.course_id&&c.section_id===s.id&&
      c.confidence==='HIGH'&&c.presentation==='prefer_corrected'&&c.status==='CHECKED_BY_ASSISTANT'&&
      c.evidence_status==='SCOPED_EVIDENCE_CHECKED'&&c.source_preserved===true&&Array.isArray(c.check_ids)&&
      c.check_ids.length>0&&c.check_ids.length<=64&&c.check_ids.every(x=>typeof x==='string'&&Array.from(x).length>0&&Array.from(x).length<=200)&&
      c.original_title===r.title&&canonical(c.original_parts??null)===canonical(r.parts??null)&&Array.isArray(c.corrected_parts)&&c.corrected_parts.length>0);
  }
  function choices(m,s,r){
    const out=[{layer:'source',layer_id:null,label:'原始转录正文'}];
    if(r.source_completion)out.push({layer:'completion',layer_id:r.source_completion.id,label:'原页补录正文（待独立复核）'});
    const cs=corrections(r,m,s);
    if(cs.length===1)out.push({layer:'correction',layer_id:cs[0].id,label:'AI 校正正文（非官方勘误）'});
    return out;
  }
  async function project(m,s,input){
    const selected=selection(input);need(plain(m)&&plain(s),'INVALID_SOURCE');
    for(const k of ['course_id','book_id','book_version_id'])need(m[k]===selected[k],'SOURCE_VERSION_MISMATCH');
    need(s.id===selected.section_id,'SOURCE_SECTION_MISMATCH');
    need(s.book_version_id===undefined||s.book_version_id===selected.book_version_id,'SOURCE_VERSION_MISMATCH');
    need(Array.isArray(m.sections)&&m.sections.some(x=>x.id===selected.section_id),'SECTION_NOT_IN_MANIFEST');
    need(Array.isArray(s.records)&&s.records.length<=20000,'INVALID_RECORDS');const index=new Map();
    for(const r of s.records){need(plain(r)&&exact(RID,r.id),'INVALID_RECORD_IDENTIFIER');need(!index.has(r.id),'DUPLICATE_RECORD_ID');need(r.section_id===s.id,'RECORD_SECTION_MISMATCH');index.set(r.id,r);}
    const r=index.get(selected.record_id);need(r,'RECORD_NOT_FOUND');
    let chosen=r.parts,parentIds=[r.id],title=string(r.title||'',1000),origin='SOURCE_TRANSCRIPTION_NOT_INDEPENDENTLY_CERTIFIED';const warnings=[];
    if(selected.layer==='source'){
      if(r.source_completion||corrections(r,m,s).length)warnings.push('RAW_SOURCE_LAYER_MAY_DIFFER_FROM_DEFAULT_READER_BODY');
    }else if(selected.layer==='completion'){
      const c=r.source_completion;need(plain(c)&&c.id===selected.layer_id,'COMPLETION_NOT_FOUND');
      need(c.origin==='source_visual_transcription_not_generated_proof','COMPLETION_ORIGIN_MISMATCH');chosen=c.parts;origin='SOURCE_COMPLETION_TRANSCRIPTION_NOT_INDEPENDENTLY_CERTIFIED';
    }else if(selected.layer==='correction'){
      const cs=corrections(r,m,s);need(cs.length===1&&cs[0].id===selected.layer_id,'CORRECTION_NOT_UNIQUELY_ELIGIBLE');chosen=cs[0].corrected_parts;origin='AI_CORRECTION_NOT_TEXTBOOK_NOT_OFFICIAL_ERRATUM';
    }else{
      const groups=s.practice_groups||[];need(Array.isArray(groups)&&groups.length<=20000,'INVALID_GROUPS');
      const matches=groups.filter(g=>plain(g)&&g.id===selected.layer_id);need(matches.length===1,'DERIVED_GROUP_NOT_UNIQUE');const g=matches[0];
      need(g.anchor_id===r.id,'DERIVED_ANCHOR_MISMATCH');parentIds=g.record_ids;
      need(Array.isArray(parentIds)&&parentIds.length>0&&parentIds.length<=32&&parentIds.every(x=>typeof x==='string'&&index.has(x))&&new Set(parentIds).size===parentIds.length&&parentIds.includes(r.id),'DERIVED_SOURCE_CLOSURE');
      const guide=g.derived_guidance;need(plain(guide)&&guide.textbook_official_solution===false&&canonical(guide.source_record_ids??null)===canonical(parentIds),'DERIVED_GUIDANCE_IDENTITY');
      const known=new Set(m.sections.map(x=>x.id));
      need(Array.isArray(guide.source_sections)&&guide.source_sections.length>0&&guide.source_sections.length<=32&&guide.source_sections.every(x=>typeof x==='string'&&known.has(x)),'DERIVED_SECTION_CLOSURE');
      chosen=guide[selected.portion+'_parts'];title=string(g.title||'',1000);origin='AI_DERIVED_NOT_TEXTBOOK_NOT_OFFICIAL_SOLUTION';
    }
    const p=parts(chosen,selected.representation);need(p.parts.length&&p.parts.some(x=>(x.text??x.latex).trim()),'EMPTY_BODY');
    if(p.excluded)warnings.push('NON_TEXT_PARTS_EXCLUDED');const parents=[];
    for(const rid of parentIds)parents.push({record_id:rid,source_parts_sha256:await digest(parts(index.get(rid).parts,'raw').parts)});
    const payload={schema:'book.selected-content.v1',selection:selected,title,parts:p.parts,origin,parent_sources:parents,warnings,
      qualification:'BODY_ONLY_NO_IMAGES_NO_NOTES_NO_ANSWERS;INDEPENDENT_REVIEW_PENDING'};
    need(new TextEncoder().encode(canonical(payload)).length<=64000,'SELECTION_TOO_LARGE');return payload;
  }
  const api=Object.freeze({canonical,digest,selection,parts,corrections,choices,project});
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else Object.defineProperty(globalThis,'BookSelectionProjection',{value:api,writable:false,configurable:false});
})();
