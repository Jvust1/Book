'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const crypto=require('node:crypto').webcrypto;
const P=require('../book_mygpt_selection/web/projection.js');
const registry=new Map();

class Element {
  constructor(tag='div',text='') {
    this.tagName=tag.toUpperCase();this.textContent=text;this.children=[];this.listeners={};
    this.attributes={};this.dataset={};this.className='';this.classList={add(){},remove(){},toggle(){}};
    this.hidden=false;this.disabled=false;this.value='';this.parentElement=null;this._id='';
  }
  get id(){return this._id;}
  set id(value){if(this._id)registry.delete(this._id);this._id=value;if(value)registry.set(value,this);}
  append(...nodes){for(const node of nodes){this.children.push(node);node.parentElement=this;}}
  prepend(node){this.children.unshift(node);node.parentElement=this;}
  after(node){this.next=node;node.parentElement=this;}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  async dispatch(type,event={}){for(const fn of this.listeners[type]||[])await fn({target:this,preventDefault(){},...event});}
  setAttribute(k,v){this.attributes[k]=String(v);if(k==='id')this.id=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];if(k==='id')this.id='';}
  focus(){}
  scrollIntoView(){}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(x=>x!==this);}
}
const ids=['bridge-connect','bridge-choose','bridge-revoke','bridge-share','bridge-explain',
  'bridge-cancel','bridge-clear','bridge-layer','bridge-representation','bridge-preview',
  'bridge-status','bridge-selection-panel','bridge-reply','notebook'];
for(const id of ids){const e=new Element(id==='bridge-layer'||id==='bridge-representation'?'select':'div');e.id=id;}
const byId=registry;
byId.get('notebook').hidden=true;
const picks=[];
const record={
  id:'record-1',section_id:'section-1',title:'Test segment',
  parts:[{kind:'text',text:'Original source'}],
  source_completion:{id:'completion-1',origin:'source_visual_transcription_not_generated_proof',
    parts:[{kind:'text',text:'Supplemental source'}]},
  corrections:[{id:'correction-1',record_id:'record-1',course_id:'course-1',section_id:'section-1',
    confidence:'HIGH',presentation:'prefer_corrected',status:'CHECKED_BY_ASSISTANT',
    evidence_status:'SCOPED_EVIDENCE_CHECKED',source_preserved:true,check_ids:['check-1'],
    original_title:'Test segment',original_parts:[{kind:'text',text:'Original source'}],
    corrected_parts:[{kind:'text',text:'AI-corrected source'}]}]
};
const article=new Element('article');article.dataset.recordId=record.id;
const course={course_id:'course-1',book_id:'book-1',book_version_id:'book@v1',
  sections:[{id:'section-1'}]};
const section={id:'section-1',records:[record],practice_groups:[]};
const header=new Element('header'),body=new Element('body');
const document={
  body,createElement:tag=>new Element(tag),getElementById:id=>registry.get(id)||null,
  querySelector:selector=>selector==='header'?header:null,
  querySelectorAll(selector){
    if(selector==='.bridge-pick')return picks.filter(x=>x.parentElement);
    if(selector==='#content .record[data-record-id]')return[article];
    return[];
  },
  addEventListener(){}
};
const response=(value)=>({ok:true,status:200,json:async()=>value});
const calls=[];
async function fetch(url,options){
  const action=String(url).split('/').at(-1);calls.push({action,options});
  if(action==='authorize')return response({session:{last_sequence:0,expires_at_ms:Date.now()+60000}});
  return response({state:'ok'});
}
const window={BookSelectionProjection:P,addEventListener(){}};
const context={window,document,crypto,fetch,AbortController,Date,Promise,Map,Set,Array,Object,String,JSON,
  TextEncoder,Uint8Array,setInterval:()=>1,clearInterval(){}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../book_mygpt_selection/web/bridge.js'),'utf8'),context);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
async function click(element){await element.dispatch('click');await settle();await settle();}

(async()=>{
  window.BookCompanionBridge.rendered({course,section,mode:'learn'});
  await click(byId.get('bridge-connect'));
  assert.equal(byId.get('bridge-choose').disabled,false,'connected Reader context should allow a deliberate segment choice');
  await click(byId.get('bridge-choose'));
  const pick=article.children.find(x=>x.className==='bridge-pick');
  assert.ok(pick,'explicit record selection control should be present');
  await click(pick);
  const layer=byId.get('bridge-layer'),share=byId.get('bridge-share'),preview=byId.get('bridge-preview');
  assert.equal(layer.children.length,4,'multiple available source layers plus an explicit placeholder');
  assert.equal(layer.value,'','a multi-layer record must start with no layer selected');
  assert.equal(share.disabled,true,'sharing must stay unavailable before an explicit layer choice');
  assert.match(preview.textContent,/请选择/,'the preview should ask the user to choose a source layer');
  layer.value='1';
  await layer.dispatch('change');
  await settle();await settle();
  assert.equal(share.disabled,false,'an explicit layer choice unlocks the read-only share confirmation');
  assert.match(preview.textContent,/补录正文/,'the preview must follow the selected completion layer');
  assert.doesNotMatch(preview.textContent,/AI 校正/,'a different eligible layer must never be selected implicitly');
  assert.equal(calls.filter(x=>x.action==='select').length,0,'previewing a layer must not grant it automatically');
  console.log('PASS: multi-layer segment remains unshared until the user chooses and previews one exact layer');
})().catch(error=>{console.error(error);process.exitCode=1;});
