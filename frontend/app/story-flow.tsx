'use client';
import {HeartHandshake,MapPin,Box,Zap,ChevronRight} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import type {ChapterFact,Entity} from './types';

const sections:{category:ChapterFact['category'];title:string;description:string;icon:LucideIcon}[]=[
 {category:'relationship',title:'Relationships',description:'Meaningful bonds and changes between characters',icon:HeartHandshake},
 {category:'location',title:'Locations',description:'Who entered, visited, discovered, or learned about a place',icon:MapPin},
 {category:'object',title:'Objects',description:'Who found, used, possessed, revealed, or knows about an object',icon:Box},
 {category:'event',title:'Important events',description:'Actions and discoveries that changed the chapter',icon:Zap},
];

function sentence(value:string){const text=value.replaceAll('_',' ').replace(/\s+/g,' ').trim();return text?text[0].toUpperCase()+text.slice(1).replace(/[.!?]?$/,'.'):''}

function legacyFacts(entities:Entity[]):ChapterFact[]{
 const byId=new Map(entities.map(entity=>[entity.id,entity]));const facts:ChapterFact[]=[];const pairs=new Set<string>();let order=1;
 for(const source of entities){
  for(const relation of source.relations||[]){
   const target=byId.get(relation.target_id);if(!target)continue;
   const label=relation.label.replaceAll('_',' ').trim();if(!label||['related','related to','connected','connected to'].includes(label.toLowerCase()))continue;
   let category:ChapterFact['category']|null=null;
   if(source.kind==='character'&&target.kind==='character')category='relationship';
   else if(source.kind==='location'||target.kind==='location')category='location';
   else if(source.kind==='object'||target.kind==='object')category='object';
   if(!category)continue;
   const pair=category==='relationship'?[source.id,target.id].sort().join('|'):source.id+'|'+target.id;
   if(pairs.has(pair))continue;pairs.add(pair);
   facts.push({category,text:sentence(`${source.name} ${label} ${target.name}`),evidence:relation.evidence,order:order++,entity_ids:[source.id,target.id]});
  }
 }
 for(const entity of entities.filter(item=>item.kind==='event'))facts.push({category:'event',text:sentence(entity.summary||entity.name),evidence:entity.evidence,order:entity.timeline_order??order++,entity_ids:[entity.id]});
 return facts;
}

export function chapterFacts(entities:Entity[],provided:ChapterFact[]=[]){
 const visibleIds=new Set(entities.map(entity=>entity.id));
 const supported=provided.filter(fact=>!fact.entity_ids?.length||fact.entity_ids.every(id=>visibleIds.has(id)));
 return (supported.length?supported:legacyFacts(entities)).slice().sort((a,b)=>a.order-b.order);
}

export default function StoryFlow({entities,facts=[],onSelect}:{entities:Entity[];facts?:ChapterFact[];onSelect:(id:string)=>void}){
 const items=chapterFacts(entities,facts);
 return <div className="chapter-facts-shell">
  <header className="chapter-facts-heading"><div><span className="eyebrow">AT THE END OF THIS CHAPTER</span><h3>What changed in the story?</h3><p>A concise, evidence-backed view of the chapter. Each chapter keeps its own state.</p></div><span>{items.length} important fact{items.length===1?'':'s'}</span></header>
  <div className="chapter-fact-grid">{sections.map(({category,title,description,icon:Icon})=>{const group=items.filter(fact=>fact.category===category).slice(0,8);return <section className={'chapter-fact-section fact-'+category} key={category}>
   <header><span><Icon size={18}/></span><div><h4>{title}</h4><p>{description}</p></div><b>{group.length}</b></header>
   {group.length?<ol>{group.map((fact,index)=><li key={`${fact.text}-${index}`}><button onClick={()=>fact.entity_ids?.[0]&&onSelect(fact.entity_ids[0])} disabled={!fact.entity_ids?.length}><span>{fact.text}</span>{fact.entity_ids?.length>0&&<ChevronRight size={15}/>}</button></li>)}</ol>:<p className="chapter-fact-empty">No important {title.toLowerCase()} were identified.</p>}
  </section>})}</div>
 </div>;
}
