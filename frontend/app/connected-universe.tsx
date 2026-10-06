'use client';
import {useEffect,useMemo,useState} from 'react';
import {Background,Controls,Handle,Position,ReactFlow,MarkerType, type NodeProps,type Node} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {buildUniverseGraph,focusGraph,eventContext,orderedEvents,type GraphItem,type UniverseGraph} from './universe-model';
import type {Universe} from './types';
import './connected-universe.css';

type ItemNode=Node<{item:GraphItem;active:boolean},'story'>;
function StoryNode({data}:NodeProps<ItemNode>){return <div className={'connected-node kind-'+data.item.kind+(data.active?' is-active':'')}><Handle type="target" position={Position.Left}/><span>{data.item.kind.replaceAll('_',' ')}</span><strong>{data.item.name}</strong>{data.item.certainty&&data.item.certainty!=='explicit'&&<small>{data.item.certainty} interpretation</small>}<Handle type="source" position={Position.Right}/></div>}
const nodeTypes={story:StoryNode};
const views=[['story','Story graph'],['character','Character graph'],['event','Event graph'],['location','Location graph'],['timeline','Timeline']] as const;

function Context({graph,item,onPick}:{graph:UniverseGraph;item:GraphItem;onPick:(item:GraphItem)=>void}){
 const {people,places}=eventContext(graph,item.id);
 return <><div className="connected-context"><strong>Characters</strong>{people.length?people.map(({item:p,connection:c})=><button type="button" className="button small" key={c.id} onClick={()=>onPick(p)}>{p.name}<small>{c.generic?'Referenced · role unspecified':c.label}</small></button>):<span>No participants recorded.</span>}</div><div className="connected-context"><strong>Locations</strong>{places.length?places.map(({item:p,connection:c})=><button type="button" className="button small" key={c.id} onClick={()=>onPick(p)}>{p.name}<small>{c.generic?'Referenced · visit unspecified':c.label}</small></button>):<span>No location recorded.</span>}</div></>
}

