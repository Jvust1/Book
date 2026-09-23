const fs=require('node:fs'),path=require('node:path');
const P=require('../book_mygpt_selection/web/projection.js');
if(process.argv.length!==4)throw new Error('Usage: node project_vectors.cjs R6_ROOT OUTPUT_JSON');
(async()=>{
 const root=path.join(path.resolve(process.argv[2]),'coursepacks'),out=[];
 for(const cid of JSON.parse(fs.readFileSync(path.join(root,'catalog.json'))).courses){
  const m=JSON.parse(fs.readFileSync(path.join(root,cid,'manifest.json')));
  for(const meta of m.sections){
   const s=JSON.parse(fs.readFileSync(path.join(root,cid,'sections',meta.id+'.json')));
   const selections=[];
   for(const r of s.records){
    const options=[['source',null,'body']];
    if(r.source_completion)options.push(['completion',r.source_completion.id,'body']);
    for(const c of P.corrections(r,m,s))options.push(['correction',c.id,'body']);
    for(const [layer,layer_id,portion] of options)for(const representation of ['display','raw'])selections.push({course_id:cid,book_id:m.book_id,book_version_id:m.book_version_id,section_id:s.id,record_id:r.id,layer,layer_id,portion,representation});
   }
   for(const g of s.practice_groups||[])if(g.derived_guidance)for(const portion of ['hint','solution'])for(const representation of ['display','raw'])selections.push({course_id:cid,book_id:m.book_id,book_version_id:m.book_version_id,section_id:s.id,record_id:g.anchor_id,layer:'derived',layer_id:g.id,portion,representation});
   for(const selection of selections){try{out.push({selection,hash:await P.digest(await P.project(m,s,selection))});}catch(e){out.push({selection,error:e.message});}}
  }
 }
 fs.writeFileSync(process.argv[3],JSON.stringify(out),{flag:'wx'});console.log('JS projection results',out.length);
})();
