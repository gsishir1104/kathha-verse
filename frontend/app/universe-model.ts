import type {Entity, Universe} from './types';

export type GraphItem={id:string;name:string;kind:string;entityId?:string;summary:string;evidence:string;order?:number;storyTime?:string;certainty?:string;synthetic?:boolean};
export type GraphConnection={id:string;source:string;target:string;label:string;evidence:string;generic:boolean};
export type UniverseGraph={items:GraphItem[];connections:GraphConnection[]};

/** Only use references present in the supplied (server-projected for readers) snapshot. */
export function buildUniverseGraph(universe:Universe):UniverseGraph{
 const entities=universe.entities.filter(e=>e.status!=='rejected');
 const ids=new Set(entities.map(e=>e.id));
 const items:GraphItem[]=entities.map(e=>({id:e.id,entityId:e.id,name:e.name,kind:e.kind,summary:e.summary,evidence:e.evidence,order:e.timeline_order??undefined,storyTime:e.story_time,certainty:e.certainty}));
 const connections:GraphConnection[]=[];
 const add=(source:string,target:string,label:string,evidence:string,generic=false)=>{
  if(source===target||!ids.has(source)||!ids.has(target))return;
  if(connections.some(c=>c.source===source&&c.target===target&&c.label===label))return;
  connections.push({id:'connection-'+connections.length,source,target,label,evidence,generic});
 };
 for(const entity of entities)for(const relation of entity.relations||[])add(entity.id,relation.target_id,relation.label,relation.evidence);
 for(const entity of entities)for(const target of entity.links||[]){
  if(!connections.some(c=>(c.source===entity.id&&c.target===target)||(c.target===entity.id&&c.source===target)))add(entity.id,target,'Connected · role unspecified',entity.evidence,true);
 }
 // Facts support existing events. Prose statements are never extra graph nodes.
 for(const [index,fact] of (universe.facts||[]).entries()){
  if(!fact.entity_ids.length||!fact.entity_ids.every(id=>ids.has(id)))continue;
  const existingEvent=fact.category==='event'?entities.find(e=>e.kind==='event'&&fact.entity_ids.includes(e.id)):undefined;
  let id=existingEvent?.id;
  if(!id){
   if(fact.category!=='event')continue;
   id='fact:'+index;while(ids.has(id))id='fact:'+id;ids.add(id);
   items.push({id,name:fact.text,kind:'event',summary:fact.text,evidence:fact.evidence,synthetic:true});
  }
  for(const target of fact.entity_ids){
   if(target!==id&&!connections.some(c=>(c.source===id&&c.target===target)||(c.source===target&&c.target===id)))add(id,target,'Referenced in event'+(fact.category==='event'?'':' / fact'),fact.evidence,true);
  }
 }
 return {items,connections};
}

export function focusGraph(graph:UniverseGraph,focus:string){
 if(!focus)return graph;
 const ids=new Set([focus]);
 graph.connections.forEach(c=>{if(c.source===focus)ids.add(c.target);if(c.target===focus)ids.add(c.source)});
 // Include participants/places of directly linked event or statement hubs.
 const hubs=new Set(graph.items.filter(n=>ids.has(n.id)&&(n.kind==='event'||n.kind==='statement')).map(n=>n.id));
 graph.connections.forEach(c=>{if(hubs.has(c.source))ids.add(c.target);if(hubs.has(c.target))ids.add(c.source)});
 return {items:graph.items.filter(n=>ids.has(n.id)),connections:graph.connections.filter(c=>ids.has(c.source)&&ids.has(c.target))};
}

export function eventContext(graph:UniverseGraph,id:string){
 const connections=graph.connections.filter(c=>c.source===id||c.target===id);
 const linked=connections.map(c=>({item:graph.items.find(n=>n.id===(c.source===id?c.target:c.source))!,connection:c})).filter(x=>x.item);
 return {people:linked.filter(x=>x.item.kind==='character'),places:linked.filter(x=>x.item.kind==='location')};
}

export function orderedEvents(graph:UniverseGraph){
 const events=graph.items.filter(n=>n.kind==='event');
 const known=events.filter(e=>Number.isFinite(e.order)).sort((a,b)=>a.order!-b.order!);
 const unknown=events.filter(e=>!Number.isFinite(e.order));
 return {known,unknown};
}

export function entityForItem(universe:Universe,item:GraphItem):Entity|undefined{return universe.entities.find(e=>e.id===item.entityId)}