export default function ConnectedUniverse({universe,onSelect,onChange}:{universe:Universe;onSelect:(id:string)=>void;onChange?:(u:Universe)=>void}){
 const [view,setView]=useState<string>('story'),[focus,setFocus]=useState(''),[picked,setPicked]=useState('');
 const graph=useMemo(()=>buildUniverseGraph(universe),[universe]);
 const options=graph.items.filter(n=>n.kind===view);
 const activeFocus=options.some(n=>n.id===focus)?focus:options[0]?.id||'';
 const shown=useMemo(()=>view==='story'?graph:focusGraph(graph,activeFocus),[graph,view,activeFocus]);
 const selected=graph.items.find(n=>n.id===(picked||(['character','event','location'].includes(view)?activeFocus:'')));
 function pick(item:GraphItem){setPicked(item.id);if(item.entityId)onSelect(item.entityId)}
 const positions=useMemo(()=>{
  const map=new Map<string,{x:number;y:number}>();
  // Deterministic kind lanes keep cards apart; React Flow supplies pan, zoom and dragging.
  const groups=[shown.items.filter(n=>n.kind==='character'),shown.items.filter(n=>!['character','location'].includes(n.kind)),shown.items.filter(n=>n.kind==='location')].filter(group=>group.length);
  groups.forEach((group,col)=>group.forEach((n,row)=>map.set(n.id,{x:col*350,y:row*145+(col%2)*35})));
  return map;
 },[shown]);
 const nodes:ItemNode[]=shown.items.map(n=>({id:n.id,type:'story',position:positions.get(n.id)||{x:0,y:0},data:{item:n,active:n.id===picked||n.id===activeFocus&&view!=='story'}}));
 const edges=shown.connections.map(c=>({id:c.id,source:c.source,target:c.target,label:c.label,type:'smoothstep',markerEnd:c.generic?undefined:{type:MarkerType.ArrowClosed},style:{stroke:'var(--muted)',strokeDasharray:c.generic?'5 4':undefined},labelStyle:{fill:'var(--ink)',fontSize:12},labelBgStyle:{fill:'var(--paper)'},labelBgPadding:[6,4] as [number,number],labelBgBorderRadius:4}));
 const chronology=orderedEvents(graph);
 function eventCard(item:GraphItem){return <article className="connected-event" key={item.id}><button type="button" className="text-button" onClick={()=>pick(item)}><strong>{item.name}</strong></button><small>{item.order!=null?'Story order '+item.order:'Chronological position not recorded'}{item.storyTime?' · '+item.storyTime:''}</small><p>{item.summary!==item.name?item.summary:''}</p><Context graph={graph} item={item} onPick={pick}/>{onChange&&item.entityId&&<label>Chronological position<input aria-label={'Chronological position for '+item.name} type="number" min={1} value={item.order??''} onChange={e=>{const value=e.target.value;onChange({...universe,entities:universe.entities.map(n=>n.id===item.entityId?{...n,timeline_order:value?Math.max(1,Math.floor(Number(value))):null}:n)})}}/></label>}</article>}
 useEffect(()=>{if(picked&&!graph.items.some(n=>n.id===picked))setPicked('')},[graph,picked]);
 return <section className="connected-universe"><nav className="connected-tabs" aria-label="Universe graph views">{views.map(([id,label])=><button type="button" key={id} className={'button small '+(view===id?'primary':'')} aria-pressed={view===id} onClick={()=>{setView(id);setFocus('');setPicked('')}}>{label}</button>)}</nav>
 {view!=='story'&&view!=='timeline'&&<label className="connected-picker">Choose {view}<select aria-label={'Choose '+view} value={activeFocus} onChange={e=>{setFocus(e.target.value);setPicked('')}}>{!options.length&&<option value="">No {view}s recorded</option>}{options.map(n=><option key={n.id} value={n.id}>{n.name}</option>)}</select></label>}
 <p className="connected-note">Connections come from this chapter’s story data. Dashed links indicate a reference without a recorded role; they do not establish participation, a visit, or guilt.</p>
 {view==='timeline'?<div className="connected-timeline"><h3>Events in story chronology</h3>{chronology.known.map(eventCard)}{!!chronology.unknown.length&&<><h4>Order not yet established</h4><p>These events are not assigned an invented chronological position. The writer can record their order before verification.</p>{chronology.unknown.map(eventCard)}</>}{!chronology.known.length&&!chronology.unknown.length&&<p>No events recorded in this chapter.</p>}</div>:((view!=='story'&&!options.length)||!shown.items.length)?<div className="empty inset"><h3>No {view==='story'?'story elements':view+'s'} recorded</h3><p>Analyze the chapter or review its extracted entities.</p></div>:<><div className="connected-canvas"><ReactFlow key={view+activeFocus+shown.items.map(n=>n.id).join('|')} nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{padding:0.25,minZoom:0.25,maxZoom:1}} minZoom={0.15} maxZoom={1.8} nodesConnectable={false} nodesDraggable={false} onNodeClick={(_,node)=>pick(node.data.item as GraphItem)} onEdgeClick={(_,edge)=>{const c=shown.connections.find(x=>x.id===edge.id);if(c)setPicked(c.source)}}><Background color="var(--line)" gap={24}/><Controls showInteractive={false}/></ReactFlow></div><details className="connected-accessible"><summary>Browse all {shown.items.length} visible nodes and their connections</summary>{shown.items.map(n=><div key={n.id}><button type="button" className="text-button" onClick={()=>pick(n)}>{n.name} · {n.kind}</button><ul>{shown.connections.filter(c=>c.source===n.id).map(c=><li key={c.id}>{c.label} → {shown.items.find(x=>x.id===c.target)?.name}</li>)}</ul></div>)}</details></>}
 {selected&&<section className="connected-selection" aria-live="polite"><div className="row between"><h3>{selected.name}</h3><button type="button" className="text-button" onClick={()=>setPicked('')}>Close</button></div><p>{selected.summary}</p>{selected.evidence&&<details><summary>Chapter evidence</summary><blockquote>{selected.evidence}</blockquote></details>}{selected.kind==='event'&&<Context graph={graph} item={selected} onPick={pick}/>}{['character','event','location'].includes(selected.kind)&&<button type="button" className="button small" onClick={()=>{setView(selected.kind);setFocus(selected.id)}}>Explore this {selected.kind}</button>}{selected.kind==='location'&&<><h4>Connected events at this location</h4>{[...chronology.known,...chronology.unknown].filter(e=>eventContext(graph,e.id).places.some(p=>p.item.id===selected.id)).map(eventCard)}<p>Only recorded event links appear here; a reference alone does not prove a visit.</p></>}</section>}
 </section>
}
