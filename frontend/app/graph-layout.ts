import type {UniverseGraph} from './universe-model';
import dagre from '@dagrejs/dagre';

/** Bounded connected overview; all entities remain accessible in the selector. */
export function overviewGraph(graph:UniverseGraph,focus='',page=0,showReferences=false):UniverseGraph{
 const connections=graph.connections.filter(c=>showReferences||!c.generic);
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
 graph.connections.forEach(c=>g.setEdge(c.source,c.target,{width:Math.max(70,c.label.length*8+24),height:34,labelpos:'c'},c.id));
 dagre.layout(g);
 const positions=new Map<string,{x:number;y:number}>();
 graph.items.forEach(n=>{const p=g.node(n.id);positions.set(n.id,{x:p.x-110,y:p.y-41})});
 const routes=new Map<string,{points:{x:number;y:number}[];x:number;y:number}>();
 graph.connections.forEach(c=>{const e=g.edge({v:c.source,w:c.target,name:c.id});routes.set(c.id,{points:e.points,x:e.x!,y:e.y!})});
 return {positions,routes,width:g.graph().width||800,height:Math.max(500,g.graph().height||500)};
}
