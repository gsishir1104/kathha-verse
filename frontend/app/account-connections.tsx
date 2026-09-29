'use client';
import {useState} from 'react';
import type {Account,Pair,Story} from './admin-account';

export default function AccountConnections({account,stories,pairs}:{account:Account;stories:Story[];pairs:Pair[]}){
 const writer=account.role==='writer'&&!account.is_admin;
 const groups=writer?stories.map(s=>({id:s.id,title:s.title,writer:account.name,chapters:s.chapters.length,verified:s.chapters.filter(c=>['verified','released'].includes(c.state)).length,pairs:pairs.filter(p=>p.story_id===s.id)})):Array.from(new Set(pairs.map(p=>p.story_id))).map(id=>{const rows=pairs.filter(p=>p.story_id===id);return {id,title:rows[0].story,writer:rows[0].writer,chapters:null,verified:null,pairs:rows}});
 const [selected,setSelected]=useState('');
 const story=groups.find(s=>s.id===selected)||groups[0];
 return <section className="admin-card connection-explorer" aria-label="Account connection graph"><div className="connection-heading"><div><p className="eyebrow">WHO IS CONNECTED TO WHOM</p><h2>Story connections</h2><p className="muted">{writer?'Your selected writer’s stories and beta readers.':'Writers and stories connected to this account.'}</p></div>{groups.length>1&&<label>Story<select value={story?.id||''} onChange={e=>setSelected(e.target.value)}>{groups.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select></label>}</div>
 {!story?<p className="connection-empty">{writer?'No stories created yet. Connections will appear here when this writer creates a story.':'No story invitations for this account yet.'}</p>:<>
 <div className="connection-root"><span className="connection-symbol" aria-hidden="true">✎</span><strong>Writer: {story.writer}</strong><span>{story.title}</span></div>
 <div className="connection-stem" aria-hidden="true"/>
 <div className="connection-stage"><strong>{story.pairs.some(p=>p.released>0)?'Beta testing':story.pairs.length?'Reader invitations':'Preparing the story'}</strong><span>{story.chapters!==null?`${story.verified} of ${story.chapters} chapters verified or released`:`${story.pairs.reduce((n,p)=>n+p.released,0)} chapters accessible to this account`}</span></div>
 {story.pairs.length>0?<><div className="connection-stem" aria-hidden="true"/><ul className="connection-branches">{story.pairs.map(p=>{
 const active=p.chapters.filter(c=>c.active),progress=active.length?Math.round(active.reduce((n,c)=>n+c.progress,0)/active.length):0;
 const status=p.status!=='accepted'?p.status==='pending'?'Pending invitation':p.status:p.released===0?'Awaiting chapters':p.completed===p.released?'Released chapters read':'Reading in progress';
 return <li key={p.id}><details className="connection-person"><summary><span className="connection-avatar" aria-hidden="true">{(p.reader==='Not registered'?p.reader_email:p.reader).slice(0,1).toUpperCase()}</span><strong>{p.reader==='Not registered'?p.reader_email:p.reader}</strong><span className={'badge '+(p.status==='pending'?'amber':p.status==='accepted'&&p.released?'green':'')}>{status}</span><span>{p.released?`${p.completed} / ${p.released} accessible chapters read`:'No chapters accessible'}</span>{p.released>0&&<progress max={100} value={progress} aria-label={`${p.reader}: average reading progress ${progress}%`}/>}<small>View chapter progress ↓</small></summary><div className="connection-detail"><p className="muted">{p.reader_email}</p>{p.chapters.length?p.chapters.map(c=><div key={c.position}><strong>Chapter {c.position}: {c.title}</strong><p>{c.progress}% read · {c.active?'Accessible':'Access inactive'}</p><small>{c.answers} answers · {c.feedback} inline comments</small></div>):<p>No chapter releases yet.</p>}</div></details></li>
 })}</ul></>:<p className="connection-empty">No beta readers invited to this story yet.</p>}
 <p className="connection-footnote">Reading progress is saved by each reader. “Released chapters read” does not mean the entire story is finished. Open a reader card for chapter details.</p>
 </>}
 </section>
}
