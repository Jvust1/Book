'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const crypto=require('node:crypto').webcrypto;
const P=require('../book_mygpt_selection/web/projection.js');

class Element {
  constructor(registry,tag='div',text='') {
    this.registry=registry;this.tagName=tag.toUpperCase();this.textContent=text;this.children=[];this.listeners={};
    this.attributes={};this.dataset={};this.className='';this.classList={add(){},remove(){},toggle(){}};
    this.hidden=false;this.disabled=false;this.value='';this.parentElement=null;this._id='';
  }
  get id(){return this._id;}
  set id(value){if(this._id)this.registry.delete(this._id);this._id=value;if(value)this.registry.set(value,this);}
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

function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return{promise,resolve,reject};}
const settle=()=>new Promise(resolve=>setImmediate(resolve));

function makeHarness({delaySelect=false}={}){
  const registry=new Map();
  const create=(tag,text)=>new Element(registry,tag,text);
  const ids=['bridge-connect','bridge-choose','bridge-revoke','bridge-share','bridge-explain',
    'bridge-cancel','bridge-clear','bridge-layer','bridge-representation','bridge-preview',
    'bridge-status','bridge-selection-panel','bridge-reply','notebook'];
  for(const id of ids){const e=create(id==='bridge-layer'||id==='bridge-representation'?'select':'div');e.id=id;}
  registry.get('notebook').hidden=true;
  const record={id:'record-1',section_id:'section-1',title:'Single source',parts:[{kind:'text',text:'raw',render_text:'display'}]};
  const article=create('article');article.dataset.recordId=record.id;
  const course={course_id:'course-1',book_id:'book-1',book_version_id:'book@v1',sections:[{id:'section-1'}]};
  const section={id:'section-1',records:[record],practice_groups:[]};
  const header=create('header'),body=create('body');
  const document={
    body,hidden:false,createElement:tag=>create(tag),getElementById:id=>registry.get(id)||null,
    querySelector:selector=>selector==='header'?header:null,
    querySelectorAll(selector){
      if(selector==='.bridge-pick')return article.children.filter(x=>x.className==='bridge-pick');
      if(selector==='#content .record[data-record-id]')return[article];
      return[];
    },
    addEventListener(){}
  };
  const calls=[];const selectGate=delaySelect?deferred():null;
  const response=value=>({ok:true,status:200,json:async()=>value});
  async function fetch(url,options){
    const action=String(url).split('/').at(-1);const body=options?.body?JSON.parse(options.body):{};calls.push({action,body});
    if(action==='authorize')return response({session:{last_sequence:0,expires_at_ms:Date.now()+60000}});
    if(action==='select'){
      if(selectGate)await selectGate.promise;
      return response({schema:'book.selection-lease.v1',expires_at_ms:Date.now()+60000,selection:body.selection,epoch:1});
    }
    return response({state:'ok'});
  }
  const window={BookSelectionProjection:P,addEventListener(){}};
  const context={window,document,crypto,fetch,AbortController,Date,Promise,Map,Set,Array,Object,String,JSON,
    TextEncoder,Uint8Array,setInterval:()=>1,clearInterval(){}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../book_mygpt_selection/web/bridge.js'),'utf8'),context);
  return {window,document,registry,article,course,section,calls,selectGate};
}

async function click(e){await e.dispatch('click');await settle();await settle();}
async function ready(h){
  h.window.BookCompanionBridge.rendered({course:h.course,section:h.section,mode:'learn'});
  await click(h.registry.get('bridge-connect'));
  await click(h.registry.get('bridge-choose'));
  const pick=h.article.children.find(x=>x.className==='bridge-pick');assert.ok(pick);await click(pick);
  await settle();
}

(async()=>{
  {
    const h=makeHarness();await ready(h);
    const rep=h.registry.get('bridge-representation');
    for(let i=0;i<8;i++){rep.value=i%2?'raw':'display';await rep.dispatch('change');await settle();}
    for(let i=0;i<40;i++)h.window.BookCompanionBridge.invalidate('paint');
    await settle();
    assert.equal(h.calls.filter(x=>x.action==='clear').length,0,
      'local preview/render invalidation must not consume server command receipts before a share exists');
    assert.equal(h.calls.filter(x=>x.action==='select').length,0);
  }
  {
    const h=makeHarness();await ready(h);await click(h.registry.get('bridge-share'));
    assert.equal(h.calls.filter(x=>x.action==='select').length,1);
    for(let i=0;i<40;i++)h.window.BookCompanionBridge.invalidate('paint');
    await settle();
    const clears=h.calls.filter(x=>x.action==='clear');
    assert.equal(clears.length,1,'one granted selection needs only one superseding clear');
    assert.ok(clears[0].body.sequence>h.calls.find(x=>x.action==='select').body.sequence);
  }
  {
    const h=makeHarness({delaySelect:true});await ready(h);
    const share=h.registry.get('bridge-share');
    const pendingClick=share.dispatch('click');await settle();await settle();
    assert.equal(h.calls.filter(x=>x.action==='select').length,1,'select must be in flight');
    for(let i=0;i<20;i++)h.window.BookCompanionBridge.invalidate('paint');
    await settle();
    const select=h.calls.find(x=>x.action==='select');const clears=h.calls.filter(x=>x.action==='clear');
    assert.equal(clears.length,1,'an in-flight select must be superseded exactly once');
    assert.ok(clears[0].body.sequence>select.body.sequence,'clear must use a higher authority sequence');
    h.selectGate.resolve();await pendingClick;await settle();
    assert.equal(h.registry.get('bridge-explain').disabled,true,'a late select result must not resurrect a ticket');
    assert.equal(h.registry.get('bridge-share').disabled,true,'invalidated draft stays unavailable after late select completion');
  }
  console.log('PASS: local browsing spends zero clear receipts; granted/in-flight selections are superseded once');
})().catch(error=>{console.error(error);process.exitCode=1;});
