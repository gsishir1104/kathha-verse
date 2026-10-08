const fs=require('fs'),ts=require('./frontend/node_modules/typescript'),Module=require('module'),assert=require('node:assert/strict');
function load(name){const m=new Module(name);m.paths=[__dirname+'/frontend/node_modules'];m._compile(ts.transpileModule(fs.readFileSync(__dirname+'/frontend/app/'+name+'.ts','utf8'),{compilerOptions:{esModuleInterop:true,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,name+'.js');return m.exports}
const {overviewGraph,branchingLayout}=load('graph-layout');const {buildUniverseGraph,orderedEvents}=load('universe-model');
const items=Array.from({length:49},(_,i)=>({id:String(i),name:'Character '+i,kind:'character',summary:'',evidence:''}));
const connections=items.slice(1).map((n,i)=>({id:'e'+i,source:'0',target:n.id,label:'knows',generic:false,evidence:''}));
const graph={items,connections};const all=new Set();
for(let page=0;page<6;page++){const shown=overviewGraph(graph,'0',page);assert(shown.items.length<=10);shown.items.forEach(n=>all.add(n.id));const {positions}=branchingLayout(shown);assert.equal(new Set([...positions.values()].map(p=>p.x+','+p.y)).size,shown.items.length)}
assert.equal(all.size,49);
assert.equal(overviewGraph({...graph,connections:connections.map(c=>({...c,generic:true}))}).connections.length,0);
assert.equal(overviewGraph(graph,'48').items.find(n=>n.id==='48').id,'48');
const entity={id:'a',name:'A',kind:'character',summary:'',evidence:'e',status:'confirmed',links:[],relations:[],knowledge:[],reader_safe:true,confidence:1};
const built=buildUniverseGraph({entities:[entity],facts:[{category:'relationship',text:'Statement',entity_ids:['a'],evidence:'e',order:1},{category:'event',text:'An event',entity_ids:['a'],evidence:'e',order:2}]});
assert(!built.items.some(n=>n.kind==='statement'));assert.equal(orderedEvents(built).unknown.length,1);
const cycle={items:items.slice(0,3),connections:[{...connections[0],source:'0',target:'1'},{...connections[0],source:'1',target:'0'}]};assert.equal(branchingLayout(cycle).positions.size,3);
console.log('Passed: 49-node pagination, every character reachable, bounded connections, no statement nodes, timeline retained, cycle-safe layout.');

