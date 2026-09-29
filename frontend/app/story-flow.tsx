'use client';
import {useEffect,useMemo,useState} from 'react';
import {ReactFlow,Background,Controls,MarkerType} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type {Entity} from './types';

const typeColors:Record<string,string>={character:'#8e7bd6',relationship:'#aa78b5',event:'#d6a552',location:'#63aaa1',object:'#8098bd',secret:'#c77a83',clue:'#d5a24a',reveal:'#d98264',plot_thread:'#7f91b0',mystery:'#a77ac0'};
const kindOrder=Object.keys(typeColors);
type Link={source:string;target:string;label:string;labeled:boolean};

export default function StoryFlow({entities,onSelect}:{entities:Entity[];onSelect:(id:string)=>void}){
 const [mode,setMode]=useState<'focus'|'overview'>('focus');
 const links=useMemo<Link[]>(()=>{
  const ids=new Set(entities.map(e=>e.id));const seen=new Set<string>();const result:Link[]=[];
  for(const entity of entities){
   for(const relation of entity.relations||[]){
    if(!ids.has(relation.target_id)||relation.target_id===entity.id)continue;
    const key=entity.id+'|'+relation.target_id+'|'+relation.label.toLowerCase();
    if(!seen.has(key)){seen.add(key);result.push({source:entity.id,target:relation.target_id,label:relation.label,labeled:true});}
   }
   for(const target of entity.links){
    if(!ids.has(target)||target===entity.id)continue;
    const hasLabel=result.some(link=>link.source===entity.id&&link.target===target);
    const key=entity.id+'|'+target+'|related';
    if(!hasLabel&&!seen.has(key)){seen.add(key);result.push({source:entity.id,target,label:'Related',labeled:false});}
   }
  }
  return result;
 },[entities]);
 const initial=useMemo(()=>entities.reduce((best,current)=>{
  const degree=(id:string)=>links.filter(link=>link.source===id||link.target===id).length;
  return !best||degree(current.id)>degree(best.id)?current:best;
 },entities[0]),[entities,links]);
 const [focusId,setFocusId]=useState(initial?.id||'');
 useEffect(()=>{if(!entities.some(e=>e.id===focusId))setFocusId(initial?.id||'');},[entities,focusId,initial]);
 const direct=links.filter(link=>link.source===focusId||link.target===focusId);
 const neighborIds=new Set(direct.flatMap(link=>[link.source,link.target]));
 const visible=mode==='focus'?entities.filter(e=>neighborIds.has(e.id)||e.id===focusId):[...entities].sort((a,b)=>kindOrder.indexOf(a.kind)-kindOrder.indexOf(b.kind)||a.name.localeCompare(b.name));
 const positions=new Map<string,{x:number;y:number}>();
 if(mode==='focus'){
  positions.set(focusId,{x:420,y:245});
  const neighbors=visible.filter(e=>e.id!==focusId);
  neighbors.forEach((entity,index)=>{
   const angle=(index*2*Math.PI/Math.max(neighbors.length,1))-Math.PI/2;
   positions.set(entity.id,{x:420+Math.cos(angle)*340,y:245+Math.sin(angle)*220});
  });
 }else visible.forEach((entity,index)=>positions.set(entity.id,{x:(index%4)*250,y:Math.floor(index/4)*155}));
 const nodes=visible.map(entity=>({
  id:entity.id,position:positions.get(entity.id)||{x:0,y:0},
  data:{label:<button className="graph-node-button" aria-label={'Inspect '+entity.name} onClick={()=>{setFocusId(entity.id);onSelect(entity.id)}}><small>{entity.kind.replaceAll('_',' ')}</small><strong>{entity.name}</strong><span className={'badge '+(entity.status==='confirmed'?'green':'amber')}>{entity.status==='confirmed'?'Writer confirmed':'Needs review'}</span></button>},
  style:{width:220,background:'var(--paper)',color:'var(--ink)',border:`2px solid ${entity.id===focusId?'var(--blue)':typeColors[entity.kind]||'var(--line)'}`,borderRadius:12,padding:14,boxShadow:entity.id===focusId?'0 0 0 4px color-mix(in srgb,var(--blue) 18%,transparent)':'0 5px 18px #0002'}
 }));
 const shownIds=new Set(visible.map(e=>e.id));
 const shownLinks=(mode==='focus'?direct:links.filter(link=>link.labeled)).filter(link=>shownIds.has(link.source)&&shownIds.has(link.target));
 const edges=shownLinks.map((link,index)=>({id:`${link.source}-${link.target}-${index}`,source:link.source,target:link.target,label:link.label,markerEnd:{type:MarkerType.ArrowClosed},style:{stroke:link.labeled?'var(--blue)':'var(--muted)',strokeWidth:link.labeled?2:1.2,opacity:link.labeled?1:.65},labelStyle:{fill:'var(--ink)',fontSize:11},labelBgStyle:{fill:'var(--paper)',fillOpacity:.92},labelBgPadding:[5,3] as [number,number],labelBgBorderRadius:4}));
 function focus(id:string){setFocusId(id);setMode('focus');onSelect(id);}
 return <div className="story-map-shell">
  <div className="story-map-toolbar">
   <div className="story-map-modes"><button className={mode==='focus'?'active':''} onClick={()=>setMode('focus')}>Focus map</button><button className={mode==='overview'?'active':''} onClick={()=>setMode('overview')}>All entities</button></div>
   <label>Focus on<select value={focusId} onChange={event=>focus(event.target.value)}>{entities.map(entity=><option value={entity.id} key={entity.id}>{entity.name} · {entity.kind.replaceAll('_',' ')}</option>)}</select></label>
   <span>{mode==='focus'?`${Math.max(visible.length-1,0)} direct connection${visible.length===2?'':'s'}`:`${entities.length} entities grouped for review`}</span>
  </div>
  <p className="story-map-help">{mode==='focus'?'Select a card to place it in the center and inspect only its direct relationships.':'The overview groups every extracted entity. Only specifically labeled relationships are drawn to prevent crossing-line clutter.'}</p>
  <div className="story-flow"><ReactFlow key={`${mode}-${focusId}-${visible.map(e=>e.id).join(',')}`} nodes={nodes} edges={edges} fitView fitViewOptions={{padding:.22,maxZoom:1.15}} nodesDraggable nodesConnectable={false} onNodeClick={(_,node)=>focus(node.id)} minZoom={.35} maxZoom={1.8} aria-label={mode==='focus'?'Focused chapter relationship map':'Chapter entity overview'}><Background gap={22} size={1}/><Controls showInteractive={false}/></ReactFlow></div>
 </div>
}
