'use client';
import {useEffect,useMemo,useState} from 'react';
import {Background,Controls,Handle,Position,ReactFlow,MarkerType,BaseEdge,EdgeLabelRenderer,type EdgeProps, type NodeProps,type Node} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {buildUniverseGraph,focusGraph,eventContext,orderedEvents,type GraphItem,type UniverseGraph} from './universe-model';
import type {Universe} from './types';
import './connected-universe.css';
import {overviewGraph,branchingLayout} from './graph-layout';

type ItemNode=Node<{item:GraphItem;active:boolean},'story'>;
function StoryNode({data}:NodeProps<ItemNode>){const title=data.item.name.length>64?data.item.name.slice(0,61)+'…':data.item.name;return <div title={data.item.name} className={'connected-node kind-'+data.item.kind+(data.active?' is-active':'')}><Handle type="target" position={Position.Top}/><strong>{title}</strong><Handle type="source" position={Position.Bottom}/></div>}
const nodeTypes={story:StoryNode};
function StoryEdge({id,data,label,markerEnd,style}:EdgeProps){
 const route=data?.route as {points:{x:number;y:number}[];x:number;y:number}|undefined;
 if(!route?.points.length)return null;
 const points=route.points;let path=`M ${points[0].x} ${points[0].y}`;
 for(let i=1;i<points.length;i++){
  const p=points[i],next=points[i+1];
  if(next)path+=` Q ${p.x} ${p.y} ${(p.x+next.x)/2} ${(p.y+next.y)/2}`;
  else path+=` L ${p.x} ${p.y}`;
 }
 return <><BaseEdge id={id} path={path} markerEnd={markerEnd} style={style}/><EdgeLabelRenderer><span className="branch-edge-label" style={{transform:`translate(-50%, -50%) translate(${route.x}px,${route.y}px)`}}>{label}</span></EdgeLabelRenderer></>;
}
const edgeTypes={branch:StoryEdge};
const views=[['story','Story graph'],['character','Character graph'],['event','Event graph'],['location','Location graph'],['timeline','Timeline']] as const;

function Context({graph,item,onPick}:{graph:UniverseGraph;item:GraphItem;onPick:(item:GraphItem)=>void}){
 const {people,places}=eventContext(graph,item.id);
 return <><div className="connected-context"><strong>Characters</strong>{people.length?people.map(({item:p,connection:c})=><button type="button" className="button small" key={c.id} onClick={()=>onPick(p)}>{p.name}<small>{c.generic?'Referenced · role unspecified':c.label}</small></button>):<span>No participants recorded.</span>}</div><div className="connected-context"><strong>Locations</strong>{places.length?places.map(({item:p,connection:c})=><button type="button" className="button small" key={c.id} onClick={()=>onPick(p)}>{p.name}<small>{c.generic?'Referenced · visit unspecified':c.label}</small></button>):<span>No location recorded.</span>}</div></>
}

