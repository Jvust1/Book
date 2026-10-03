/* Book 1.3 document reader. Source is immutable; personal state uses the existing CAS store. */
'use strict';
(() => {
const $=id=>document.getElementById(id), $$=(q,root=document)=>Array.from(root.querySelectorAll(q));
const MODES={preview:'预习',learn:'学习',review:'复习',practice:'刷题'};
const MODE_GUIDES={
 preview:{kicker:'10–20 分钟',title:'先搭骨架，再进入正文。',text:'只抓本章要解决的问题、路线图、核心概念和关键公式；读完用自检确认你知道“接下来学什么”。',primary:'开始学习',secondary:'跳到预习自检'},
 learn:{kicker:'连续正文',title:'按教材顺序完整学习。',text:'保持正文连贯，公式、例题与图表跟随内容推进；来源与技术说明留在审计层，不打断阅读。',primary:'进入复习',secondary:'沉浸阅读'},
 review:{kicker:'考试复习',title:'把知识压缩成可回忆结构。',text:'先主动回忆定义、定理、公式与条件，再展开正文核对；最后进入刷题验证。',primary:'开始刷题',secondary:'开启主动回忆'},
 practice:{kicker:'教材原题',title:'先独立作答，再核对参考解答。',text:'答案默认折叠；点击“参考解答”只展开本题。草稿与掌握状态保存在本机。',primary:'打开作答面板',secondary:'下一题'}
};
const clampFontSize=value=>Math.max(10,Math.min(20,Number(value)||18));
const DEFAULTS={size:18,leading:1.62,margin:20,font:'shusong',layout:'continuous',theme:'light',zoom:'fit',cleanReading:true};
const FONT_STACKS={
 shusong:'\"FZShuSong-Z01\",\"FZShuSong-Z01S\",\"方正书宋_GBK\",\"方正书宋简体\",\"书宋\",\"Songti SC\",\"STSong\",\"SimSun\",\"Noto Serif CJK SC\",\"Source Han Serif SC\",serif',
 songti:'\"SimSun\",\"宋体\",\"NSimSun\",\"新宋体\",\"Songti SC\",\"STSong\",\"Noto Serif CJK SC\",serif',
 sourcehan:'\"Source Han Serif SC\",\"Noto Serif CJK SC\",\"思源宋体 CN\",serif',
 sans:'\"Microsoft YaHei UI\",\"Microsoft YaHei\",\"Noto Sans CJK SC\",sans-serif',
 custom:'\"BookLocalFont\",\"FZShuSong-Z01\",\"SimSun\",serif'
};
const SHUSONG_CANDIDATES=['FZShuSong-Z01','FZShuSong-Z01S','方正书宋_GBK','方正书宋简体','书宋','Songti SC','STSong','SimSun'];
let detectedFace=null,customFace=null,fullscreenPriorImmersive=null,printing=false,searchReflow=false,reflowAnchor=null;
let state=null,revision=0,token='',library=null,book=null,chapter=null,current=null,contentPackage=null;
let prefs={...DEFAULTS},saveQueue=Promise.resolve(),savePending=0,renderToken=0,loadingController=null,selected=null,editorBlock=null,searchHits=[],searchIndex=-1,notesTab='notes',answersHidden=false;
let revealedAnswers=new Set(),reviewRecall=false,revealedReviewSections=new Set(),practiceCursor=1;
const cache=new Map(),historyKeys=new Set();let failedMutations=[];let busy=false,positionTimer=null,reflowTimer=null,toastTimer=null,navigationRequest=0;
const mm=x=>x*96/25.4, clone=x=>structuredClone(x);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s??'').replace(/\s/g,'');
function toast(t){$('toast').textContent=t;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),4500);}
function status(t,failed=false){$('save-state').textContent=t;$('save-state').classList.toggle('failed',failed);}
function messageError(e){console.error(e);status('未保存 · 请导出备份',true);toast(String(e.message||e));}
async function readJSON(url,options){const r=await fetch(url,{cache:'no-store',...options});if(!r.ok)throw new Error('无法读取 '+url+'（'+r.status+'）');return r.json();}
async function session(){const s=await readJSON('/api/session');if(!s.state||s.state.schema!=='book-personal-state-v1')throw new Error('本机学习记录格式不正确，未覆盖。');state=s.state;revision=s.revision;token=s.token;return s;}
function formatBytes(n){n=Number(n)||0;if(n<1024)return n+' B';if(n<1024**2)return (n/1024).toFixed(1)+' KiB';if(n<1024**3)return (n/1024**2).toFixed(1)+' MiB';return (n/1024**3).toFixed(2)+' GiB';}
function renderContentPackageSummary(){
 const el=$('content-package-summary');if(!el)return;
 if(!contentPackage?.available){el.innerHTML='<div class="content-package-empty"><strong>尚未安装教材内容包</strong><span>'+escape(contentPackage?.error||'程序壳可以独立启动，安装内容包后书架才会出现。')+'</span></div>';return;}
 el.innerHTML='<dl><div><dt>内容版本</dt><dd>'+escape(contentPackage.content_version||'')+'</dd></div><div><dt>包 ID</dt><dd>'+escape(contentPackage.package_id||'')+'</dd></div><div><dt>教材 / 文档</dt><dd>'+escape(contentPackage.reader_books)+' 本 · '+escape(contentPackage.reader_documents)+' 份</dd></div><div><dt>大小</dt><dd>'+formatBytes(contentPackage.bytes)+'</dd></div><div><dt>SHA-256</dt><dd><code>'+escape((contentPackage.sha256||'').slice(0,16))+'…</code></dd></div><div><dt>来源</dt><dd>'+escape(contentPackage.source||'')+'</dd></div></dl>';
}
function showContentMissing(info=contentPackage){contentPackage=info||{available:false};$('content-missing').hidden=false;$('welcome').hidden=true;$('workspace').hidden=true;$('book-list').replaceChildren();$('chapter-list').replaceChildren();$('legacy-link').setAttribute('aria-disabled','true');$('legacy-link').onclick=e=>{e.preventDefault();openContentPackageDialog();};renderContentPackageSummary();status('等待教材内容包');}
async function refreshContentPackageStatus(){renderContentPackageSummary();return contentPackage;}
async function loadLibraryFromContent(){
 ++navigationRequest;++renderToken;busy=false;clearTimeout(positionTimer);cache.clear();contentAudit=null;library=await readJSON('/documents/catalog.json');if(!library||library.books.length!==6)throw Error('六本书的文档目录不完整。');
 current=null;book=null;chapter=null;selected=null;editorBlock=null;$('pages').replaceChildren();$('workspace').hidden=true;$('content-missing').hidden=true;$('welcome').hidden=false;$('legacy-link').removeAttribute('aria-disabled');$('legacy-link').onclick=null;renderNav();renderShelf();return library;
}
function openContentPackageDialog(){renderContentPackageSummary();$('content-package-dialog').showModal();}
async function reloadContentPackage(){
 if($('edit-dialog').open||$('note-text').value.trim()){toast('先保存个人编辑或批注，再更新教材。');return;}await savePosition();await saveQueue;
 const b=$('content-reload');b.disabled=true;$('content-upload-text').textContent='正在重新读取已安装内容…';
 try{const r=await fetch('/api/content/reload',{method:'POST',headers:{'X-Book-Token':token}});let data={};try{data=await r.json();}catch{}if(!r.ok)throw Error(data.error||'重新加载失败');contentPackage=data;await loadLibraryFromContent();renderContentPackageSummary();$('content-upload-text').textContent='已重新加载 '+(data.content_version||'内容包');toast('教材内容已重新加载。');}
 catch(e){await refreshContentPackageStatus().catch(()=>{});if(!contentPackage?.available)showContentMissing(contentPackage);$('content-upload-text').textContent=e.message;toast(e.message);}
 finally{b.disabled=false;}
}
function installContentPackage(file){
 if($('edit-dialog').open||$('note-text').value.trim()||savePending||failedMutations.length){toast('先保存个人编辑/批注并等待写入完成，再更新教材。');return;}
 if(!file){toast('先选择 Book 内容 ZIP。');return;}if(!/\.zip$/i.test(file.name)){toast('请选择 .zip 内容包。');return;}
 const max=8*1024*1024*1024;if(file.size>max){toast('内容包超过 8 GB。');return;}
 const button=$('content-install'),progress=$('content-upload-progress'),label=$('content-upload-text');button.disabled=true;progress.value=0;label.textContent='正在上传到本机 Book… 0%';
 const xhr=new XMLHttpRequest();xhr.open('POST','/api/content/install');xhr.responseType='json';xhr.setRequestHeader('X-Book-Token',token);xhr.setRequestHeader('Content-Type','application/zip');
 xhr.upload.onprogress=e=>{if(e.lengthComputable){const pct=Math.min(100,Math.round(e.loaded/e.total*100));progress.value=pct;label.textContent='正在上传到本机 Book… '+pct+'%';}else label.textContent='正在上传到本机 Book…';};
 xhr.onerror=()=>{button.disabled=false;label.textContent='上传失败；原内容包未改变。';toast('内容包上传失败。');};
 xhr.onload=async()=>{button.disabled=false;const data=xhr.response||{};if(xhr.status<200||xhr.status>=300){label.textContent=data.error||'安装失败；原内容包未改变。';toast(label.textContent);return;}try{contentPackage=data;label.textContent='校验通过，正在刷新书架…';progress.value=100;await loadLibraryFromContent();renderContentPackageSummary();$('content-package-dialog').close();status('已连接本机存储');toast('内容包已安装：'+(data.content_version||data.package_id));}catch(e){label.textContent='内容已安装，但刷新失败：'+e.message;messageError(e);}};
 xhr.send(file);
}

