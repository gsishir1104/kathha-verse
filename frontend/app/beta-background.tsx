 'use client';
import {useEffect} from 'react';
export default function BetaBackground({route}:{route:string}){
 useEffect(()=>{let disposed=false,cleanup:(()=>void)|undefined;const library=document.createElement('script'),animation=document.createElement('script');library.src='/three.min.js';animation.src='/beta-animation.js';const start=()=>{if(!disposed)document.body.appendChild(animation)};library.onload=start;animation.onload=()=>{if(!disposed)cleanup=(window as typeof window & {startKathhaBeta?:()=>()=>void}).startKathhaBeta?.()};if((window as typeof window & {THREE?:unknown}).THREE)start();else document.body.appendChild(library);return ()=>{disposed=true;cleanup?.();library.remove();animation.remove()};},[]);
 useEffect(()=>{window.dispatchEvent(new CustomEvent('kathha-beta-view',{detail:({library:'hm',inbox:'inv',profile:'prof',messages:'msg',discover:'dis',support:'hlp'} as Record<string,string>)[route]||'hm'}))},[route]);
 return <canvas id="beta-ambient" aria-hidden="true"/>;
}
