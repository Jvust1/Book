/* Explicit, two-stage sharing; tickets stay only in memory. No notes or answers are read. */
'use strict';
(() => {
  const P=window.BookSelectionProjection;
  let context=null,connected=false,connecting=false,revoking=false,choosing=false,generation=0,sequence=0;
  let draft=null,ticket=null,pending=null,sharing=null,sessionExpiry=0;
  const $=id=>document.getElementById(id);
  const uid=()=>crypto.randomUUID();
  function element(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
  function button(id,text,fn){const b=element('button',text);b.type='button';b.id=id;b.addEventListener('click',()=>Promise.resolve().then(fn).catch(fail));return b;}
  const box=element('section');box.id='book-companion';box.setAttribute('aria-label','mygpt 只读联调');
  const heading=element('div');heading.className='bridge-heading';heading.append(element('h2','Book × mygpt'),element('p','真实归档选段 · 只读 · TestModel 固定回复 · 非手机 APK 联通'));
  const actions=element('div');actions.className='bridge-actions';
  actions.append(button('bridge-connect','开启本次只读连接',connect),button('bridge-choose','选择一段',()=>{choosing=!choosing;decorate();update();}),button('bridge-revoke','撤销连接',revoke));
  const status=element('p','未连接。阅读和打开页面不会自动解释。');status.id='bridge-status';status.setAttribute('role','status');
  const panel=element('section');panel.id='bridge-selection-panel';panel.hidden=true;
  const label=element('label','导出层级 ');const layer=element('select');layer.id='bridge-layer';layer.setAttribute('aria-label','导出层级');label.append(layer);
  const representationLabel=element('label','正文表示 ');const representation=element('select');representation.id='bridge-representation';representation.setAttribute('aria-label','正文表示');
  for(const [value,text] of [['display','当前排版文字 / LaTeX'],['raw','原始文字 / LaTeX（可能不同于当前排版）']]){const o=element('option',text);o.value=value;representation.append(o);}representationLabel.append(representation);
  const preview=element('div');preview.id='bridge-preview';
  const controls=element('div');controls.className='bridge-actions';controls.append(button('bridge-share','确认只读交给 mygpt',share),button('bridge-explain','测试解释这段',explain),button('bridge-cancel','取消请求',cancel),button('bridge-clear','清除选段',()=>invalidate('手动清除')));
  panel.append(label,representationLabel,preview,controls);
  const reply=element('div');reply.id='bridge-reply';reply.hidden=true;reply.setAttribute('role','status');
  box.append(heading,actions,status,panel,reply);document.querySelector('header').after(box);document.body.classList.add('bridge-host');
  layer.addEventListener('change',()=>refreshDraft().catch(fail));representation.addEventListener('change',()=>refreshDraft().catch(fail));
  function say(text){status.textContent=text;}
  function fail(error){say('未完成：'+(error?.message||'未知错误')+'。没有自动重试或启用真实模型。');update();}
  async function request(action,body,options={}){
    const response=await fetch('/api/companion/'+action,{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json','X-Book-Companion':'1'},body:JSON.stringify(body),...options});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'REQUEST_FAILED');return data;
  }
  async function connect(){
    if(connected||connecting||revoking)return;const gen=generation;connecting=true;update();
    try{const data=await request('authorize',{});if(gen!==generation||document.hidden){await request('revoke',{}, {keepalive:true});return;}connected=true;sequence=data.session.last_sequence;sessionExpiry=data.session.expires_at_ms;say('本次只读连接已开启。先选择、核对层级，再明确交给 mygpt；不会导出笔记、作答或图片。');}
    finally{connecting=false;update();}
  }
  function invalidate(reason){
    generation++;draft=null;ticket=null;sharing=null;
    if(['navigation','leave','页面离开'].includes(reason)){context=null;decorate();}panel.hidden=true;reply.hidden=true;reply.textContent='';
    if(pending){const current=pending;pending=null;current.controller.abort();if(connected)request('cancel',{request_id:current.id},{keepalive:true}).catch(()=>{});}
    if(connected){const seq=++sequence;request('clear',{sequence:seq,request_id:uid()},{keepalive:true}).catch(error=>{if(connected&&seq===sequence)fail(error);});}
    if(connected)say('选段已失效：'+reason+'。需要重新选择并确认。');update();
  }
  async function revoke(){
    if(revoking)return;revoking=true;invalidate('撤销连接');choosing=false;const wasConnected=connected;connected=false;update();decorate();
    try{if(wasConnected)await request('revoke',{}, {keepalive:true});say('已撤销本次连接，旧选段和迟到回复不可重新使用。');}
    finally{revoking=false;update();}
  }
  function readonly(){
    for(const n of document.querySelectorAll('#notebook input,#notebook textarea,#notebook button,#content textarea,#content select.rating,#export-notes'))n.disabled=true;
    const notebook=$('notebook');if(notebook)notebook.hidden=true;
    for(const t of document.querySelectorAll('#content textarea'))t.placeholder='只读联调宿主：此处不读取或保存作答。';
    const desc=document.querySelector('.modes-description');
    if(desc&&!document.querySelector('#content .bridge-readonly-notice')){const note=element('p','当前是独立只读联调窗口。笔记、作答、自评和进度写入已禁用；原 Book 应用和数据库未被修改。');note.className='bridge-readonly-notice';desc.after(note);}
  }
  function rendered(value){context=value;readonly();decorate();update();}
  function decorate(){
    for(const old of document.querySelectorAll('.bridge-pick'))old.remove();
    if(!choosing||!connected||!context?.section)return;
    const index=new Map(context.section.records.map(r=>[r.id,r]));
    for(const article of document.querySelectorAll('#content .record[data-record-id]')){
      const r=index.get(article.dataset.recordId);if(!r)continue;
      if(!r.parts.some(p=>(p.text||p.latex||p.render_text||p.render_latex)) && P.choices(context.course,context.section,r).length===1)continue;
      const b=button('', '选择这段',()=>chooseRecord(r.id));b.removeAttribute('id');b.className='bridge-pick';b.dataset.bridgeRecord=r.id;article.prepend(b);
    }
    for(const article of document.querySelectorAll('#content .group-card[data-group-id]')){
      const g=context.section.practice_groups.find(x=>x.id===article.dataset.groupId);if(!g?.derived_guidance)continue;
      for(const [selector,portion,title] of [['details.guidance:not(.derived-solution)','hint','选择思路提示'],['details.derived-solution','solution','选择参考推导']]){
        const target=article.querySelector(selector);if(!target)continue;
        const b=button('',title,()=>chooseDerived(g,portion));b.removeAttribute('id');b.className='bridge-pick';b.dataset.bridgePortion=portion;target.append(b);
      }
    }
  }
  function base(recordId){const c=context.course,s=context.section;return {course_id:c.course_id,book_id:c.book_id,book_version_id:c.book_version_id,section_id:s.id,record_id:recordId,layer:'source',layer_id:null,portion:'body',representation:'display'};}
  async function chooseRecord(id){
    const saved=context;invalidate('重新选择');context=saved;
    const r=context.section.records.find(x=>x.id===id);if(!r)throw new Error('RECORD_NOT_FOUND');
    const options=P.choices(context.course,context.section,r);layer.replaceChildren();
    if(options.length>1){const placeholder=element('option','请选择要交给 mygpt 的内容层…');placeholder.value='';layer.append(placeholder);}
    for(const [i,opt] of options.entries()){const o=element('option',opt.label);o.value=String(i);layer.append(o);}layer.value=options.length===1?'0':'';representation.value='display';
    draft={base:base(id),options,payload:null,hash:null};panel.hidden=false;await refreshDraft();panel.scrollIntoView({block:'nearest'});layer.focus({preventScroll:true});
  }
  async function chooseDerived(g,portion){
    const saved=context;invalidate('重新选择');context=saved;
    const options=[{layer:'derived',layer_id:g.id,label:portion==='hint'?'AI 思路提示（非教材原文）':'AI 参考推导（非标准答案）'}];layer.replaceChildren();const o=element('option',options[0].label);o.value='0';layer.append(o);representation.value='display';
    draft={base:{...base(g.anchor_id),portion},options,payload:null,hash:null};panel.hidden=false;await refreshDraft();panel.scrollIntoView({block:'nearest'});
  }
  async function refreshDraft(){
    if(!draft)return;
    const saved=draft,ctx=context;generation++;const gen=generation;ticket=null;saved.hash=null;reply.hidden=true;
    if(pending)await cancel();
    if(connected)request('clear',{sequence:++sequence,request_id:uid()},{keepalive:true}).catch(()=>{});
    if(saved.options.length>1&&layer.value===''){
      saved.payload=null;preview.textContent='请选择具体来源层并核对预览；确认前不会共享。';
      say('多种来源层均可用。请先明确选择一层，再核对内容。');update();return;
    }
    const opt=saved.options[Number(layer.value)];const selected={...saved.base,layer:opt.layer,layer_id:opt.layer_id,representation:representation.value};
    update();const payload=await P.project(ctx.course,ctx.section,selected);const hash=await P.digest(payload);
    if(gen!==generation||draft!==saved)return;
    saved.payload=payload;saved.hash=hash;preview.textContent=opt.label+'\n'+payload.parts.map(p=>p.text??p.latex).join('\n');
    say('仅在本页预览，尚未导出。确认后只发送选段身份和哈希；正文由 Book 服务重新读取并校验。');update();
  }
  async function share(){
    if(!connected||!draft?.hash||sharing||ticket||pending)return;const gen=generation,saved=draft;const seq=++sequence;
    const operation={gen,seq};sharing=operation;update();
    try{const result=await request('select',{selection:saved.payload.selection,expected_sha256:saved.hash,sequence:seq,request_id:uid()});
      if(gen!==generation||draft!==saved)return;ticket=result;say('选段身份已核验，当前层级：'+saved.options[Number(layer.value)].label+'。只有点击测试解释才调用 TestModel。');}
    finally{if(sharing===operation)sharing=null;update();}
  }
  async function explain(){
    if(!ticket||pending||!connected||Date.now()>=ticket.expires_at_ms)return;
    const gen=generation,selected=ticket,id=uid(),controller=new AbortController();pending={id,controller};reply.hidden=true;say('正在进行本机 TestModel 联调，可取消。');update();
    try{const result=await request('explain',{ticket:selected,request_id:id},{signal:controller.signal});
      if(gen!==generation||pending?.id!==id||ticket!==selected||document.hidden)return;
      if(result.context.selection.record_id!==selected.selection.record_id||result.context.epoch!==selected.epoch||Date.now()>=selected.expires_at_ms)throw new Error('LATE_OR_MISMATCHED_REPLY');
      reply.textContent=result.reply.text;reply.hidden=false;say('本次联调完成。真实 Book 选段已进入 mygpt 接收端；付费模型调用为 0。');
    }catch(error){if(gen===generation&&pending?.id===id&&error.name!=='AbortError')fail(error);}
    finally{if(pending?.id===id)pending=null;update();}
  }
  async function cancel(){
    if(!pending)return;const current=pending;pending=null;current.controller.abort();reply.hidden=true;
    if(connected)await request('cancel',{request_id:current.id});say('本次请求已取消，迟到回复不会显示。');update();
  }
  function update(){
    $('bridge-connect').disabled=connected||connecting||revoking;$('bridge-choose').disabled=!connected||!context?.section;$('bridge-revoke').disabled=!connected||revoking;
    $('bridge-choose').textContent=choosing?'收起选段按钮':'选择一段';$('bridge-choose').setAttribute('aria-pressed',String(choosing));
    $('bridge-share').disabled=!connected||!draft?.hash||!!ticket||!!pending||!!sharing;
    $('bridge-explain').disabled=!connected||!ticket||!!pending||Date.now()>=ticket.expires_at_ms;
    $('bridge-cancel').disabled=!pending;
  }
  window.addEventListener('pagehide',()=>{const active=connected;invalidate('页面离开');if(active)request('revoke',{}, {keepalive:true}).catch(()=>{});connected=false;});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)invalidate('页面隐藏');});
  setInterval(()=>{if(connected&&Date.now()>=sessionExpiry){invalidate('会话过期');connected=false;choosing=false;decorate();say('只读连接已过期，需要重新明确开启。');}else if(ticket&&Date.now()>=ticket.expires_at_ms)invalidate('选段过期');update();},500);
  Object.defineProperty(window,'BookCompanionBridge',{value:Object.freeze({invalidate,rendered}),writable:false,configurable:false});
  update();
})();