function validateBackup(v){if(!v||v.schema!=='book-personal-state-v1')throw Error('不是 Book 学习备份');for(const k of ['settings','books','notes','bookmarks','cards'])if(!v[k]||typeof v[k]!=='object'||Array.isArray(v[k]))throw Error('备份缺少 '+k);const walk=(x,depth=0)=>{if(depth>20)throw Error('备份嵌套过深');if(x&&typeof x==='object')for(const [k,v] of Object.entries(x)){if(['__proto__','constructor','prototype'].includes(k))throw Error('备份含不安全字段');walk(v,depth+1);}};walk(v);return v;}
function pendingSnapshot(){const next=clone(state);for(const apply of failedMutations)apply(next);return next;}
function mutate(fn){
 savePending++;status('正在保存…');
 const task=saveQueue.catch(()=>{}).then(async()=>{
  const operations=[...failedMutations,fn];failedMutations=[];
  try{
   for(let i=0;i<3;i++){
    const next=clone(state);for(const apply of operations)apply(next);validateBackup(next);const body=JSON.stringify({state:next,expected_revision:revision});
    if(new Blob([body]).size>30*1024*1024)throw Error('学习记录超过容量，请先导出备份。');
    const r=await fetch('/api/state',{method:'POST',headers:{'Content-Type':'application/json','X-Book-Token':token},body});
    if(r.status===409){const latest=await readJSON('/api/state');state=latest.state;revision=latest.revision;continue;}
    if(r.status===403){await session();continue;}
    if(!r.ok){let err={};try{err=await r.json();}catch{};throw Error(err.error||'保存失败；待保存内容仍在当前窗口，请导出备份或再次保存。');}
    const saved=await r.json();state=saved.state;revision=saved.revision;return saved;
   }
   throw Error('学习记录正在被另一窗口修改，未覆盖；请关闭其他窗口后重试。');
  }catch(e){failedMutations.push(...operations);throw e;}
 });
 saveQueue=task;task.then(()=>{savePending--;status(savePending?'正在保存…':'已保存到本机');},e=>{savePending--;messageError(e);});return task;
}
function settingSave(){prefs.size=clampFontSize(prefs.size);const snapshot=clone(prefs);return mutate(s=>{s.settings.documentReader=snapshot;});}
function noteKey(kind,bid){return 'doc:'+kind+':'+bid;}
function localCopy(block){const n=state?.notes?.[noteKey('copy',block.id)];return n&&n.source_sha===current.source_pdf.sha256?n:null;}
function noteEntries(){return Object.entries(state?.notes||{}).filter(([k,n])=>n.document_id===current?.id&&n.kind!=='document-copy');}
function bookmarks(){return Object.entries(state?.bookmarks||{}).filter(([k,n])=>n.document_id===current?.id);}
function sanitizeHTML(raw){
 const t=document.createElement('template');t.innerHTML=raw;
 const allowed=new Set(['P','DIV','SPAN','STRONG','B','EM','I','U','S','BR','SUB','SUP','OL','UL','LI','BLOCKQUOTE','PRE','CODE','TABLE','THEAD','TBODY','TR','TH','TD','CAPTION','FIGURE','FIGCAPTION','IMG','H1','H2','H3','H4','H5','H6','A','MARK']);
 for(const el of $$('*',t.content)){
  if(!allowed.has(el.tagName)){el.replaceWith(document.createTextNode(el.textContent||''));continue;}
  for(const a of Array.from(el.attributes)){
   const n=a.name.toLowerCase();
   if(n.startsWith('on')||(!['class','src','alt','title','width','height','style','href','start','colspan','rowspan','data-latex','data-vector-math'].includes(n)))el.removeAttribute(a.name);
  }
  if(el.hasAttribute('style')){const accepted=[];for(const name of ['width','height','vertical-align','text-align','font-weight','font-style','text-decoration','max-width']){const val=el.style.getPropertyValue(name);if(val&&/^[\w\s.()%+-]+$/.test(val))accepted.push(name+':'+val);}el.setAttribute('style',accepted.join(';'));}
  if(el.tagName==='IMG'&&(!/^\/document-assets\/[a-z0-9.-]+$/i.test(el.getAttribute('src')||'')))el.remove();
  // Pagination measures reserved image boxes, not decoded images. Avoid eagerly
  // requesting every formula in a long chapter while repeatedly cloning it.
  if(el.tagName==='IMG'){el.loading='lazy';el.decoding='async';}
  if(el.tagName==='A'){const href=el.getAttribute('href')||'';if(!/^(#|https?:\/\/)/.test(href))el.removeAttribute('href');else{el.setAttribute('target','_blank');el.setAttribute('rel','noopener');}}
 }
 return t.innerHTML;
}
function plainHTML(raw){const t=document.createElement('template');t.innerHTML=raw;for(const repeated of $$('[data-pagination-repeat]',t.content))repeated.remove();for(const im of $$('img',t.content))im.replaceWith(document.createTextNode(im.getAttribute('alt')||''));return t.content.textContent||'';}
function wrapInlineNoise(root,re,cls='reading-marker'){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement?.closest('.reading-marker,.reading-source-tail,script,style')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});
 const nodes=[];let n;while((n=walker.nextNode()))nodes.push(n);
 for(const node of nodes){const text=node.data;re.lastIndex=0;let m,last=0,changed=false,frag=document.createDocumentFragment();while((m=re.exec(text))){changed=true;frag.append(document.createTextNode(text.slice(last,m.index)));const span=document.createElement('span');span.className=cls;span.textContent=m[0];span.setAttribute('aria-label','隐藏的阅读注记');frag.append(span);last=m.index+m[0].length;if(!m[0].length)re.lastIndex++;}if(changed){frag.append(document.createTextNode(text.slice(last)));node.replaceWith(frag);}}
}
function wrapSourceTail(el){
 const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n,found=null,index=-1;
 while((n=walker.nextNode())){for(const key of ['资料来源：','资料来源:','数据来源：','数据来源:']){const i=n.data.indexOf(key);if(i>=0){found=n;index=i;break;}}if(found)break;}
 if(!found)return false;const before=(el.textContent||'').slice(0,Math.max(0,(el.textContent||'').indexOf(found.data))).trim();
 try{const r=document.createRange();r.setStart(found,index);r.setEnd(el,el.childNodes.length);const frag=r.extractContents(),span=document.createElement('span');span.className='reading-source-tail';span.append(frag);r.insertNode(span);return true;}catch{return false;}
}
function annotateReadingNoise(a){
 const text=(a.textContent||'').replace(/\s+/g,' ').trim();
 if(!text)return;
 if(/^教材来源要点[（(]重组[）)]$/.test(text)||/^以下内容继续按教材结构化来源展开/.test(text)||/^[•·]?\s*知道普通\s*OCR\s*仅为辅助层/.test(text)||/^(资料来源|数据来源)[：:]/.test(text)){a.classList.add('reading-noise');a.dataset.readingNoise='source';}
 if(/^(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+[.、]?)?\s*[（(]原书本页脚注[）)]/.test(text)||/^脚注\s*原书脚注指出/.test(text)||/^(?:\d+[.、]?)?\s*[（(]原书脚注标记[）)]\s*[（(]原书本页脚注[）)]/.test(text)){a.classList.add('reading-footnote');a.dataset.readingNoise='footnote';}
 wrapInlineNoise(a,/（原书脚注标记）|\(原书脚注标记\)|（原书本页脚注）|\(原书本页脚注\)|不依赖页码或\s*record\s*ID[^。；]*[。；]?/gi);
 for(const el of $$('p,li,figcaption,caption',a))wrapSourceTail(el);
 // Keep the useful heading, hide only the provenance wording.
 wrapInlineNoise(a,/（来源展开）|\(来源展开\)/g);
}
function decorateArticle(a,b){
 a.classList.add('doc-block');a.dataset.blockId=b.id;a.dataset.kind=b.kind;if(b.correction_id){a.dataset.correction=b.correction_id;a.classList.add('editorial-revised');}if(b.audit_notice)a.classList.add('editorial-notice');
 if(b.answer_text)a.dataset.answer='1';if(b.question_number)a.dataset.questionNumber=String(b.question_number);if(b.answer_label)a.classList.add('source-answer-label');if(b.question_text)a.classList.add('source-question');if(b.question_start)a.dataset.questionStart='1';
 if(current?.mode==='practice'&&b.answer_text){const q=Number(b.question_number)||0;const open=!answersHidden||revealedAnswers.has(q);if(b.answer_label){a.classList.toggle('answer-label-closed',!open);a.setAttribute('role','button');a.setAttribute('tabindex','0');a.setAttribute('aria-expanded',String(open));}else a.classList.toggle('answer-concealed',!open);}
 const copy=localCopy(b);if(copy)a.classList.add('edited');
 const entries=noteEntries().filter(([,n])=>resolveAnchor(n.block_id)===b.id);if(entries.length)a.classList.add('has-note');
 for(const [,n]of entries){if(n.kind==='document-highlight')highlightQuote(a,n.quote,'saved-highlight');}
 return a;
}
function reserveMedia(root){
 for(const im of $$('img.math-atom,img.math-display',root)){
  if(im.parentElement?.classList.contains('math-box'))continue;
  const block=im.classList.contains('math-display'),box=document.createElement('span');box.className='math-box '+(block?'block':'inline');box.style.width=im.style.width||'1em';box.style.height=im.style.height||'1em';if(!block)box.style.verticalAlign=im.style.verticalAlign||'-.15em';
  im.replaceWith(box);box.append(im);im.style.width='100%';im.style.height='100%';im.style.verticalAlign='';
 }
 for(const im of $$('img.source-figure',root)){
  if(im.parentElement?.classList.contains('figure-frame'))continue;const w=Number(im.getAttribute('width')),h=Number(im.getAttribute('height'));if(!w||!h)continue;
  const box=document.createElement('span');box.className='figure-frame';box.style.width=w+'px';box.style.aspectRatio=w+'/'+h;im.replaceWith(box);box.append(im);
 }
}
function isReviewRecallHeading(a){
 const h=a.querySelector(':scope>h1,:scope>h2,:scope>h3,:scope>h4,:scope>h5,:scope>h6');if(!h)return false;const text=(h.textContent||'').replace(/\s+/g,' ').trim();return /^(?:§\s*\d+|\d+\.\d+(?!\.)|[一二三四五六七八九十]+、)/.test(text)||/(?:章末|讲末|单元)\s*(?:总结|自测)|闭卷自测|考试要点/.test(text);
}
function hasSourceFigure(node){return Boolean(node?.querySelector?.('img.source-figure'))||Boolean(node?.matches?.('img.source-figure'));}
function mediaCaptionLike(node){
 if(!node||node.nodeType!==1)return false;const text=(node.textContent||'').replace(/\s+/g,' ').trim();
 return Boolean(node.matches('h1,h2,h3,h4,h5,h6,figcaption,caption,blockquote'))||/^(?:表|图|附表|附图)\s*[0-9一二三四五六七八九十IVXivx]/.test(text)||/(?:原表图像|本讲配图原页|原图|原页|独立裁图)/.test(text);
}
function mediaAwareUnits(nodes){
 const units=[];for(let i=0;i<nodes.length;){
  let end=i+1;if(nodes[i]?.nodeType===1&&!hasSourceFigure(nodes[i])){
   let probe=i;while(probe<nodes.length&&probe<i+3&&mediaCaptionLike(nodes[probe])&&!hasSourceFigure(nodes[probe]))probe++;
   if(probe<nodes.length&&hasSourceFigure(nodes[probe]))end=probe+1;
  }
  const group=nodes.slice(i,end);units.push({nodes:group,mediaGroup:group.some(hasSourceFigure)&&group.length>1});i=end;
 }
 return units;
}
function allFragments(){
 const fragments=[];
 if(current.mode==='learn'){
  const div=document.createElement('div');div.className='document-title';div.innerHTML='<h1>'+escape(current.title.replaceAll('_',' '))+'</h1><p>'+escape(current.book_title)+' · 学习正文</p>';const a=document.createElement('article');a.className='doc-block';a.dataset.blockId=current.id+'-title';a.append(div);fragments.push(a);
 }
 let reviewSection=0;
 for(const b of current.blocks){
  if(b.reader_visibility==='audit_only')continue;
  const readerHTML=localCopy(b)?.html||b.reader_html||b.html;
  const t=document.createElement('template');t.innerHTML=sanitizeHTML(readerHTML);const nodes=Array.from(t.content.childNodes).filter(n=>n.nodeType===1||(n.textContent||'').trim());
  for(const unit of mediaAwareUnits(nodes)){const a=decorateArticle(document.createElement('article'),b);for(const node of unit.nodes){let child=node;if(node.nodeType!==1){child=document.createElement('p');child.append(node);}a.append(child);}if(unit.mediaGroup)a.classList.add('source-media-group');if(current.mode==='practice'&&b.answer_label){const h=a.querySelector(':scope>h1,:scope>h2,:scope>h3,:scope>h4,:scope>h5,:scope>h6');if(h){const d=document.createElement('div');d.className='answer-label-text';d.innerHTML=h.innerHTML;h.replaceWith(d);}}annotateReadingNoise(a);reserveMedia(a);if(current.mode==='review'){const heading=isReviewRecallHeading(a);if(heading)reviewSection++;if(reviewSection){a.dataset.reviewSection=String(reviewSection);if(heading){a.classList.add('review-section-title');a.setAttribute('role','button');a.setAttribute('tabindex','0');const open=!reviewRecall||revealedReviewSections.has(reviewSection);a.classList.toggle('recall-closed',!open);a.setAttribute('aria-expanded',String(open));}else if(reviewRecall&&!revealedReviewSections.has(reviewSection))a.classList.add('review-recall-hidden');}}fragments.push(a);}
 }
 if(current.mode==='review'){
  const withBody=new Set();for(const a of fragments){if(a.dataset.reviewSection&&!a.classList.contains('review-section-title'))withBody.add(a.dataset.reviewSection);}
  for(const a of fragments.filter(x=>x.classList.contains('review-section-title'))){if(withBody.has(a.dataset.reviewSection))continue;a.classList.remove('review-section-title','recall-closed');a.removeAttribute('role');a.removeAttribute('tabindex');a.removeAttribute('aria-expanded');}
 }
 return fragments;
}
function applyPrefs(){
 prefs.size=clampFontSize(prefs.size);const root=document.documentElement;root.style.setProperty('--doc-size',prefs.size+'px');root.style.setProperty('--doc-leading',prefs.leading);root.style.setProperty('--doc-margin',prefs.margin+'mm');root.dataset.theme=prefs.theme;root.dataset.cleanReading=String(prefs.cleanReading!==false);
 const font=FONT_STACKS[prefs.font]||FONT_STACKS.shusong;root.style.setProperty('--doc-font',font);
 $('layout-toggle').querySelector('span').textContent=prefs.layout==='pages'?'连续阅读':'A4 分页';$('layout-toggle').setAttribute('aria-label',prefs.layout==='pages'?'切换连续阅读':'切换 A4 自动分页');
 adjustZoom();
}
async function detectLocalSerif(){
 await document.fonts.ready;let found='';
 // FontFaceSet.check() returns true even for missing system fonts. A local-only
 // load either resolves a real face or fails; no font is fetched or redistributed.
 const names=[...SHUSONG_CANDIDATES,'Noto Serif CJK SC','Source Han Serif SC'];
 for(const name of names){try{const face=new FontFace('BookDetectedSerif','local('+JSON.stringify(name)+')',{weight:'400'});await face.load();if(detectedFace)document.fonts.delete(detectedFace);detectedFace=face;document.fonts.add(face);found=name;break;}catch{}}
 if(found)FONT_STACKS.shusong='"BookDetectedSerif",'+FONT_STACKS.shusong.replace(/^"BookDetectedSerif",/,'');
 const dedicated=found&& !['SimSun','STSong','Songti SC','Noto Serif CJK SC','Source Han Serif SC'].includes(found);
 $('font-detect').textContent=found?(dedicated?'已加载本机书宋：':'未加载专用书宋，当前回退：')+found+'。本机字体不上传、不随内容包分发。':'未能确认本机书宋字体；按系统字体回退。可导入你有使用权的本地字体。';
 document.documentElement.dataset.serifFont=found||'fallback';applyPrefs();return found;
}
function updateFullscreenUI(){const on=Boolean(document.fullscreenElement);document.body.classList.toggle('fullscreen-active',on);if(on){if(fullscreenPriorImmersive===null)fullscreenPriorImmersive=document.body.classList.contains('immersive');if(current)setImmersive(true);}else if(fullscreenPriorImmersive!==null){setImmersive(fullscreenPriorImmersive);fullscreenPriorImmersive=null;}const b=$('fullscreen'),f=$('focus-fullscreen');if(b){b.innerHTML=on?'⛶ <span>退出全屏</span>':'⛶ <span>全屏</span>';b.title=on?'退出全屏 F11 / Esc':'全屏 F11';}if(f)f.textContent=on?'退出全屏':'⛶ 全屏';adjustZoom();}
async function toggleFullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen({navigationUI:'hide'});}catch(e){setImmersive(true);toast('系统全屏未被允许，已进入沉浸阅读。');}updateFullscreenUI();}
function setImmersive(on){const next=Boolean(on);document.body.classList.toggle('immersive',next);const b=$('immersive');if(b){b.innerHTML=next?'◱ <span>退出沉浸</span>':'◱ <span>沉浸</span>';b.title=next?'退出沉浸 Esc':'沉浸阅读 M';}requestAnimationFrame(adjustZoom);}
function toggleImmersive(){setImmersive(!document.body.classList.contains('immersive'));}
function isTypingTarget(t){return Boolean(t?.closest?.('input,textarea,select,[contenteditable="true"]'));}
function adjustZoom(){const available=Math.max(260,$('reading-area').clientWidth-52);const z=prefs.zoom==='fit'?Math.min(1,available/mm(210)):Math.max(.3,Math.min(1.8,Number(prefs.zoom)));document.documentElement.style.setProperty('--view-zoom',z);$('zoom-fit').textContent=prefs.zoom==='fit'?'适合宽度':Math.round(z*100)+'%';}
function makeSheet(num){const s=document.createElement('section');s.className='sheet';s.dataset.page=String(num);const header=document.createElement('div');header.className='page-header';header.innerHTML='<span>'+escape(current.book_title)+'</span><span>'+escape(current.title.replaceAll('_',' ')+' · '+MODES[current.mode])+'</span>';const body=document.createElement('div');body.className='sheet-body document-body';const footer=document.createElement('div');footer.className='page-footer';footer.innerHTML='<span>Book · '+escape(MODES[current.mode])+'</span><span class="page-number">'+num+'</span>';s.append(header,body,footer);return {sheet:s,body,footer};}
const nextFrame=()=>new Promise(r=>requestAnimationFrame(r));
function outerHeight(el){const c=getComputedStyle(el);return el.getBoundingClientRect().height+(parseFloat(c.marginTop)||0)+(parseFloat(c.marginBottom)||0);}

