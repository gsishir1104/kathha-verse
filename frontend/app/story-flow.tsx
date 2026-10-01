'use client';
import {useEffect,useMemo,useState} from 'react';
import {ArrowDown,ArrowRight,GitBranch,MapPin,UserRound,CalendarDays,Box,KeyRound,Lightbulb,Network} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import type {CSSProperties} from 'react';
import type {Entity} from './types';

const typeColors:Record<string,string>={character:'#8e7bd6',relationship:'#aa78b5',event:'#d6a552',location:'#63aaa1',object:'#8098bd',secret:'#c77a83',clue:'#d5a24a',reveal:'#d98264',plot_thread:'#7f91b0',mystery:'#a77ac0'};
const typeIcons:Record<string,LucideIcon>={character:UserRound,event:CalendarDays,location:MapPin,object:Box,secret:KeyRound,clue:Lightbulb,relationship:Network,reveal:Lightbulb,plot_thread:GitBranch,mystery:KeyRound};
const kindOrder=Object.keys(typeColors);
type Link={source:string;target:string;label:string;labeled:boolean};

function EntityCard({entity,active=false,onClick}:{entity:Entity;active?:boolean;onClick:()=>void}){
 const Icon=typeIcons[entity.kind]||GitBranch;
 return <button className={'simple-entity-card '+(active?'active':'')} style={{'--entity-color':typeColors[entity.kind]||'var(--blue)'} as CSSProperties} onClick={onClick} aria-label={'Focus on '+entity.name}>
  <span className="simple-entity-icon"><Icon size={18}/></span>
  <span className="simple-entity-copy"><small>{entity.kind.replaceAll('_',' ')}</small><strong>{entity.name}</strong></span>
  <span className={'simple-status '+(entity.status==='confirmed'?'confirmed':'')}>{entity.status==='confirmed'?'Confirmed':'Review'}</span>
 </button>;
}

export default function StoryFlow({entities,onSelect}:{entities:Entity[];onSelect:(id:string)=>void}){
 const [mode,setMode]=useState<'focus'|'overview'>('focus');
 const links=useMemo<Link[]>(()=>{
  const ids=new Set(entities.map(e=>e.id));const seen=new Set<string>();const result:Link[]=[];
  for(const entity of entities){
   for(const relation of entity.relations||[]){
    if(!ids.has(relation.target_id)||relation.target_id===entity.id)continue;
    const key=entity.id+'|'+relation.target_id+'|'+relation.label.trim().toLowerCase();
    if(!seen.has(key)){seen.add(key);result.push({source:entity.id,target:relation.target_id,label:relation.label.trim()||'related to',labeled:true});}
   }
   for(const target of entity.links||[]){
    if(!ids.has(target)||target===entity.id)continue;
    const pair=[entity.id,target].sort().join('|');
    const hasRelationship=result.some(link=>[link.source,link.target].sort().join('|')===pair);
    const key=pair+'|related';
    if(!hasRelationship&&!seen.has(key)){seen.add(key);result.push({source:entity.id,target,label:'related to',labeled:false});}
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
 const byId=useMemo(()=>new Map(entities.map(entity=>[entity.id,entity])),[entities]);
 const focusEntity=byId.get(focusId)||initial;
 const direct=links.filter(link=>link.source===focusId||link.target===focusId);
 const groups=kindOrder.map(kind=>({kind,entities:entities.filter(entity=>entity.kind===kind).sort((a,b)=>a.name.localeCompare(b.name))})).filter(group=>group.entities.length);
 function focus(id:string){setFocusId(id);setMode('focus');onSelect(id);}
 return <div className="story-map-shell">
  <div className="story-map-toolbar">
   <div className="story-map-modes"><button className={mode==='focus'?'active':''} onClick={()=>setMode('focus')}>Relationships</button><button className={mode==='overview'?'active':''} onClick={()=>setMode('overview')}>Story overview</button></div>
   <label>Show connections for<select value={focusId} onChange={event=>focus(event.target.value)}>{entities.map(entity=><option value={entity.id} key={entity.id}>{entity.name} · {entity.kind.replaceAll('_',' ')}</option>)}</select></label>
   <span>{mode==='focus'?`${direct.length} connection${direct.length===1?'':'s'}`:`${entities.length} story element${entities.length===1?'':'s'}`}</span>
  </div>
  <p className="story-map-help">{mode==='focus'?'Each row reads from left to right. Select any connected card to explore it.':'Story elements are grouped by type. Select a card to see only its relationships.'}</p>
  {mode==='focus'?<div className="simple-focus-map">
   {focusEntity&&<div className="simple-focus-subject"><span>Currently exploring</span><EntityCard entity={focusEntity} active onClick={()=>onSelect(focusEntity.id)}/><ArrowDown size={22}/></div>}
   {direct.length?<div className="relationship-list">{direct.map((link,index)=>{
    const source=byId.get(link.source);const target=byId.get(link.target);if(!source||!target)return null;
    const other=link.source===focusId?target:source;
    return <button className="relationship-row" key={`${link.source}-${link.target}-${index}`} onClick={()=>focus(other.id)}>
     <span className="relationship-name">{source.name}</span>
     <span className="relationship-meaning"><ArrowRight size={16}/><b>{link.label}</b><ArrowRight size={16}/></span>
     <span className="relationship-name">{target.name}</span>
     <span className="relationship-kind" style={{'--entity-color':typeColors[other.kind]||'var(--blue)'} as CSSProperties}>{other.kind.replaceAll('_',' ')}</span>
    </button>;
   })}</div>:<div className="simple-map-empty"><GitBranch size={30}/><h3>No direct relationships yet</h3><p>This story element is in the chapter, but the analysis did not identify a specific connection for it.</p></div>}
  </div>:<div className="story-overview-groups">{groups.map(group=>{
   const Icon=typeIcons[group.kind]||GitBranch;
   return <section className="story-overview-group" key={group.kind} style={{'--entity-color':typeColors[group.kind]||'var(--blue)'} as CSSProperties}>
    <header><Icon size={18}/><strong>{group.kind.replaceAll('_',' ')}</strong><span>{group.entities.length}</span></header>
    <div>{group.entities.map(entity=><EntityCard key={entity.id} entity={entity} active={entity.id===focusId} onClick={()=>focus(entity.id)}/>)}</div>
   </section>;
  })}</div>}
 </div>;
}
