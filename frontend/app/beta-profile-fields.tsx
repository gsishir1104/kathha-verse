'use client';
import {useState} from 'react';
import {Check,ChevronDown} from 'lucide-react';

export type BetaProfileData={bio:string;genres:string[];specialties:string[];availability:string;listed:boolean};

export const GENRES=['Mystery','Thriller','Romance','Fantasy','Science fiction','Horror','Contemporary','Historical fiction','Literary fiction','Young adult','Adventure','Crime','Paranormal','Non-fiction'];
export const SPECIALTIES=['Plot twists','Pacing','Characters','Dialogue','Worldbuilding','Emotional impact','Continuity','Atmosphere','Clarity','Mystery clues','Romance','Sensitivity reading'];

export function ProfileDropdown({label,options,value,onChange,required=false}:{label:string;options:string[];value:string[];onChange:(value:string[])=>void;required?:boolean}){
 const [open,setOpen]=useState(false);
 const toggle=(option:string)=>onChange(value.includes(option)?value.filter(item=>item!==option):[...value,option]);
 return <div className="profile-dropdown-field"><span>{label}{required&&<b aria-hidden="true"> *</b>}</span><details open={open} onToggle={event=>setOpen(event.currentTarget.open)}><summary aria-label={`${label}: ${value.length} selected`}><span>{value.length?`${value.length} selected`:`Choose ${label.toLowerCase()}`}</span><ChevronDown size={16}/></summary><div className="profile-dropdown-menu" role="group" aria-label={label}>{options.map(option=><label key={option} className={value.includes(option)?'selected':''}><input type="checkbox" checked={value.includes(option)} onChange={()=>toggle(option)}/><span>{option}</span>{value.includes(option)&&<Check size={14}/>}</label>)}</div></details>{value.length>0&&<div className="profile-selection-tags">{value.map(option=><button type="button" key={option} onClick={()=>toggle(option)} aria-label={`Remove ${option}`}>{option} ×</button>)}</div>}</div>
}