function rangePoints(el){const points=[];function walk(n){if(n.nodeType===3){let offset=0;for(const c of n.data){offset+=c.length;points.push({node:n,offset,c});}}else if(n.nodeType===1){if(['IMG','SVG','BR','HR','MATH','MJX-CONTAINER'].includes(n.tagName)||n.classList.contains('math-box')||n.classList.contains('figure-frame')){points.push({node:n.parentNode,offset:Array.prototype.indexOf.call(n.parentNode.childNodes,n)+1,c:'\uFFFC'});}else for(const child of n.childNodes)walk(child);}}walk(el);return points;}
function splitAt(original,points,n){const root=original.cloneNode(false),r=document.createRange();r.selectNodeContents(original);r.setEnd(points[n-1].node,points[n-1].offset);root.append(r.cloneContents());return root;}
function splitFragment(a,available,measure){
 if(a.classList.contains('source-media-group')&&a.querySelector('img.source-figure'))return null;
 const points=rangePoints(a);if(points.length<2)return null;
 // Table boundaries should stay at rows whenever possible.
 const table=a.querySelector('table');
 if(table){const rows=$$('tbody>tr',table);if(rows.length>1){let k=0;for(let i=1;i<rows.length;i++){const h=a.cloneNode(true);const hr=$$('tbody>tr',h);hr.slice(i).forEach(x=>x.remove());measure.replaceChildren(h);if(outerHeight(h)<=available)k=i;else break;}if(k){const h=a.cloneNode(true),t=a.cloneNode(true);$$('tbody>tr',h).slice(k).forEach(x=>x.remove());$$('tbody>tr',t).slice(0,k).forEach(x=>x.remove());const repeatedHead=t.querySelector('thead');if(repeatedHead){repeatedHead.dataset.paginationRepeat='table-header';repeatedHead.setAttribute('aria-hidden','true');}h.classList.add('fragment-head');t.classList.add('fragment-tail');return [h,t];}return null;}}
 let lo=1,hi=points.length-1,best=0;
 while(lo<=hi){const n=Math.floor((lo+hi)/2),part=splitAt(a,points,n);measure.replaceChildren(part);if(outerHeight(part)<=available){best=n;lo=n+1;}else hi=n-1;}
 if(best<1)return null;
 // Prefer a nearby word or clause boundary, but never drop characters.
 if(best>15){for(let i=best-1;i>=Math.max(1,best-28);i--){if(/[\s。；，！？,.!?;:]/u.test(points[i].c)){best=i+1;break;}}}
 const head=splitAt(a,points,best),tail=a.cloneNode(false);const range=document.createRange();range.selectNodeContents(a);range.setStart(points[best-1].node,points[best-1].offset);tail.append(range.cloneContents());head.classList.add('fragment-head');tail.classList.add('fragment-tail');
 const hol=head.querySelector('ol'),tol=tail.querySelector('ol');if(hol&&tol){const count=hol.querySelectorAll(':scope>li').length;tol.start=(Number(hol.getAttribute('start'))||1)+Math.max(0,count-1);}
 return [head,tail];
}
// A block can span many pages. Store a content offset, not a fraction of just
// the current fragment; fragment boundaries change when the font size changes.
const READING_TOP=150;
function anchorPoints(el){return rangePoints(el).filter(p=>!(p.node.nodeType===1?p.node:p.node.parentElement)?.closest('[data-pagination-repeat]'));}
function anchorPointRect(p){
 const r=document.createRange();r.setStart(p.node,Math.max(0,p.offset-p.c.length));r.setEnd(p.node,p.offset);return r.getBoundingClientRect();
}
function activeAnchor(){
 if(!current)return null;if(busy&&reflowAnchor?.document_id===current.id&&reflowAnchor.anchor)return clone(reflowAnchor.anchor);const blocks=$$('.doc-block',$('pages'));
 const el=blocks.find(e=>e.getBoundingClientRect().height>0&&e.getBoundingClientRect().bottom>READING_TOP+1);if(!el)return null;
 const rect=el.getBoundingClientRect(),points=anchorPoints(el);let within=0;
 if(rect.top<READING_TOP&&points.length){
  const x=rect.left+Math.min(8,rect.width/2),y=READING_TOP+2;
  const caret=document.caretPositionFromPoint?.(x,y),range=!caret&&document.caretRangeFromPoint?.(x,y);
  const node=caret?.offsetNode||range?.startContainer,offset=caret?.offset??range?.startOffset;
  if(node&&el.contains(node)){const i=points.findIndex(p=>p.node===node&&p.offset>offset);if(i>=0)within=i;}
  else{let lo=0,hi=points.length-1;while(lo<hi){const mid=(lo+hi)>>1;if(anchorPointRect(points[mid]).bottom<=READING_TOP)lo=mid+1;else hi=mid;}within=lo;}
 }
 let prior=0;for(const b of blocks){if(b===el)break;if(b.dataset.blockId===el.dataset.blockId)prior+=anchorPoints(b).length;}
 return {block_id:el.dataset.blockId,offset:Math.max(0,(READING_TOP-rect.top)/Math.max(1,rect.height)),content_offset:prior+within};
}
// If even one table row plus its header cannot fit at the selected size,
// render a labelled, linear table rather than silently shrinking the type.
// The original document and table remain unchanged in the source layer.
function linearizeTable(a){
 const table=a.querySelector('table');if(!table)return false;
 const out=document.createElement('div');out.className='reflow-table';out.setAttribute('role','table');out.style.fontSize='.9em';
 const headers=$$('thead th,thead td',table).map(h=>h.textContent.trim());
 if(table.caption){const caption=document.createElement('div');caption.append(...Array.from(table.caption.childNodes).map(n=>n.cloneNode(true)));out.append(caption);}
 for(const row of $$('tr',table).filter(r=>r.closest('table')===table)){
  // Empty OCR placeholder rows have no readable payload; keep them in the
  // source table, not as dozens of blank/label-only pages in the reader.
  if(row.closest('tbody')&&Array.from(row.cells).every(cell=>!cell.textContent.trim()&&!cell.querySelector('img,svg,math')))continue;
  const group=document.createElement('div');group.setAttribute('role','row');
  Array.from(row.cells).forEach((cell,i)=>{
   const box=document.createElement('div');box.setAttribute('role',cell.tagName==='TH'?'columnheader':'cell');box.style.cssText='border-bottom:1px solid var(--line);padding:.35em 0;overflow-wrap:anywhere;';
   if(cell.tagName!=='TH'&&headers[i]){const label=document.createElement('strong');label.dataset.paginationRepeat='table-label';label.setAttribute('aria-hidden','true');label.textContent=headers[i]+'：';box.append(label);}
   box.append(...Array.from(cell.childNodes).map(n=>n.cloneNode(true)));group.append(box);
  });out.append(group);
 }
 table.replaceWith(out);return true;
}
function fitContinuousTables(root){
 for(const a of $$('.doc-block',root)){const table=a.querySelector('table');if(table&&table.getBoundingClientRect().width>a.getBoundingClientRect().width+1)linearizeTable(a);}
}
function headingFollowerNeed(queue,measure,H){
 let need=0,seen=0;
 for(const upcoming of queue.slice(0,5)){
  const probe=upcoming.cloneNode(true);measure.replaceChildren(probe);const h=outerHeight(probe),isHeading=Boolean(probe.querySelector(':scope>h1,:scope>h2,:scope>h3,:scope>h4,:scope>h5,:scope>h6'));
  if(isHeading){need+=Math.min(h,H*.22);seen++;continue;}
  need+=Math.min(h,prefs.size*prefs.leading*3.2);seen++;break;
 }
 return seen?need:prefs.size*prefs.leading*2.8;
}
function fitIndivisible(a,H,measure){
 measure.replaceChildren(a);let h=outerHeight(a);const frames=$$('.figure-frame',a),math=a.querySelector('.math-box'),im=a.querySelector('img');
 if(a.classList.contains('source-media-group')&&frames.length){
  const boxes=frames.map(f=>f.getBoundingClientRect()),mediaH=boxes.reduce((n,b)=>n+b.height,0),extra=Math.max(0,h-mediaH),target=Math.max(42,H-extra-8),scale=Math.min(1,target/Math.max(1,mediaH));
  frames.forEach((f,i)=>{const box=boxes[i];f.style.width=(box.width*scale)+'px';f.style.height=(box.height*scale)+'px';f.style.aspectRatio='auto';});measure.replaceChildren(a);h=outerHeight(a);
 }else if(math||frames.length){
  const frame=math||frames[0];let box=frame.getBoundingClientRect(),extra=Math.max(0,h-box.height),target=Math.max(36,H-extra-4),scale=Math.min(1,target/Math.max(1,box.height));
  frame.style.width=(box.width*scale)+'px';frame.style.height=(box.height*scale)+'px';frame.style.aspectRatio='auto';measure.replaceChildren(a);h=outerHeight(a);
  if(h>H+2){box=frame.getBoundingClientRect();extra=Math.max(0,h-box.height);target=Math.max(24,H-extra-6);const ratio=box.width/Math.max(1,box.height);frame.style.height=target+'px';frame.style.width=Math.min(box.width,target*ratio)+'px';measure.replaceChildren(a);h=outerHeight(a);}
 }else if(im){im.style.maxHeight=Math.max(80,H-30)+'px';im.style.width='auto';im.style.maxWidth='100%';im.style.height='auto';measure.replaceChildren(a);h=outerHeight(a);}
  // Text must keep the requested size. Oversized text is split by paginate().
 return h;
}
async function paginate(anchor=null){
 if(!current)return;const my=++renderToken;reflowAnchor={document_id:current.id,anchor:anchor?clone(anchor):null};busy=true;$('loading').hidden=false;$('loading').textContent='正在按你的字号整理纸页…';$('pages').replaceChildren();$('pages').className=prefs.layout==='continuous'?'continuous':'';applyPrefs();
 await document.fonts.ready;if(my!==renderToken)return;const fragments=allFragments(),measure=$('measure-root');measure.style.width=(mm(210)-2*mm(prefs.margin))+'px';const H=mm(297-19-18)-2;
 let count=0,currentSheet=makeSheet(1),used=0;const parent=$('pages');parent.append(currentSheet.sheet);let queue=fragments.slice();
 if(prefs.layout==='continuous'){currentSheet.body.append(...queue);fitContinuousTables(currentSheet.body);count=1;}
 else{
  let iter=0;
  while(queue.length){
   if(my!==renderToken)return;
   const a=queue.shift();measure.replaceChildren(a);let h=outerHeight(a);
   if(a.querySelector('table')?.getBoundingClientRect().width>measure.clientWidth+1){linearizeTable(a);measure.replaceChildren(a);h=outerHeight(a);}
   const heading=Boolean(a.querySelector(':scope>h1,:scope>h2,:scope>h3,:scope>h4,:scope>h5,:scope>h6'));
   const needsRoom=heading?Math.min(H,h+headingFollowerNeed(queue,measure,H)):h;
   if(used&&used+needsRoom>H&&heading){currentSheet=makeSheet(++count+1);parent.append(currentSheet.sheet);used=0;}
   if(used+h<=H+.3){currentSheet.body.append(a);used+=h;}
   else{
    const available=H-used;let pieces=null;
    if(available>prefs.size*prefs.leading*2.3&&(!heading||(!used&&h>H)))pieces=splitFragment(a,available,measure);
    if(pieces){const [head,tail]=pieces;measure.replaceChildren(head);const hh=outerHeight(head);currentSheet.body.append(head);used+=hh;queue.unshift(tail);currentSheet=makeSheet(++count+1);parent.append(currentSheet.sheet);used=0;}
    else if(used){queue.unshift(a);currentSheet=makeSheet(++count+1);parent.append(currentSheet.sheet);used=0;}
    else{
     if(a.querySelector('table')&&h>H&&linearizeTable(a)){queue.unshift(a);continue;}
     const original=a.cloneNode(true);
     // Fit only indivisible media; never reduce the user's selected text size.
     h=fitIndivisible(a,H,measure);
     if(h>H+2&&original.classList.contains('source-media-group')&&original.children.length>1){
      const units=Array.from(original.children).map(child=>{const unit=original.cloneNode(false);unit.classList.remove('source-media-group');unit.append(child);return unit;});queue.unshift(...units);continue;
     }
     if(h>H+2){
      const split=splitFragment(a,H,measure);if(split){queue.unshift(...split);continue;}
      // A genuinely indivisible object stays accessible by scrolling, never
      // by clipping content or shrinking otherwise readable surrounding text.
      a.classList.add('oversize-object');a.style.maxHeight=H+'px';a.style.overflow='auto';a.tabIndex=0;measure.replaceChildren(a);h=outerHeight(a);
     }
     currentSheet.body.append(a);used=h;
    }
   }
   if(++iter%70===0){$('loading').textContent='正在排版 · '+(count+1)+' 页';await nextFrame();}
  }
  count=parent.children.length;
 }
 measure.replaceChildren();
 if(my!==renderToken)return;
 for(const [i,s]of Array.from(parent.children).entries()){s.querySelector('.page-number').textContent=(prefs.layout==='continuous'?'连续正文':`${i+1} / ${count}`);s.dataset.page=String(i+1);}
 $$('img',parent.children[0]||parent).slice(0,30).forEach(im=>im.loading='eager');
 $('loading').hidden=true;busy=false;$('doc-info').textContent=prefs.layout==='continuous'?`连续正文 · ${prefs.size}px`:`${count} 页 · ${prefs.size}px`;$('edition-label').textContent=current.mode==='learn'?'正文排印稿 · 2026-09-26':current.edition+' · 教材原题 / AI 参考解答';
 refreshAnswerVisibility();renderNotes();
 if(anchor?.block_id)jumpToBlock(anchor.block_id,false,anchor.offset,anchor.content_offset);else window.scrollTo({top:$('workspace').offsetTop,behavior:'instant'});
 updatePosition();if($('find-input').value&&!$('findbar').hidden)findText($('find-input').value);
 window.dispatchEvent(new CustomEvent('book-document-rendered',{detail:{id:current.id,pages:count,layout:prefs.layout}}));
}
function resolveAnchor(id){const source=current?.anchor_aliases?.[id]||id;return current?.reader_anchor_aliases?.[source]||source;}
function jumpToBlock(id,smooth=true,offset=0,contentOffset=null){
 id=resolveAnchor(id);const items=$$('[data-block-id]',$('pages')).filter(x=>x.dataset.blockId===id);let el=items[0];if(!el)return false;
 let r=el.getBoundingClientRect(),y=r.top+r.height*(offset||0);
 if(Number.isFinite(contentOffset)){
  let remaining=Math.max(0,contentOffset);
  for(const item of items){const points=anchorPoints(item);if(remaining<points.length||item===items.at(-1)){const point=points[Math.min(remaining,points.length-1)];y=point?anchorPointRect(point).top:item.getBoundingClientRect().top;break;}remaining-=points.length;}
 }
 window.scrollTo({top:window.scrollY+y-READING_TOP,behavior:smooth?'smooth':'instant'});return true;
}
function updatePosition(){
 if(!current||busy)return;const sheets=$$('.sheet',$('pages'));let page=1;
 for(const s of sheets){if(s.getBoundingClientRect().top<window.innerHeight*.55)page=Number(s.dataset.page);else break;}
 const total=sheets.length;const percent=prefs.layout==='continuous'?Math.min(1,Math.max(0,(window.scrollY+window.innerHeight-$('workspace').offsetTop)/Math.max(1,$('pages').scrollHeight))):page/Math.max(1,total);
 $('progress-line').firstElementChild.style.width=(percent*100).toFixed(1)+'%';$('position-label').textContent=prefs.layout==='continuous'?'连续正文 · '+Math.round(percent*100)+'%':`重排第 ${page} / ${total} 页`;
 clearTimeout(positionTimer);positionTimer=setTimeout(savePosition,750);
}
function savePosition(){
 if(!current||busy)return Promise.resolve();const anchor=activeAnchor(),id=current.id,bid=current.book_id,ch=current.chapter,mode=current.mode;if(!anchor)return Promise.resolve();
 const progress=studySharing?captureStudyProgress():null;
 return mutate(s=>{s.books[bid]??={};s.books[bid].documentPositions??={};s.books[bid].documentPositions[id]={...anchor,updated_at:new Date().toISOString()};s.settings.documentReaderLast={book_id:bid,chapter:ch,mode};if(progress)s.settings.documentReaderLive=progress;})
  .then(saved=>{if(progress)dispatchStudyProgress(progress);return saved;});
}
// Session-scoped semantic progress. Native mygpt reads the existing /api/state;
// no cross-origin browser request, model call, screenshot, note or answer upload.
let studySharing=false,studySequence=0,studyVisibleMs=0,studyLastTick=Date.now(),studyLastVisible=false,studyLastInput=Date.now();
const studySession='book-'+crypto.randomUUID();
function captureStudyProgress(forcedStatus=null){
 const now=Date.now(),visible=Boolean(studySharing&&current&&!busy&&document.visibilityState==='visible'&&document.hasFocus());
 if(studyLastVisible)studyVisibleMs+=Math.max(0,Math.min(5000,now-studyLastTick));studyLastTick=now;studyLastVisible=visible;
 const status=!studySharing?'disabled':forcedStatus||(current?(visible?'reading':'paused'):'stopped');
 let context=null;
 if(studySharing&&current&&['reading','paused'].includes(status)){
  const anchor=activeAnchor(),blocks=current.blocks.filter(b=>b.reader_visibility!=='audit_only');
  const index=Math.max(0,blocks.findIndex(b=>b.id===anchor?.block_id)),sheets=$$('.sheet',$('pages'));
  const sheet=sheets.find(s=>s.getBoundingClientRect().bottom>READING_TOP+1)||sheets[0];
  context={book_id:current.book_id,book_title:String(book?.title||current.book_id).slice(0,160),document_id:current.id,chapter:Number(current.chapter)||0,mode:current.mode,
   source_sha256:current.source_pdf.sha256,block_id:anchor?.block_id||blocks[0]?.id||current.id,content_offset:Math.max(0,Math.floor(anchor?.content_offset||0)),
   block_index:index,block_count:Math.max(1,blocks.length),position_fraction:index/Math.max(1,blocks.length),
   rendered_page:Number(sheet?.dataset.page)||1,rendered_page_count:Math.max(1,sheets.length),font_px:prefs.size,
   practice_answered:current.mode==='practice'?answeredPracticeCount():0,practice_total:current.mode==='practice'?(current.questions||[]).length:0,fullscreen:Boolean(document.fullscreenElement)};
 }
 const modal=['edit-dialog','settings-dialog','backup-dialog','content-package-dialog','content-audit-dialog'].some(id=>$(id)?.open);
 const typing=Boolean(document.activeElement&&isTypingTarget(document.activeElement));
 return {schema:'book.study-progress.v1',producer_session:studySession,sequence:++studySequence,captured_at:new Date(now).toISOString(),expires_at:new Date(now+15000).toISOString(),
  status,visible_seconds:studySharing?Math.floor(studyVisibleMs/1000):0,idle_seconds:studySharing?Math.max(0,Math.floor((now-studyLastInput)/1000)):0,
  can_interact:status==='reading'&&!printing&&!modal&&!typing&&!$('note-text').value.trim(),context};
}
function dispatchStudyProgress(progress){window.dispatchEvent(new CustomEvent('book-study-progress',{detail:clone(progress)}));}
function publishStudyPresence(status=null){const progress=captureStudyProgress(status);return mutate(s=>{s.settings.documentReaderLive=progress;}).then(saved=>{dispatchStudyProgress(progress);return saved;});}
function setStudySharing(on){
 if(typeof on!=='boolean')return Promise.reject(new TypeError('共享开关必须是布尔值'));
 studySharing=on;const checkbox=$('study-sharing');if(checkbox)checkbox.checked=on;return publishStudyPresence();
}
function bindStudySharing(){
 const row=document.createElement('p'),label=document.createElement('label'),checkbox=document.createElement('input'),hint=document.createElement('small');
 row.className='settings-note';checkbox.type='checkbox';checkbox.id='study-sharing';label.append(checkbox,document.createTextNode(' 让 mygpt 了解本次阅读进度'));
 hint.textContent='仅本机书名、章节、位置和模式；不共享正文、笔记或答案。重开 Book 后需重新开启。';row.append(label,document.createElement('br'),hint);
 $('settings-dialog').insertBefore(row,$('settings-dialog').querySelector('.dialog-footer'));
 checkbox.onchange=()=>setStudySharing(checkbox.checked).catch(messageError);
 // Clear an old/imported lease instead of silently resuming sharing on restart.
 setStudySharing(false).catch(messageError);
 for(const name of ['pointerdown','keydown','wheel','touchstart'])window.addEventListener(name,()=>{studyLastInput=Date.now();},{passive:true});
 const presence=()=>{if(studySharing&&!busy)(current?savePosition():publishStudyPresence('stopped')).catch(messageError);};
 window.addEventListener('focus',presence);window.addEventListener('blur',presence);setInterval(presence,5000);
}
function answeredPracticeCount(){
 if(!current||current.mode!=='practice')return 0;let n=0;for(const q of current.questions||[]){const item=state?.cards?.['doc:attempt:'+current.id+':q'+q.number];if((item?.answer||'').trim()||['again','mastered'].includes(item?.rating))n++;}return n;
}
function renderModeGuide(){
 if(!current)return;const g=MODE_GUIDES[current.mode],primary=$('mode-primary'),secondary=$('mode-secondary');if(!g)return;
 let kicker=g.kicker,text=g.text;
 if(current.mode==='practice'){const total=(current.questions||[]).length,done=answeredPracticeCount();kicker=`${total} 道教材题 · ${done} 已作答`;text=`${g.text} 当前定位：第 ${practiceCursor||1} 题。`;}
 if(current.mode==='review'&&reviewRecall){kicker='主动回忆已开启';text='正文暂时折叠，只保留知识标题。先在脑中作答，再点击标题展开这一节核对。';}
 $('mode-kicker').textContent=kicker;$('mode-guide-title').textContent=g.title;$('mode-guide-text').textContent=text;
 primary.textContent=g.primary;secondary.textContent=current.mode==='review'?(reviewRecall?'退出主动回忆':'开启主动回忆'):g.secondary;secondary.hidden=!g.secondary;
 document.documentElement.dataset.readerMode=current.mode;document.documentElement.dataset.reviewRecall=String(reviewRecall);
}
function jumpModeLandmark(words){
 for(const el of $$('.doc-block',$('pages'))){const text=(el.innerText||'').replace(/\s+/g,' ');if(words.some(w=>text.includes(w))){const r=el.getBoundingClientRect();window.scrollTo({top:window.scrollY+r.top-190,behavior:'smooth'});el.classList.add('focus-block');setTimeout(()=>el.classList.remove('focus-block'),1500);return true;}}
 toast('本章没有找到对应的自检/总结标题。');return false;
}
function openPracticePanel(){if(!current||current.mode!=='practice')return;notesTab='practice';showNotes();renderPractice(true);$('practice-answer').focus();}
function nextPracticeQuestion(){
 if(!current||current.mode!=='practice')return;const qs=current.questions||[];if(!qs.length)return;let i=qs.findIndex(q=>q.number===practiceCursor);i=(i+1+qs.length)%qs.length;practiceCursor=qs[i].number;if(!$('notes-panel').hidden&&notesTab==='practice'){$('practice-question').value=practiceCursor;renderPractice(true);}jumpToBlock(qs[i].block_id);renderModeGuide();
}
async function togglePracticeAnswer(number){
 if(!current||current.mode!=='practice')return;number=Number(number)||practiceCursor||1;if(!answersHidden){answersHidden=true;revealedAnswers=new Set((current.questions||[]).map(q=>Number(q.number)));}
 if(revealedAnswers.has(number))revealedAnswers.delete(number);else revealedAnswers.add(number);practiceCursor=number;const anchor={block_id:(current.questions||[]).find(q=>Number(q.number)===number)?.block_id||activeAnchor()?.block_id};await paginate(anchor);renderModeGuide();
}
async function setReviewRecall(on){
 if(!current||current.mode!=='review')return;reviewRecall=Boolean(on);if(!reviewRecall)revealedReviewSections.clear();const anchor=activeAnchor();renderModeGuide();await paginate(anchor);
}
async function toggleReviewSection(section,blockId){
 section=Number(section);if(!reviewRecall||!section)return;if(revealedReviewSections.has(section))revealedReviewSections.delete(section);else revealedReviewSections.add(section);await paginate({block_id:blockId});renderModeGuide();
}
function modePrimaryAction(){if(!current)return;if(current.mode==='preview')openChapter(chapter.number,'learn');else if(current.mode==='learn')openChapter(chapter.number,'review');else if(current.mode==='review')openChapter(chapter.number,'practice');else openPracticePanel();}
function modeSecondaryAction(){if(!current)return;if(current.mode==='preview')jumpModeLandmark(['预习自检','自检']);else if(current.mode==='learn')toggleImmersive();else if(current.mode==='review')setReviewRecall(!reviewRecall);else nextPracticeQuestion();}
function renderNav(){
 $('book-list').replaceChildren();$('chapter-list').replaceChildren();if(!library)return;for(const [i,b]of library.books.entries()){const button=document.createElement('button');button.dataset.book=b.id;button.className=book?.id===b.id?'active':'';button.innerHTML='<span class="book-no">'+String(i+1).padStart(2,'0')+'</span>'+escape(b.title);button.onclick=()=>openBook(b.id);$('book-list').append(button);}
 if(book)for(const c of book.chapters){const button=document.createElement('button');button.dataset.chapter=c.number;button.textContent=c.title;button.className=chapter?.number===c.number?'active':'';button.onclick=()=>openChapter(c.number,current?.mode||'learn');$('chapter-list').append(button);}
}
function renderShelf(){
 $('shelf').replaceChildren();if(!library)return;library.books.forEach((b,i)=>{const button=document.createElement('button');button.className='shelf-card';button.innerHTML=`<div class="cover"><div class="num">BOOK ${String(i+1).padStart(2,'0')}</div><h2>${escape(b.title)}</h2><p>${escape(b.subtitle)}</p></div><div class="shelf-meta"><span>${b.source_count} 章 · 四模式阅读</span><span class="arrow">↗</span></div>`;button.onclick=()=>openBook(b.id);$('shelf').append(button);});
 const last=state.settings.documentReaderLast;$('resume').textContent=last?'继续上次阅读 →':'开始阅读 →';
}
async function loadDocument(url){if(cache.has(url))return cache.get(url);loadingController?.abort();loadingController=new AbortController();const data=await readJSON(url,{signal:loadingController.signal});if(!data||data.schema!=='book-reflow-document-v1'||!Array.isArray(data.blocks))throw Error('文档内容不完整，未显示错误的替代内容。');if(cache.size>8)cache.delete(cache.keys().next().value);cache.set(url,data);return data;}
async function openBook(id){const req=++navigationRequest;const saving=savePosition().catch(()=>{});busy=true;++renderToken;await saving;if(req!==navigationRequest)return;book=library.books.find(b=>b.id===id);if(!book){busy=false;return;}const last=state.settings.documentReaderLast;const number=last?.book_id===id?last.chapter:1;await openChapter(number,last?.book_id===id?last.mode:'learn');}
async function openChapter(number,mode='learn'){
 const request=++navigationRequest;
 if(!book)return;const newChapter=book.chapters.find(c=>c.number===Number(number));if(!newChapter)return;
 const saving=current&&!busy?savePosition().catch(()=>{}):Promise.resolve();busy=true;++renderToken;await saving;if(request!==navigationRequest)return;chapter=newChapter;mode=chapter.modes[mode]?mode:'learn';const ref=chapter.modes[mode];
 ++renderToken;busy=true;$('welcome').hidden=true;$('workspace').hidden=false;$('loading').hidden=false;$('loading').textContent='正在打开 '+book.title+' · '+MODES[mode]+'…';
 renderNav();for(const button of $$('[data-mode]')){button.classList.toggle('active',button.dataset.mode===mode);button.setAttribute('aria-selected',button.dataset.mode===mode);button.disabled=!chapter.modes[button.dataset.mode];}
 $('crumb-book').textContent=book.title;$('crumb-chapter').textContent=chapter.title;const requested=ref.id;
 try{
  const data=await loadDocument(ref.url);if(request!==navigationRequest||chapter.modes[mode]?.id!==requested||book.id!==data.book_id)return;current=data;selected=null;answersHidden=mode==='practice';revealedAnswers.clear();reviewRecall=false;revealedReviewSections.clear();practiceCursor=Number((current.questions||[])[0]?.number)||1;editorBlock=null;document.documentElement.dataset.readerMode=mode;document.documentElement.dataset.reviewRecall='false';
  $('selection-tools').hidden=true;$('original-pdf').href=current.source_pdf.url;$('original-pdf').title=current.source_pdf.name;$('answer-toggle').hidden=mode!=='practice';$('practice-draft-open').hidden=mode!=='practice';$('practice-tab').hidden=mode!=='practice';if(mode!=='practice'&&notesTab==='practice')notesTab='notes';$('answer-toggle').textContent='遮住答案';$('find-input').value='';$('findbar').hidden=true;searchHits=[];searchIndex=-1;
  if(!state.settings.documentReader?.leading)prefs.leading=data.page_style.leading;
  if(!state.settings.documentReader?.margin)prefs.margin=data.page_style.left_mm;
  const anchor=state.books[book.id]?.documentPositions?.[data.id];const i=book.chapters.findIndex(c=>c.number===number);$('previous-chapter').disabled=i<=0;$('next-chapter').disabled=i>=book.chapters.length-1;
  document.title=book.title+' · '+MODES[mode]+' — Book 1.3.1';refreshContentStatus();renderModeGuide();await paginate(anchor);await mutate(s=>{s.settings.documentReaderLast={book_id:data.book_id,chapter:number,mode};});
 }catch(e){if(e.name==='AbortError')return;busy=false;$('loading').textContent='打开失败：'+e.message+'。没有替换为旧版内容。';messageError(e);}
}
function chooseBlock(event){
 const el=event.target.closest?.('[data-block-id]');if(!el||!current)return;const b=current.blocks.find(x=>x.id===el.dataset.blockId);if(!b)return;
 $$('.focus-block',$('pages')).forEach(x=>x.classList.remove('focus-block'));el.classList.add('focus-block');selected={block_id:b.id,quote:'',element:el};
 $('selection-quote').textContent=plainHTML(localCopy(b)?.html||b.html).slice(0,220)||b.plain.slice(0,220);
}
function captureSelection(){
 const sel=window.getSelection();if(!sel||sel.isCollapsed||!sel.rangeCount){$('selection-tools').hidden=true;return;}
 const r=sel.getRangeAt(0);let n=r.startContainer.nodeType===1?r.startContainer:r.startContainer.parentElement;const el=n.closest?.('#pages [data-block-id]');
 if(!el||!current){$('selection-tools').hidden=true;return;}
 const quote=sel.toString().trim();if(!quote)return;selected={block_id:el.dataset.blockId,quote:quote.slice(0,3000),element:el};$('selection-quote').textContent=quote.slice(0,450);
 const box=r.getBoundingClientRect(),t=$('selection-tools');t.style.left=Math.max(8,Math.min(window.innerWidth-190,box.left))+'px';t.style.top=Math.max(8,box.top-43)+'px';t.hidden=false;
}
function highlightQuote(root,quote,cls){
 if(!quote)return false;const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement?.closest('script,style,.math-render')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});let nodes=[],all='',n;
 while((n=walker.nextNode())){nodes.push({node:n,start:all.length});all+=n.data;}
 const start=all.indexOf(quote);if(start<0)return false;const end=start+quote.length;const first=nodes.find(x=>x.start+x.node.length>start),last=nodes.find(x=>x.start+x.node.length>=end);if(!first||!last)return false;
 const r=document.createRange();r.setStart(first.node,start-first.start);r.setEnd(last.node,end-last.start);const mark=document.createElement('mark');mark.className=cls;mark.append(r.extractContents());r.insertNode(mark);return true;
}
async function addNote(kind='document-note'){
 if(!current||!selected){toast('先选中文字，或点一下要批注的正文段落。');return;}
 const text=$('note-text').value.trim(),selection=clone({block_id:selected.block_id,quote:selected.quote});if(kind==='document-note'&&!text){toast('先写下你的想法。');return;}
 const b=current.blocks.find(x=>x.id===selection.block_id);if(!b)return;
 const id='doc:annotation:'+crypto.randomUUID(),value={kind,text,quote:selection.quote||b.plain.slice(0,180),block_id:b.id,record_id:b.id,document_id:current.id,book_id:current.book_id,source_sha:current.source_pdf.sha256,chapter:current.chapter,mode:current.mode,created_at:new Date().toISOString()};
 await mutate(s=>{s.notes[id]=value;});$('note-text').value='';$('selection-tools').hidden=true;renderNotes();
 for(const el of $$('[data-block-id]',$('pages')).filter(el=>el.dataset.blockId===b.id)){el.classList.add('has-note');if(kind==='document-highlight'){if(!highlightQuote(el,value.quote,'saved-highlight'))el.classList.add('highlighted');}}
 toast(kind==='document-highlight'?'已高亮，随字号和分页保留。':'批注已保存到本机。');
}
function renderNotes(){
 $('notes-list').replaceChildren();if(!current)return;$('practice-panel').hidden=notesTab!=='practice';$('notes-panel').classList.toggle('practice-open',notesTab==='practice');$$('[data-notes]').forEach(x=>x.classList.toggle('active',x.dataset.notes===notesTab));if(notesTab==='practice'){renderPractice();return;}const entries=notesTab==='bookmarks'?bookmarks():noteEntries();$('note-count').textContent=noteEntries().length||'';
 if(!entries.length){const p=document.createElement('p');p.className='quote-hint';p.textContent=notesTab==='bookmarks'?'本章还没有书签。阅读时点击“☆ 书签”即可收藏当前位置。':'本章还没有批注。选中文字后可以高亮，或记录自己的理解。';$('notes-list').append(p);return;}
 for(const [key,n]of entries.sort((a,b)=>(b[1].created_at||'').localeCompare(a[1].created_at||''))){const article=document.createElement('article');article.className='annotation';const q=document.createElement('div');q.className='quote';q.textContent=n.quote||n.title||'书签';const p=document.createElement('p');p.textContent=n.text|| (n.kind==='document-highlight'?'选文高亮':'');const footer=document.createElement('footer');const date=document.createElement('span');date.textContent=(n.created_at||'').slice(0,10);const go=document.createElement('button');go.textContent='回到正文';go.onclick=()=>{if(!jumpToBlock(n.block_id))toast('当前版本找不到原锚点，记录仍保留。');};const del=document.createElement('button');del.textContent='删除';del.onclick=async()=>{if(!confirm('删除这一条'+(notesTab==='bookmarks'?'书签':'批注')+'？'))return;await mutate(s=>{delete s[notesTab==='bookmarks'?'bookmarks':'notes'][key];});renderNotes();await paginate(activeAnchor());};footer.append(date,go,del);article.append(q,p,footer);$('notes-list').append(article);}
}
async function addBookmark(){if(!current)return;const anchor=activeAnchor();if(!anchor)return;const b=current.blocks.find(x=>x.id===anchor.block_id);const id='doc:bookmark:'+current.id+':'+anchor.block_id,entry={kind:'document-bookmark',document_id:current.id,book_id:current.book_id,record_id:anchor.block_id,block_id:anchor.block_id,quote:(b?.plain||current.title).slice(0,180),offset:anchor.offset,chapter:current.chapter,mode:current.mode,created_at:new Date().toISOString()};await mutate(s=>{s.bookmarks[id]=entry;});toast('已收藏当前位置，重新分页后仍可跳回。');renderNotes();}
function showNotes(){if(!current){toast('打开一本书后即可批注。');return;}$('notes-panel').hidden=false;$('selection-tools').hidden=true;renderNotes();adjustZoom();}
function startEditing(){
 if(!current)return;const b=current.blocks.find(x=>x.id===selected?.block_id);if(!b){toast('先点击需要修改的正文段落。');return;}
 if(!b.editable){toast('原图或矢量公式保持原稿；可以添加批注说明。');return;}editorBlock=b;
 const editor=$('copy-editor');editor.innerHTML=sanitizeHTML(localCopy(b)?.html||b.html);$$('img,.math-render',editor).forEach(x=>x.contentEditable='false');$('edit-dialog').showModal();editor.focus();
}
async function saveCopy(){if(!editorBlock||!current)return;const raw=sanitizeHTML($('copy-editor').innerHTML);const existing=localCopy(editorBlock)?.html||editorBlock.html;
 const src=document.createElement('template'),tar=document.createElement('template');src.innerHTML=existing;tar.innerHTML=raw;
 const oldMath=$$('img[src]',src.content).map(x=>x.getAttribute('src'));const newMath=$$('img[src]',tar.content).map(x=>x.getAttribute('src'));for(const x of oldMath){const index=newMath.indexOf(x);if(index<0){toast('公式或图片受保护。请保留它们，数学修改可写入批注。');return;}newMath.splice(index,1);}
 const block=editorBlock,id=noteKey('copy',block.id),previous=localCopy(block);const entry={kind:'document-copy',text:plainHTML(raw),html:raw,record_id:block.id,block_id:block.id,document_id:current.id,book_id:current.book_id,source_sha:current.source_pdf.sha256,created_at:previous?.created_at||new Date().toISOString(),updated_at:new Date().toISOString(),history:[...(previous?.history||[]),...(previous?[{html:previous.html,at:previous.updated_at}]:[])].slice(-5)};
 await mutate(s=>{s.notes[id]=entry;});$('edit-dialog').close();await paginate({block_id:block.id});toast('个人副本已保存，教材原稿没有改变。');}
