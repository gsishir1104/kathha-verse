 'use client';
import {useEffect} from 'react';
export default function WriterBackground({route}:{route:string}){
 useEffect(()=>{let disposed=false,cleanup:(()=>void)|undefined;const library=document.createElement('script'),animation=document.createElement('script');library.src='/three.min.js';animation.src='/workspace-animation.js';library.onload=()=>{if(!disposed)document.body.appendChild(animation)};animation.onload=()=>{if(!disposed)cleanup=(window as typeof window & {startKathhaWorkspace?:()=>()=>void}).startKathhaWorkspace?.()};document.body.appendChild(library);return ()=>{disposed=true;cleanup?.();library.remove();animation.remove()};},[]);
 useEffect(()=>{window.dispatchEvent(new CustomEvent('kathha-workspace-view',{detail:({dashboard:'ov',workspace:'man',readers:'bet',analytics:'ria',messages:'msg',support:'hlp'} as Record<string,string>)[route]||'ov'}))},[route]);
 return <canvas id="writer-ambient" aria-hidden="true"/>;
}
