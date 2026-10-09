import type {UniverseGraph} from './universe-model';
import dagre from '@dagrejs/dagre';

/** Bounded connected overview; all entities remain accessible in the selector. */
export function overviewGraph(graph:UniverseGraph,focus='',page=0,showReferences=false):UniverseGraph{
 const groups=new Map<string,typeof graph.connections[number]>();
 for(const c of graph.connections.filter(c=>showReferences||!c.generic)){
  const key=c.source+'\0'+c.target,previous=groups.get(key);
  if(!previous)groups.set(key,{...c});
  else if(!previous.label.split(' · ').includes(c.label))previous.label+=' · '+c.label;
 }
 const connections=[...groups.values()];
 const degree=(id:string)=>connections.filter(c=>c.source===id||c.target===id).length;
 const ranked=[...graph.items].sort((a,b)=>degree(b.id)-degree(a.id)||a.name.localeCompare(b.name));
 const root=graph.items.find(n=>n.id===focus)||ranked.find(n=>n.kind==='character')||ranked[0];
 if(!root)return {items:[],connections:[]};
 const queue=[root.id],seen=new Set<string>();
 while(queue.length){const id=queue.shift()!;if(seen.has(id))continue;seen.add(id);const neighbors=connections.filter(c=>c.source===id||c.target===id).map(c=>c.source===id?c.target:c.source).sort((a,b)=>degree(b)-degree(a));queue.push(...neighbors.filter(n=>!seen.has(n)))}
 const ordered=[...seen].filter(id=>id!==root.id);
 // Disconnected entities stay discoverable, without invented connecting lines.
 ordered.push(...ranked.filter(n=>!seen.has(n.id)).map(n=>n.id));
 const ids=new Set([root.id,...ordered.slice(page*9,page*9+9)]);
 return {items:graph.items.filter(n=>ids.has(n.id)),connections:connections.filter(c=>ids.has(c.source)&&ids.has(c.target)).slice(0,16)};
}

/** Keep the graph usable even when the automatic router cannot place a cycle. */
function fallbackLayout(graph:UniverseGraph){
 const positions=new Map(graph.items.map((n,i)=>[n.id,{x:40+(i%2)*420,y:40+Math.floor(i/2)*220}]));
 const routes=new Map<string,{points:{x:number;y:number}[];x:number;y:number}>();
 graph.connections.forEach((c,i)=>{
  const a=positions.get(c.source),b=positions.get(c.target);if(!a||!b)return;
  const start={x:a.x+110,y:a.y+82},end={x:b.x+110,y:b.y};
  const lane=Math.max(a.x,b.x)+260+(i%4)*32;
  const y=(start.y+end.y)/2;
  routes.set(c.id,{points:[start,{x:lane,y:start.y+35},{x:lane,y:end.y-35},end],x:lane,y});
 });
 return {positions,routes,width:Math.min(2,graph.items.length)*420+180,height:Math.max(300,Math.ceil(graph.items.length/2)*220+80)};
}

/** Directed ranks with cycle breaking; no fixed per-kind columns. */
export function branchingLayout(graph:UniverseGraph){
 if(!graph.connections.length){
 const positions=new Map(graph.items.map((n,i)=>[n.id,{x:28+(i%2)*260,y:28+Math.floor(i/2)*120}]));
 return {positions,routes:new Map<string,{points:{x:number;y:number}[];x:number;y:number}>(),width:Math.min(2,graph.items.length)*260+56,height:Math.max(300,Math.ceil(graph.items.length/2)*120+56)};
 }
 const g=new dagre.graphlib.Graph({multigraph:true});
 g.setGraph({rankdir:'TB',nodesep:65,ranksep:90,edgesep:30,marginx:28,marginy:28});
 g.setDefaultEdgeLabel(()=>({}));
 graph.items.forEach(n=>g.setNode(n.id,{width:220,height:82}));
 graph.connections.forEach(c=>g.setEdge(c.source,c.target,{width:Math.min(190,Math.max(70,c.label.length*8+24)),height:Math.max(34,Math.ceil(c.label.length/22)*22+12),labelpos:'c'},c.id));
 try { dagre.layout(g); } catch { return fallbackLayout(graph); }
 if(graph.items.some(n=>{const p=g.node(n.id);return !p||!Number.isFinite(p.x)||!Number.isFinite(p.y)}))return fallbackLayout(graph);
 const positions=new Map<string,{x:number;y:number}>();
 graph.items.forEach(n=>{const p=g.node(n.id);positions.set(n.id,{x:p.x-110,y:p.y-41})});
 const routes=new Map<string,{points:{x:number;y:number}[];x:number;y:number}>();
 graph.connections.forEach(c=>{const e=g.edge({v:c.source,w:c.target,name:c.id});if(!e?.points?.length)return;routes.set(c.id,{points:e.points,x:e.x!,y:e.y!})});
 return {positions,routes,width:g.graph().width||800,height:Math.max(500,g.graph().height||500)};
}
