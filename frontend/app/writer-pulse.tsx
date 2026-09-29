'use client';
import {useState,useEffect} from 'react';
import {api} from './types';
import type {Act} from './writer';
export default function WriterPulse({act}:{act:Act}){
 const [data,setData]=useState<{awaiting_verification:number;accepted_readers:number;completed_reads:number;feedback:{id:string;chapter:string;reader:string;category:string;text:string;created:number}[]}|null>(null);
 useEffect(()=>{void act(async()=>setData(await api('/writer/pulse')))},[]);
 if(!data)return null;
 return <section className="feature-panel"><p className="eyebrow">YOUR NEXT STEPS & REAL READER ACTIVITY</p><div className="admin-stats">{[['Awaiting verification',data.awaiting_verification],['Accepted beta readers',data.accepted_readers],['Completed chapter reads',data.completed_reads]].map(([label,value])=><div className="admin-card" key={label}><strong>{value}</strong><span>{label}</span></div>)}</div><h2>Recent beta feedback</h2>{data.feedback.map(f=><article className="response-card" key={f.id}><strong>{f.reader} · {f.chapter}</strong><span className="badge">{f.category}</span><p>{f.text}</p><small>{new Date(f.created*1000).toLocaleString()}</small></article>)}{!data.feedback.length&&<p>Feedback appears here after your beta readers respond.</p>}</section>
}