async function resetCopy(){if(!editorBlock)return;if(!confirm('移除此段的个人修改，恢复教材原稿？批注不会删除。'))return;const id=editorBlock.id;await mutate(s=>{delete s.notes[noteKey('copy',id)];});$('edit-dialog').close();await paginate({block_id:id});toast('已恢复原稿。');}
function renderPractice(keep=false){
 if(!current||current.mode!=='practice')return;const qs=current.questions||current.blocks.filter(b=>b.question_start).map(b=>({number:b.question_number,block_id:b.id,title:b.plain}));
 const chosen=Number($('practice-question').value)||1;if(!keep){$('practice-question').replaceChildren();for(const q of qs){const o=document.createElement('option');o.value=q.number;o.textContent=q.title.slice(0,50);$('practice-question').append(o);}$('practice-question').value=qs.some(q=>q.number===chosen)?chosen:(qs[0]?.number||1);}
 const number=Number($('practice-question').value);practiceCursor=number||practiceCursor;const key='doc:attempt:'+current.id+':q'+number;const item=state.cards[key];$('practice-answer').value=item?.answer||'';$('practice-save-info').textContent=item?'已保存 · '+(item.updated_at||'').replace('T',' ').slice(0,19):'输入后自动保存。先独立作答，再回正文展开参考解答。';$$('[data-rating]').forEach(x=>x.classList.toggle('active',item?.rating===x.dataset.rating));renderModeGuide();
}
let draftTimer=null;
function saveDraft(rating=null){
 if(!current||current.mode!=='practice')return;clearTimeout(draftTimer);const snapshot={doc:current.id,bid:current.book_id,sha:current.source_pdf.sha256,number:Number($('practice-question').value),answer:$('practice-answer').value};$('practice-save-info').textContent='正在保存草稿…';
 const write=async()=>{const key='doc:attempt:'+snapshot.doc+':q'+snapshot.number;await mutate(s=>{const old=s.cards[key]||{};s.cards[key]={...old,kind:'document-practice-draft',book_id:snapshot.bid,record_id:key,document_id:snapshot.doc,source_sha:snapshot.sha,question_number:snapshot.number,answer:snapshot.answer,rating:rating||old.rating||'unrated',updated_at:new Date().toISOString()};});$('practice-save-info').textContent='草稿已自动保存到本机';if(rating)$$('[data-rating]').forEach(x=>x.classList.toggle('active',x.dataset.rating===rating));renderModeGuide();};
 // Queue each edit immediately; the CAS writer serializes updates and preserves other data.
 write().catch(messageError);
}
function clearSearch(){for(const m of $$('.find-mark',$('pages'))){m.replaceWith(...m.childNodes);}for(const p of $$('.doc-block',$('pages')))p.normalize();searchHits=[];searchIndex=-1;$('find-count').textContent='';}
function findText(q){clearSearch();q=q.trim();if(!q)return;if(!searchReflow&&current&&((current.mode==='practice'&&answersHidden)||(current.mode==='review'&&reviewRecall))){searchReflow=true;answersHidden=false;reviewRecall=false;paginate(activeAnchor()).then(()=>{searchReflow=false;renderModeGuide();findText(q);}).catch(e=>{searchReflow=false;messageError(e);});return;}const source=$('pages');
 const walker=document.createTreeWalker(source,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.parentElement?.closest('.page-header,.page-footer,script,style,.math-render')?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});let nodes=[],n;while((n=walker.nextNode()))nodes.push(n);
 const query=q.toLocaleLowerCase();
 for(const node of nodes){const text=node.data,low=text.toLocaleLowerCase();let idx=low.indexOf(query);if(idx<0)continue;const frag=document.createDocumentFragment();let pos=0;while(idx>=0&&searchHits.length<1500){frag.append(document.createTextNode(text.slice(pos,idx)));const mark=document.createElement('mark');mark.className='find-mark';mark.textContent=text.slice(idx,idx+q.length);frag.append(mark);searchHits.push(mark);pos=idx+q.length;idx=low.indexOf(query,pos);}frag.append(document.createTextNode(text.slice(pos)));node.replaceWith(frag);}
 if(searchHits.length)moveSearch(1);else $('find-count').textContent='没有找到正文匹配';
}
function moveSearch(delta){if(!searchHits.length)return;if(searchIndex>=0)searchHits[searchIndex].classList.remove('current');searchIndex=(searchIndex+delta+searchHits.length)%searchHits.length;const m=searchHits[searchIndex];m.classList.add('current');const r=m.getBoundingClientRect();window.scrollTo({top:window.scrollY+r.top-200,behavior:'smooth'});$('find-count').textContent=`${searchIndex+1} / ${searchHits.length}`;}
function refreshAnswerVisibility(){if(!current)return;for(const a of $$('.doc-block[data-answer="1"]',$('pages'))){const q=Number(a.dataset.questionNumber)||0,open=current.mode!=='practice'||!answersHidden||revealedAnswers.has(q);if(a.classList.contains('source-answer-label')){a.classList.toggle('answer-label-closed',!open);a.setAttribute('aria-expanded',String(open));}else a.classList.toggle('answer-concealed',!open);} $('answer-toggle').textContent=answersHidden?'展开全部答案':'折叠全部答案';}
function showSettings(){for(const [id,v]of [['font-size',prefs.size],['font-number',prefs.size],['line-height',prefs.leading],['font-select',prefs.font],['margin',prefs.margin],['layout-select',prefs.layout]])$(id).value=v;$('clean-reading').checked=prefs.cleanReading!==false;$('leading-value').textContent=prefs.leading.toFixed(2);$('margin-value').textContent=prefs.margin+' mm';$('settings-dialog').showModal();}
async function applySettings(){const anchor=activeAnchor();prefs.size=clampFontSize($('font-number').value);prefs.leading=Math.min(2.6,Math.max(1.2,Number($('line-height').value)||1.62));prefs.margin=Math.min(30,Math.max(12,Number($('margin').value)||20));prefs.font=$('font-select').value;prefs.layout=$('layout-select').value;prefs.cleanReading=true;$('settings-dialog').close();await settingSave();applyPrefs();if(current)await paginate(anchor);}
async function loadFont(){try{const r=await fetch('/api/font');if(!r.ok)return false;const face=new FontFace('BookLocalFont',await r.arrayBuffer(),{weight:'400'});await face.load();if(customFace)document.fonts.delete(customFace);customFace=face;document.fonts.add(face);return true;}catch(e){console.warn('Local font unavailable',e);return false;}}
async function importFont(file){if(!file)return;try{if(file.size>40*1024*1024)throw Error('字体文件超过40MB。');const data=await file.arrayBuffer();const face=new FontFace('BookLocalFont',data,{weight:'400'});await face.load();const r=await fetch('/api/font',{method:'POST',headers:{'X-Book-Token':token},body:data});if(!r.ok)throw Error((await r.json()).error||'字体导入失败');if(customFace)document.fonts.delete(customFace);customFace=face;document.fonts.add(face);prefs.font='custom';$('font-select').value='custom';await settingSave();toast('已导入并验证本地字体，应用排版后生效。');}catch(e){toast('字体未导入，原字体保留：'+e.message);}}
function downloadFile(name,text,type='application/json'){const a=document.createElement('a');const url=URL.createObjectURL(new Blob([text],{type}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
async function exportBackup(){await saveQueue.catch(()=>{});const payload={schema:'book-document-backup-v1',build:'20260929-windows-1.3.0-final-r2',created_at:new Date().toISOString(),includes_unsaved_changes:failedMutations.length>0,state:pendingSnapshot()};downloadFile('Book-全部学习记录-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json',JSON.stringify(payload,null,2));toast('备份已交给浏览器保存。');}
async function importBackup(file){if(!file)return;try{if(file.size>30*1024*1024)throw Error('备份过大。');const data=JSON.parse(await file.text());const incoming=validateBackup(data.state||data.data?.state||data);if(!confirm('合并这份学习备份？同名记录以导入内容为准；其他现有记录保留。'))return;await exportBackup();await mutate(s=>{for(const k of ['settings','books','notes','bookmarks','cards'])s[k]={...s[k],...incoming[k]};});prefs={...DEFAULTS,...state.settings.documentReader};if(prefs.font==='song')prefs.font='shusong';prefs.cleanReading=true;applyPrefs();$('backup-dialog').close();if(current)await paginate(activeAnchor());toast('备份已合并，原当前副本已先导出。');}catch(e){messageError(e);}}
async function printDocument(){
 if(!current||busy||printing){toast('请等文档排版完成后再打印。');return;}
 printing=true;const saved={layout:prefs.layout,anchor:activeAnchor(),hidden:answersHidden,answers:new Set(revealedAnswers),recall:reviewRecall,sections:new Set(revealedReviewSections)};let restored=false;
 const restore=async()=>{if(restored)return;restored=true;window.removeEventListener('afterprint',restore);prefs.layout=saved.layout;answersHidden=saved.hidden;revealedAnswers=saved.answers;reviewRecall=saved.recall;revealedReviewSections=saved.sections;printing=false;await paginate(saved.anchor);renderModeGuide();};
 try{
  prefs.layout='pages';answersHidden=false;reviewRecall=false;await paginate(saved.anchor);
  const images=$$('img',$('pages')).filter(i=>!i.closest('.reading-noise')&&i.getBoundingClientRect().height>0);for(const im of images)im.loading='eager';
  toast('正在准备完整A4页面，打印将包含已展开的参考解答。');
  await Promise.race([Promise.all(images.map(im=>im.complete?Promise.resolve():new Promise(r=>{im.addEventListener('load',r,{once:true});im.addEventListener('error',r,{once:true});}))),new Promise(r=>setTimeout(r,30000))]);
  if(images.some(im=>!im.complete||!im.naturalWidth))throw Error('仍有图片未就绪，已取消打印准备以免缺图。');
  await document.fonts.ready;window.addEventListener('afterprint',restore,{once:true});window.print();
 }catch(e){toast(e.message);await restore();}
}
async function quitApp(){
 if($('edit-dialog').open||$('note-text').value.trim()){toast('请先保存或关闭未完成的个人编辑/批注。');return;}
 try{await savePosition();await saveQueue;if(failedMutations.length)throw Error('仍有未保存修改，请先备份。');if(!confirm('退出 Book？已保存的学习记录保留。'))return;const r=await fetch('/api/quit',{method:'POST',headers:{'X-Book-Token':token}});if(!r.ok)throw Error('退出请求失败。');window.close();status('Book已退出，窗口可以关闭。');}catch(e){messageError(e);}
}
let contentAudit=null;
const REVIEW_NAMES={REASONING_REVIEWED:'本轮推理复核',REVISED_AND_REASONED:'已修订并复核',NOT_YET_INDIVIDUALLY_REVIEWED:'待逐题复核',QUESTION_LIST_REMOVED_REVIEW_PENDING:'题单已隔离，解答待复核'};
function refreshContentStatus(){
 if(!current)return;const n=current.correction_ids?.length||0;
 $('content-status').textContent=(current.mode==='learn'?'学习正文排印稿':'六本统一 v4 基准')+' · '+(n?'本章已校订 '+n+' 项':'原内容保留')+' · 未经全书学科终审';
 $('content-audit-open').textContent='内容校核'+(n?' ('+n+')':'');
 $('original-pdf').textContent=(current.mode==='learn'?'学习原 PDF':'v4 原 PDF')+' ↗';
 $('original-pdf').title=current.source_pdf.name+(n?'；原 PDF 不含本轮派生层校訂，请以校核记录区分。':'');
}
async function auditData(){if(!contentAudit)contentAudit=await readJSON('/documents/content-audit.json');return contentAudit;}
function auditParagraph(parent,text,cls=''){const p=document.createElement('p');p.textContent=text;if(cls)p.className=cls;parent.append(p);return p;}
async function showContentAudit(){
 if(!current)return toast('请先打开一本书。');const dlg=$('content-audit-dialog'),body=$('content-audit-body');body.replaceChildren();auditParagraph(body,'正在读取校核记录…');dlg.showModal();
 try{const data=await auditData(),s=data.summary;body.replaceChildren();
 auditParagraph(body,current.book_title+' · '+current.title+' · '+MODES[current.mode],'audit-current');
 auditParagraph(body,'本版本：'+s.version+' / '+s.content_revision+'。186份配套采用六本v4，67份学习正文保留结构化来源。v4排版通过不等于答案正确。');
 auditParagraph(body,'题目来源组 '+s.question_groups+'；本轮推理复核 '+s.individually_reasoning_reviewed+'；其中重写或补全 '+s.rewritten_or_completed_answers+'；其余 '+s.unreviewed_question_groups+' 组尚未逐题复核。未对全书学习事实或复习完整性作终审保证。','audit-scope');
 const cleanup=current.reader_cleanup_summary;
 if(cleanup){
  const h=document.createElement('h3');h.textContent='阅读层整理';body.append(h);
  auditParagraph(body,'本章为阅读连续性整理 '+cleanup.reader_modified_blocks+' 段，另将 '+cleanup.audit_only_blocks+' 段来源/脚注/技术说明移出正文。原始 plain/html、来源 PDF、题目与 source record 均未删除。','audit-scope');
  if((current.reader_audit_notes||[]).length){const det=document.createElement('details'),su=document.createElement('summary');su.textContent='查看移出正文或简化显示的来源/脚注说明（'+current.reader_audit_notes.length+' 条）';det.append(su);for(const note of current.reader_audit_notes){const row=document.createElement('div');row.className='audit-entry';const label=document.createElement('strong');label.textContent=(note.reason||'reader-cleanup')+' · '+(note.block_id||'段落');row.append(label);auditParagraph(row,note.text||'');if(note.reader_text)auditParagraph(row,'阅读显示：'+note.reader_text,'audit-reader-view');det.append(row);}body.append(det);}
 }
 if(current.mode==='practice'){
 const h=document.createElement('h3');h.textContent='本章逐题状态';body.append(h);
 for(const q of current.questions||[]){const p=document.createElement('div');p.className='audit-question';const btn=document.createElement('button');btn.textContent='第 '+q.number+' 题';btn.onclick=()=>{dlg.close();jumpToBlock(q.block_id);};const v=document.createElement('span');v.textContent=REVIEW_NAMES[q.review?.status]||'待逐题复核';p.append(btn,v);body.append(p);}
 }
 const preview=data.preview_screen.find(x=>x.document_id===current.id);if(preview){auditParagraph(body,'预习检查：'+(preview.logic_review==='REVIEWED_SPECIFIC_BRIDGE'?'已补本章逻辑衔接与有答案自检':preview.logic_review==='GOALS_SOURCE_RESTORED_OTHER_LOGIC_PENDING'?'真实学习目标已回原书恢复；其余逻辑仍需逐节复核':'目前仅做栏目结构筛查，不能证明教学逻辑完整')+'。');}
 const review=data.review_screen.find(x=>x.document_id===current.id);if(review){auditParagraph(body,'复习检查：'+(review.supplemented?'本章已加入有依据的知识补充。':'尚未完成逐知识点完整性终审。')+'与学习正文标题未匹配的候选 '+review.unmatched_heading_candidates.length+' 项（仅供复查，不自动判定为遗漏）。');if(review.unmatched_heading_candidates.length){const det=document.createElement('details'),su=document.createElement('summary');su.textContent='查看待核对小节标题';det.append(su);auditParagraph(det,review.unmatched_heading_candidates.join('；'));body.append(det);}}
 const learn=data.learning_screen.find(x=>x.document_id===current.id);if(learn&&learn.explicit_ocr_control_tokens) auditParagraph(body,'本章仍有 '+learn.explicit_ocr_control_tokens+' 处显式OCR控制标记，原始来源保留；不能理解为全文已无错误。','audit-scope');
 const items=data.items.filter(x=>x.document_id===current.id);const heading=document.createElement('h3');heading.textContent='本章已应用修订 '+items.length+' 项';body.append(heading);
 for(const item of items){const det=document.createElement('details');det.className='audit-entry';const su=document.createElement('summary');su.textContent=item.id+' · '+item.title;det.append(su);auditParagraph(det,item.reason);auditParagraph(det,'类型：'+item.kind+'。这是Book编辑校核，不是出版社官方勘误。');
 const before=document.createElement('pre');before.textContent=item.before||'（原稿没有这一补充）';const after=document.createElement('pre');after.textContent=item.after;const l1=document.createElement('h4');l1.textContent='原内容（保留）';const l2=document.createElement('h4');l2.textContent='本轮内容';det.append(l1,before,l2,after);auditParagraph(det,'依据：'+item.evidence.join('；'));body.append(det);}
 auditParagraph(body,'个人数据保护：只将唯一且文字完全相同的旧段落锚点映射到新段落；修改过的教材内容不自动覆盖或迁移个人副本。无法自动定位的笔记仍保留，可备份或在个人历史中查看。');
 }catch(e){body.replaceChildren();auditParagraph(body,'校核记录读取失败：'+e.message);}
}
async function showPersonalHistory(){
 const body=$('content-audit-body');body.replaceChildren();auditParagraph(body,'本章历史个人副本（只读，不会自动覆盖新版正文）','audit-current');
 const entries=Object.values(state.notes||{}).filter(n=>n.document_id===current?.id&&n.kind==='document-copy');
 if(!entries.length)auditParagraph(body,'本章没有已保存的个人副本。');
 for(const n of entries){const det=document.createElement('details'),su=document.createElement('summary');su.textContent=(n.updated_at||n.created_at||'')+' · '+(n.block_id||'段落');det.append(su);const pre=document.createElement('pre');pre.textContent=plainHTML(n.html||n.text||'');det.append(pre);body.append(det);}
}
function bind(){
 bindStudySharing();
 $('quit-app').onclick=quitApp;$('comfortable-layout').onclick=()=>{$('font-number').value=18;$('font-size').value=18;$('line-height').value=1.62;$('leading-value').textContent='1.62';};
 $('content-package').onclick=openContentPackageDialog;$('content-missing-install').onclick=openContentPackageDialog;$('content-missing-reload').onclick=reloadContentPackage;$('content-package-file').onchange=e=>{$('content-install').disabled=!e.target.files?.[0];$('content-upload-text').textContent=e.target.files?.[0]?(e.target.files[0].name+' · '+formatBytes(e.target.files[0].size)):'等待选择文件';};$('content-install').onclick=()=>installContentPackage($('content-package-file').files?.[0]);$('content-reload').onclick=reloadContentPackage;
 $('content-audit-open').onclick=showContentAudit;$('content-audit-close').onclick=()=>$('content-audit-dialog').close();
 $('audit-export').onclick=async()=>{const d=await auditData();downloadFile('Book-1.3-内容校核.json',JSON.stringify(d,null,2));};
 $('personal-history').onclick=showPersonalHistory;
 $('pdf-style-reset').onclick=async()=>{if(!current)return;const a=activeAnchor();prefs={...prefs,size:12,leading:current.page_style.leading,margin:current.page_style.left_mm,layout:'pages',zoom:'fit'};await settingSave();applyPrefs();await paginate(a);toast('已采用本册PDF的默认字号、行距和边距；字体与个人记录保留。');};

 $('fullscreen').onclick=toggleFullscreen;$('immersive').onclick=toggleImmersive;$('focus-fullscreen').onclick=toggleFullscreen;$('focus-exit').onclick=()=>setImmersive(false);$('focus-settings').onclick=showSettings;$('focus-nav').onclick=()=>{setImmersive(false);document.body.classList.remove('nav-hidden');adjustZoom();};document.addEventListener('fullscreenchange',updateFullscreenUI);
 $('home').onclick=async()=>{await savePosition().catch(()=>{});++renderToken;current=null;book=null;chapter=null;if(studySharing)await publishStudyPresence('stopped').catch(messageError);$('workspace').hidden=true;$('notes-panel').hidden=true;$('pages').replaceChildren();if(library){$('content-missing').hidden=true;$('welcome').hidden=false;renderNav();renderShelf();}else showContentMissing(contentPackage);$('crumb-book').textContent='阅读是一段安静的旅程';$('crumb-chapter').textContent='';document.title='Book · 纸页与自由';window.scrollTo(0,0);};
 $('resume').onclick=()=>{if(!library){openContentPackageDialog();return;}openBook(state.settings.documentReaderLast?.book_id||library.books[0].id);};
 $('toggle-nav').onclick=() => {document.body.classList.toggle('nav-hidden');adjustZoom();};$('collapse-nav').onclick=$('toggle-nav').onclick;
 $('theme').onclick=async()=>{prefs.theme=prefs.theme==='dark'?'light':'dark';applyPrefs();await settingSave();};$('settings').onclick=showSettings;$('apply-settings').onclick=applySettings;
 $('font-size').oninput=e=>$('font-number').value=e.target.value;$('font-number').oninput=e=>$('font-size').value=e.target.value;
 $('line-height').oninput=e=>$('leading-value').textContent=Number(e.target.value).toFixed(2);$('margin').oninput=e=>$('margin-value').textContent=e.target.value+' mm';$('font-file').onchange=e=>importFont(e.target.files[0]);
 $('reset-layout').onclick=async()=>{const anchor=activeAnchor();prefs={...prefs,size:12,leading:current?.page_style.leading||1.62,margin:current?.page_style.left_mm||20,font:'shusong',layout:'pages',zoom:'fit'};await settingSave();$('settings-dialog').close();applyPrefs();if(current)await paginate(anchor);};
 $('layout-toggle').onclick=async()=>{const anchor=activeAnchor();prefs.layout=prefs.layout==='pages'?'continuous':'pages';await settingSave();await paginate(anchor);};
 $('zoom-out').onclick=()=>{const currentZoom=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--view-zoom'))||1;prefs.zoom=Math.max(.3,currentZoom-.1);adjustZoom();settingSave();};$('zoom-in').onclick=()=>{const currentZoom=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--view-zoom'))||1;prefs.zoom=Math.min(1.8,currentZoom+.1);adjustZoom();settingSave();};$('zoom-fit').onclick=()=>{prefs.zoom='fit';adjustZoom();settingSave();};
 $$('[data-mode]').forEach(b=>b.onclick=()=>openChapter(chapter.number,b.dataset.mode));$('mode-primary').onclick=modePrimaryAction;$('mode-secondary').onclick=modeSecondaryAction;
 $('previous-chapter').onclick=()=>{const i=book.chapters.findIndex(x=>x.number===chapter.number);if(i>0)openChapter(book.chapters[i-1].number,current.mode);};$('next-chapter').onclick=()=>{const i=book.chapters.findIndex(x=>x.number===chapter.number);if(i<book.chapters.length-1)openChapter(book.chapters[i+1].number,current.mode);};
 $('pages').addEventListener('pointerdown',chooseBlock);$('pages').addEventListener('pointerup',()=>setTimeout(captureSelection,15));
 $('pages').addEventListener('click',e=>{const label=e.target.closest('.source-answer-label[data-question-number]');if(label&&current?.mode==='practice'){e.preventDefault();togglePracticeAnswer(label.dataset.questionNumber);return;}const hidden=e.target.closest('.answer-concealed[data-question-number]');if(hidden&&current?.mode==='practice'){e.preventDefault();togglePracticeAnswer(hidden.dataset.questionNumber);return;}const h=e.target.closest('.review-section-title[data-review-section]');if(h&&current?.mode==='review'&&reviewRecall){e.preventDefault();toggleReviewSection(h.dataset.reviewSection,h.dataset.blockId);}});
 $('pages').addEventListener('dblclick',async e=>{const im=e.target.closest('img');if(!im)return;if(im.classList.contains('source-figure')){const w=window.open(im.src,'_blank','noopener');return;}const t=im.dataset.latex||im.alt;try{await navigator.clipboard.writeText(t);toast(im.dataset.latex?'LaTeX 已复制。':'已复制来源公式文字；未将它冒充可编辑 LaTeX。');}catch{toast('请使用右键复制，剪贴板不可用。');}});
 $('toggle-notes').onclick=()=>{$('notes-panel').hidden?showNotes():($('notes-panel').hidden=true);adjustZoom();};$('close-notes').onclick=()=>{$('notes-panel').hidden=true;adjustZoom();};
 $('add-note').onclick=()=>addNote('document-note').catch(messageError);$('highlight').onclick=$('selection-highlight').onclick=()=>addNote('document-highlight').catch(messageError);$('selection-note').onclick=()=>{showNotes();$('note-text').focus();};$('selection-copy').onclick=async()=>{try{await navigator.clipboard.writeText(selected?.quote||'');toast('已复制。');}catch{toast('请使用 Ctrl+C 复制。');}$('selection-tools').hidden=true;};
 $$('[data-notes]').forEach(b=>b.onclick=()=>{notesTab=b.dataset.notes;$$('[data-notes]').forEach(x=>x.classList.toggle('active',x===b));renderNotes();});
 $('practice-draft-open').onclick=openPracticePanel;$('practice-question').onchange=()=>{renderPractice(true);const q=current?.questions?.find(x=>x.number===Number($('practice-question').value));if(q)jumpToBlock(q.block_id);};$('jump-question').onclick=()=>{const q=current?.questions?.find(x=>x.number===Number($('practice-question').value));if(q){practiceCursor=q.number;jumpToBlock(q.block_id);renderModeGuide();}};$('practice-answer').oninput=()=>saveDraft();$$('[data-rating]').forEach(x=>x.onclick=()=>saveDraft(x.dataset.rating));
 $('bookmark').onclick=()=>addBookmark().catch(messageError);$('edit-copy').onclick=startEditing;$('save-copy').onclick=()=>saveCopy().catch(messageError);$('reset-copy').onclick=()=>resetCopy().catch(messageError);
 $$('[data-format]').forEach(b=>{b.onmousedown=e=>e.preventDefault();b.onclick=()=>document.execCommand(b.dataset.format);});
 $$('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
 $('answer-toggle').onclick=async()=>{const anchor=activeAnchor();answersHidden=!answersHidden;revealedAnswers.clear();await paginate(anchor);renderModeGuide();};
 $('find-toggle').onclick=()=>{if(!current)return;$('findbar').hidden=!$('findbar').hidden;if(!$('findbar').hidden)$('find-input').focus();else clearSearch();};$('find-close').onclick=()=>{$('findbar').hidden=true;clearSearch();};let searchTimer;$('find-input').oninput=e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>findText(e.target.value),250);};$('find-next').onclick=()=>moveSearch(1);$('find-prev').onclick=()=>moveSearch(-1);$('find-input').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();moveSearch(e.shiftKey?-1:1);}};
 $('print').onclick=()=>printDocument().catch(messageError);$('backup').onclick=()=>$('backup-dialog').showModal();$('export-backup').onclick=()=>exportBackup().catch(messageError);$('import-backup').onchange=e=>importBackup(e.target.files[0]);
 $('verify-app').onclick=async()=>{const button=$('verify-app');button.disabled=true;$('verify-output').textContent='正在逐项核对内容包…';try{const r=await fetch('/api/verify',{method:'POST',headers:{'X-Book-Token':token}});if(!r.ok)throw Error('校验请求失败');$('verify-output').textContent=JSON.stringify(await r.json(),null,2);}catch(e){$('verify-output').textContent=e.message;}finally{button.disabled=false;}};
 window.addEventListener('scroll',()=>{if(!busy){updatePosition();$('selection-tools').hidden=true;}},{passive:true});window.addEventListener('resize',()=>{const anchor=activeAnchor(),id=current?.id;adjustZoom();if(id&&prefs.layout==='continuous'){clearTimeout(reflowTimer);reflowTimer=setTimeout(()=>{if(current?.id===id&&prefs.layout==='continuous')paginate(anchor).catch(messageError);},180);}});
 window.addEventListener('keydown',e=>{if(e.key==='F11'){e.preventDefault();toggleFullscreen();return;}if(e.key==='Escape'){if(document.fullscreenElement){document.exitFullscreen().catch(()=>{});}if(document.body.classList.contains('immersive'))setImmersive(false);$('selection-tools').hidden=true;return;}if(isTypingTarget(e.target))return;if(e.altKey&&!e.ctrlKey&&!e.metaKey&&current&&['1','2','3','4'].includes(e.key)){e.preventDefault();const m=['preview','learn','review','practice'][Number(e.key)-1];if(chapter?.modes?.[m])openChapter(chapter.number,m);return;}if((e.key==='Enter'||e.key===' ')&&document.activeElement?.classList?.contains('source-answer-label')&&current?.mode==='practice'){e.preventDefault();togglePracticeAnswer(document.activeElement.dataset.questionNumber);return;}if((e.key==='Enter'||e.key===' ')&&document.activeElement?.classList?.contains('review-section-title')&&reviewRecall){e.preventDefault();toggleReviewSection(document.activeElement.dataset.reviewSection,document.activeElement.dataset.blockId);return;}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='f'&&current){e.preventDefault();$('findbar').hidden=false;$('find-input').focus();$('find-input').select();}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='p'&&current){e.preventDefault();printDocument();}if(!e.ctrlKey&&!e.metaKey&&!e.altKey&&e.key.toLowerCase()==='m'&&current){e.preventDefault();toggleImmersive();}});
 window.addEventListener('beforeunload',e=>{if(savePending||failedMutations.length||$('note-text').value.trim()||$('edit-dialog').open){e.preventDefault();e.returnValue='';}});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')savePosition().catch(()=>{});});
 setInterval(()=>fetch('/api/heartbeat').catch(()=>status('本机连接已断开',true)),30000);
}
async function boot(){
 try{
  await session();prefs={...DEFAULTS,...state.settings.documentReader};if(prefs.font==='song')prefs.font='shusong';prefs.cleanReading=true;prefs.size=clampFontSize(prefs.size);prefs.leading=Math.max(1.2,Math.min(2.6,Number(prefs.leading)||1.62));prefs.margin=Math.max(12,Math.min(30,Number(prefs.margin)||20));bind();applyPrefs();status('已连接本机存储');await loadFont();await detectLocalSerif();
  contentPackage={available:true,source:'embedded-exe',package_id:'book-six-body-only-1.3.1-local-rebuild',content_version:'1.3.1-local-rebuild',reader_books:6,reader_documents:249,bytes:0,sha256:''};
  await loadLibraryFromContent();const qs=new URLSearchParams(location.search);if(qs.get('book')){book=library.books.find(x=>x.id===qs.get('book')||x.key===qs.get('book'));if(book)await openChapter(Number(qs.get('chapter')||1),qs.get('mode')||'learn');}
  window.BookDocument={get current(){return current;},get library(){return library;},get contentPackage(){return contentPackage?{...contentPackage}:null;},get prefs(){return {...prefs};},get state(){return clone(state);},get busy(){return busy;},get revision(){return revision;},get unsavedCount(){return failedMutations.length+savePending;},setStudySharing,savePosition,get studySharing(){return studySharing;},studyProgress:()=>clone(state.settings.documentReaderLive??null),backupSnapshot:pendingSnapshot,openBook,openChapter,paginate,flush:()=>saveQueue,sourceText:()=>current?.blocks.map(b=>plainHTML(localCopy(b)?.html||b.html)).join('')||'',readerText:()=>current?.blocks.filter(b=>b.reader_visibility!=='audit_only').map(b=>plainHTML(localCopy(b)?.html||b.reader_html||b.html)).join('')||'',renderedText:()=>$$('.doc-block',$('pages')).filter(el=>el.dataset.blockId!==current?.id+'-title').map(el=>plainHTML(el.innerHTML)).join(''),printDocument,get printing(){return printing;},showContentAudit,resolveAnchor,toggleFullscreen,setImmersive,toggleImmersive,detectLocalSerif,renderModeGuide,togglePracticeAnswer,setReviewRecall,nextPracticeQuestion,refreshContentPackageStatus,loadLibraryFromContent,openContentPackageDialog,get reviewRecall(){return reviewRecall;},get revealedAnswers(){return [...revealedAnswers];},settings:async x=>{const anchor=activeAnchor();prefs={...prefs,...x};if(prefs.font==='song')prefs.font='shusong';prefs.cleanReading=true;await settingSave();applyPrefs();if(current)await paginate(anchor);}};
 }catch(e){$('welcome').hidden=true;$('content-missing').hidden=false;$('content-missing').innerHTML='<div class="content-missing-card"><h1>无法启动阅读器</h1><p>'+escape(e.message)+'</p><p>个人学习记录没有被覆盖。请重新打开程序后重试。</p></div>';messageError(e);}
}
boot();
})();