export default function ConnectedUniverse({universe,onSelect,onChange}:{universe:Universe;onSelect:(id:string)=>void;onChange?:(u:Universe)=>void}){
 const [view,setView]=useState<string>('story'),[focus,setFocus]=useState(''),[picked,setPicked]=useState('');
 const [page,setPage]=useState(0),[references,setReferences]=useState(false);
 const graph=useMemo(()=>buildUniverseGraph(universe),[universe]);
 const currentGraph=useMemo(()=>buildUniverseGraph(universe,true),[universe]);
 const viewGraph=view==='event'||view==='location'?graph:currentGraph;
 const options=viewGraph.items.filter(n=>view==='story'||n.kind===view);
 const activeFocus=options.some(n=>n.id===focus)?focus:view==='story'?'':options[0]?.id||'';
 const scoped=useMemo(()=>{
 const base=activeFocus?focusGraph(viewGraph,activeFocus):viewGraph;
 const connectedIds=new Set(base.connections.flatMap(c=>[c.source,c.target]));
 const items=base.items.filter(n=>(!n.synthetic||n.id===activeFocus)&&(connectedIds.has(n.id)||n.id===activeFocus));
 const ids=new Set(items.map(n=>n.id));
 return {items,connections:base.connections.filter(c=>ids.has(c.source)&&ids.has(c.target))};
 },[viewGraph,activeFocus]);
 const pageCount=Math.max(1,Math.ceil((scoped.items.length-1)/9));
 const currentPage=Math.min(page,pageCount-1);
 const shown=useMemo(()=>overviewGraph(scoped,activeFocus,currentPage,references||view==='event'||view==='location'),[scoped,activeFocus,currentPage,references,view]);
 const selected=graph.items.find(n=>n.id===(picked||(['character','event','location'].includes(view)?activeFocus:'')));
 function pick(item:GraphItem){setPicked(item.id);if(item.entityId)onSelect(item.entityId)}
 const layout=useMemo(()=>branchingLayout(shown),[shown]);
 const positions=layout.positions;
 const nodes:ItemNode[]=shown.items.map(n=>({id:n.id,type:'story',position:positions.get(n.id)||{x:0,y:0},data:{item:n,active:n.id===picked||n.id===activeFocus&&view!=='story'}}));
 const edges=shown.connections.map((c,index)=>({id:c.id,source:c.source,target:c.target,label:c.label,type:'branch',data:{route:layout.routes.get(c.id)},markerEnd:c.generic?undefined:{type:MarkerType.ArrowClosed},style:{stroke:'var(--muted)',strokeDasharray:c.generic?'5 4':undefined},labelStyle:{fill:'var(--ink)',fontSize:15,fontWeight:500},labelBgStyle:{fill:'var(--paper)',stroke:'var(--line)'},labelBgPadding:[10,7] as [number,number],labelBgBorderRadius:16}));
 const chronology=orderedEvents(graph);
 function eventCard(item:GraphItem){return <article className="connected-event" key={item.id}><button type="button" className="text-button" onClick={()=>pick(item)}><strong>{item.name}</strong></button><small>{item.order!=null?'Story order '+item.order:'Chronological position not recorded'}{item.storyTime?' · '+item.storyTime:''}</small><p>{item.summary!==item.name?item.summary:''}</p><Context graph={graph} item={item} onPick={pick}/>{onChange&&item.entityId&&<label>Chronological position<input aria-label={'Chronological position for '+item.name} type="number" min={1} value={item.order??''} onChange={e=>{const value=e.target.value;onChange({...universe,entities:universe.entities.map(n=>n.id===item.entityId?{...n,timeline_order:value?Math.max(1,Math.floor(Number(value))):null}:n)})}}/></label>}</article>}
 useEffect(()=>{if(picked&&!graph.items.some(n=>n.id===picked))setPicked('')},[graph,picked]);
 return <section className="connected-universe"><nav className="connected-tabs" aria-label="Universe graph views">{views.map(([id,label])=><button type="button" key={id} className={'button small '+(view===id?'primary':'')} aria-pressed={view===id} onClick={()=>{setView(id);setFocus('');setPicked('');setPage(0)}}>{label}</button>)}</nav>
 {view!=='timeline'&&<><label className="connected-picker">{view==='story'?'Explore':'Choose '+view}<select aria-label={'Choose '+view} value={activeFocus} onChange={e=>{setFocus(e.target.value);setPicked('');setPage(0)}}>{view==='story'&&<option value="">Story overview</option>}{!options.length&&<option value="">No {view}s recorded</option>}{options.map(n=><option key={n.id} value={n.id}>{n.name}</option>)}</select></label><div className="connected-navigation"><span>{shown.items.length} nodes shown · {options.length} available</span>{pageCount>1&&<><button type="button" className="button small" disabled={currentPage===0} onClick={()=>setPage(currentPage-1)}>Previous connections</button><span>{currentPage+1} / {pageCount}</span><button type="button" className="button small" disabled={currentPage===pageCount-1} onClick={()=>setPage(currentPage+1)}>Next connections</button></>}<label><input type="checkbox" checked={references} onChange={e=>{setReferences(e.target.checked);setPage(0)}}/>Show unspecified links</label></div></>}
 {!universe.entities.some(e=>e.relations?.some(r=>r.scope==='current'))&&<p className="connected-note">This saved analysis predates chapter-end graphs. Only recorded family connections are shown. Re-analyze this chapter to generate its end-of-chapter relationships; your existing analysis has not been rewritten.</p>}
 <p className="connected-note">{view==='event'||view==='location'?'Explore recorded events, their characters and locations. Dashed connections are references, not proof of participation or a visit.':'Story and character graphs show chapter-end relationships. Event and location views keep the historical context.'}</p>
 {view==='timeline'?<div className="connected-timeline"><h3>Events in story chronology</h3>{chronology.known.map(eventCard)}{!!chronology.unknown.length&&<><h4>Order not yet established</h4><p>These events are not assigned an invented chronological position. The writer can record their order before verification.</p>{chronology.unknown.map(eventCard)}</>}{!chronology.known.length&&!chronology.unknown.length&&<p>No events recorded in this chapter.</p>}</div>:((view!=='story'&&!options.length)||!shown.items.length)?<div className="empty inset"><h3>No chapter-end connections recorded</h3><p>Re-analyze this chapter, or use Correct on an entity and classify its supported connections as Chapter-end graph. All characters remain available in the selector.</p></div>:<><div className="connected-canvas" style={{height:Math.min(1050,Math.max(560,layout.height*0.7+50))}}><div className="connected-flow" style={{width:Math.max(320,layout.width*0.7+50),height:Math.max(560,layout.height*0.7+50)}}><ReactFlow key={view+activeFocus+String(references)+shown.items.map(n=>n.id).join('|')} nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView fitViewOptions={{padding:0.15,minZoom:0.7,maxZoom:1}} minZoom={0.4} maxZoom={1.8} nodesConnectable={false} nodesDraggable={false} onNodeClick={(_,node)=>pick(node.data.item as GraphItem)} onEdgeClick={(_,edge)=>{const c=shown.connections.find(x=>x.id===edge.id);if(c)setPicked(c.source)}}><Background color="var(--line)" gap={24}/><Controls showInteractive={false}/></ReactFlow></div></div><details className="connected-accessible"><summary>Browse all {shown.items.length} visible nodes and their connections</summary>{shown.items.map(n=><div key={n.id}><button type="button" className="text-button" onClick={()=>pick(n)}>{n.name} · {n.kind}</button><ul>{shown.connections.filter(c=>c.source===n.id).map(c=><li key={c.id}>{c.label} → {shown.items.find(x=>x.id===c.target)?.name}</li>)}</ul></div>)}</details></>}
 {selected&&<section className="connected-selection" aria-live="polite"><div className="row between"><h3>{selected.name}</h3><button type="button" className="text-button" onClick={()=>setPicked('')}>Close</button></div><p>{selected.summary}</p>{selected.evidence&&<details><summary>Chapter evidence</summary><blockquote>{selected.evidence}</blockquote></details>}{selected.kind==='event'&&<Context graph={graph} item={selected} onPick={pick}/>}{['character','event','location'].includes(selected.kind)&&<button type="button" className="button small" onClick={()=>{setView(selected.kind);setFocus(selected.id);setPage(0)}}>Explore this {selected.kind}</button>}{selected.kind==='location'&&<><h4>Connected events at this location</h4>{[...chronology.known,...chronology.unknown].filter(e=>eventContext(graph,e.id).places.some(p=>p.item.id===selected.id)).map(eventCard)}<p>Only recorded event links appear here; a reference alone does not prove a visit.</p></>}</section>}
 </section>
}

import './branching-graph.css';
