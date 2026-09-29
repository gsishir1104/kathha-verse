"use client";
import {useEffect,useState} from 'react';
import {api,Chapter,Reading} from './types';
import type {Act} from './writer';

export function ThemeControl(){
 const [theme,setTheme]=useState('dark');
 useEffect(()=>{setTheme(localStorage.getItem('storylens-theme')||'dark')},[]);
 useEffect(()=>{const media=window.matchMedia('(prefers-color-scheme: dark)');const apply=()=>{document.documentElement.dataset.theme=theme==='system'?(media.matches?'dark':'light'):theme};apply();media.addEventListener('change',apply);return()=>media.removeEventListener('change',apply)},[theme]);
 return <label className="theme-control">Appearance<select aria-label="Color theme" value={theme} onChange={e=>{setTheme(e.target.value);localStorage.setItem('storylens-theme',e.target.value)}}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
}

type Changes={previous_chapter:number|null;added:string[];changed:string[];absent:string[]};
export function GraphChanges({path,act}:{path:string;act:Act}){
 const [changes,setChanges]=useState<Changes|null>(null);
 return <section className="feature-panel"><h3>What changed?</h3><p>Compare with the nearest earlier chapter available to you. Names and types identify matching entities; missing entities do not necessarily mean they left the story.</p><button className="button small" onClick={()=>act(async()=>setChanges(await api<Changes>(path)))}>Compare chapter graphs</button>{changes&&(changes.previous_chapter===null?<p>No earlier chapter graph is available for comparison.</p>:<><p>Compared with Chapter {changes.previous_chapter}</p>{(['added','changed','absent'] as const).map(k=><p key={k}><strong>{k==='absent'?'Not in this chapter':k==='added'?'New in this chapter':'Changed'}: </strong>{changes[k].join(', ')||'None'}</p>)}</>)}</section>
}

type Comment={id:string;entity_id:string;target_id:string;category:string;text:string};
export function GraphFeedback({reading,selected,act,busy}:{reading:Reading;selected:string;act:Act;busy:boolean}){
 const [entity,setEntity]=useState(''),[target,setTarget]=useState(''),[category,setCategory]=useState('confusion'),[text,setText]=useState(''),[comments,setComments]=useState<Comment[]>([]);
 const entities=reading.universe.entities;const current=entities.find(e=>e.id===entity);
 async function load(){setComments(await api<Comment[]>('/read/'+reading.id+'/graph-comments'))}
 useEffect(()=>{void act(load)},[reading.id,reading.snapshot_id]);
 useEffect(()=>{setEntity(selected);setTarget('')},[selected]);
 return <section className="feature-panel"><h3>Feedback on the graph</h3><p>Select a graph node or choose an item below. Your comments are private to you and the writer.</p><form className="form-stack" onSubmit={e=>{e.preventDefault();void act(async()=>{await api('/read/'+reading.id+'/graph-comments','POST',{snapshot_id:reading.snapshot_id,entity_id:entity,target_id:target,category,text});setText('');await load()},'Graph feedback saved')}}><label>Graph item<select required value={entity} onChange={e=>{setEntity(e.target.value);setTarget('')}}><option value="">Choose an entity</option>{entities.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label><label>Comment on<select value={target} onChange={e=>setTarget(e.target.value)}><option value="">This entity</option>{(current?.links||[]).map(id=><option key={id} value={id}>Connection to {entities.find(e=>e.id===id)?.name}</option>)}</select></label><label>Category<select value={category} onChange={e=>setCategory(e.target.value)}>{['confusion','positive','plot','character','pacing','worldbuilding'].map(c=><option key={c}>{c}</option>)}</select></label><label>Your feedback<textarea required maxLength={4000} rows={3} value={text} onChange={e=>setText(e.target.value)}/></label><button className="button primary" disabled={busy||!entity||!text.trim()}>Share graph feedback</button></form>{comments.map(c=><article className="response-card" key={c.id}><strong>{entities.find(e=>e.id===c.entity_id)?.name}{c.target_id?' → '+entities.find(e=>e.id===c.target_id)?.name:''}</strong><span className="badge">{c.category}</span><p>{c.text}</p></article>)}</section>
}

type History={id:string;revision:number;title:string;content:string;created:number};
export function ChapterRecovery({chapter,dirty,act,busy,onRestored}:{chapter:Chapter;dirty:boolean;act:Act;busy:boolean;onRestored:()=>Promise<void>}){
 const [history,setHistory]=useState<History[]>([]),[chosen,setChosen]=useState('');const item=history.find(h=>h.id===chosen);
 return <section className="feature-panel"><h3>Saved versions & recovery</h3><p>Earlier saved drafts are kept automatically. Restoring creates a new draft; released chapters stay unchanged.</p><button className="button small" disabled={busy} onClick={()=>act(async()=>setHistory(await api<History[]>('/chapters/'+chapter.id+'/history')))}>Load saved versions</button><label>Earlier draft<select value={chosen} onChange={e=>setChosen(e.target.value)}><option value="">Choose a version ({history.length} available)</option>{history.map(h=><option key={h.id} value={h.id}>Version {h.revision} · {new Date(h.created*1000).toLocaleString()}</option>)}</select></label>{item&&<><h4>{item.title}</h4><textarea aria-label="Saved version preview" readOnly value={item.content} rows={7}/><button className="button" disabled={busy||dirty} onClick={()=>act(async()=>{await api('/chapters/'+chapter.id+'/restore/'+item.id,'POST',{revision:chapter.revision});setChosen('');await onRestored()},'Earlier version restored as a new draft')}>Restore this saved version</button></>}{dirty&&<p>Save your current changes before restoring.</p>}</section>
}

type FeedbackItem={key:string;chapter:number;revision?:number;target:string;category:string;text:string;reader:string;status:string};
export function FeedbackBoard({storyId,act,busy}:{storyId:string;act:Act;busy:boolean}){
 const [items,setItems]=useState<FeedbackItem[]>([]),[status,setStatus]=useState('all');
 async function load(){setItems(await api<FeedbackItem[]>('/stories/'+storyId+'/feedback-board'))}
 useEffect(()=>{void act(load)},[storyId]);
 const shown=items.filter(i=>status==='all'||i.status===status);const categories=Array.from(new Set(shown.map(i=>i.category)));
 return <section className="feature-panel"><h2>Feedback to work through</h2><p>Graph and manuscript comments grouped by category. Counts show repeated categories, not an AI claim that comments mean the same thing.</p><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}>{['all','new','reviewed','addressed'].map(s=><option key={s}>{s}</option>)}</select></label><button className="text-button" onClick={()=>act(load)}>Refresh feedback</button>{!shown.length&&<p>No feedback in this view yet.</p>}{categories.map(category=><section key={category}><h3>{category} · {shown.filter(i=>i.category===category).length}</h3>{shown.filter(i=>i.category===category).map(i=><article className="response-card" key={i.key}><strong>{i.reader} · Chapter {i.chapter}{i.revision?' · version '+i.revision:''}</strong><blockquote>{i.target}</blockquote><p>{i.text}</p><label>Review status<select aria-label={'Status for '+i.reader+' feedback '+i.key} disabled={busy} value={i.status} onChange={e=>{const value=e.target.value;void act(async()=>{await api('/stories/'+storyId+'/feedback-board/'+encodeURIComponent(i.key),'PUT',{status:value});await load()})}}>{['new','reviewed','addressed'].map(s=><option key={s}>{s}</option>)}</select></label></article>)}</section>)}</section>
}
