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

const finalState=buildUniverseGraph({entities:[{...entity,id:'parent',relations:[{target_id:'child',label:'father of',scope:'current'}]},{...entity,id:'child',relations:[{target_id:'parent',label:'daughter of',scope:'current'},{target_id:'parent',label:'warns',scope:'history'}]}]},true);
assert.equal(finalState.connections.length,1);assert.equal(finalState.connections[0].label,'father of');
assert.equal(buildUniverseGraph({entities:[{...entity,relations:[{target_id:'b',label:'partner'}]},{...entity,id:'b'}]},true).connections.length,0);
console.log('Passed: current state excludes historical actions and unclassified legacy claims; inverse family edges consolidated.');
const legacy=buildUniverseGraph({entities:[{...entity,id:'king',relations:[{target_id:'sam',label:'father of'}]},{...entity,id:'sam',relations:[{target_id:'king',label:'daughter of'},{target_id:'abhi',label:'warns'},{target_id:'abhi',label:'partner'}]},{...entity,id:'abhi'}]},true);
assert.equal(legacy.connections.length,1);assert.equal(legacy.connections[0].label,'father of');assert.equal(legacy.items.length,3);
const disconnected=branchingLayout({items:items.slice(0,6),connections:[]});assert(disconnected.width<800);assert.equal(new Set([...disconnected.positions.values()].map(p=>p.x)).size,2);
console.log('Passed: legacy family connections preserved without inventing feelings; disconnected cards use a compact grid.');

const crashGraph={"items": [{"id": "n0", "name": "Node 0", "kind": "character"}, {"id": "n1", "name": "Node 1", "kind": "character"}, {"id": "n2", "name": "Node 2", "kind": "character"}, {"id": "n3", "name": "Node 3", "kind": "character"}, {"id": "n4", "name": "Node 4", "kind": "character"}, {"id": "n5", "name": "Node 5", "kind": "character"}], "connections": [{"id": "e0", "source": "n4", "target": "n3", "label": "Referenced in event"}, {"id": "e1", "source": "n5", "target": "n0", "label": "Referenced in event"}, {"id": "e2", "source": "n2", "target": "n4", "label": "Referenced in event"}, {"id": "e3", "source": "n1", "target": "n4", "label": "Referenced in event"}, {"id": "e4", "source": "n1", "target": "n4", "label": "Referenced in event"}, {"id": "e5", "source": "n4", "target": "n5", "label": "Referenced in event"}, {"id": "e6", "source": "n2", "target": "n0", "label": "Referenced in event"}, {"id": "e8", "source": "n2", "target": "n5", "label": "Referenced in event"}, {"id": "e9", "source": "n5", "target": "n2", "label": "Referenced in event"}, {"id": "e10", "source": "n1", "target": "n4", "label": "Referenced in event"}, {"id": "e11", "source": "n5", "target": "n2", "label": "Referenced in event"}, {"id": "e12", "source": "n4", "target": "n5", "label": "Referenced in event"}, {"id": "e13", "source": "n2", "target": "n4", "label": "Referenced in event"}, {"id": "e15", "source": "n0", "target": "n2", "label": "Referenced in event"}]};
const recovered=branchingLayout(crashGraph);assert.equal(recovered.positions.size,6);assert.equal(recovered.routes.size,crashGraph.connections.length);for(const p of recovered.positions.values())assert(Number.isFinite(p.x)&&Number.isFinite(p.y));console.log("Passed: formerly crashing cyclic graph preserves every node and edge.");
