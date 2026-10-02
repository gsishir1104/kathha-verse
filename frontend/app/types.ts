export type User = {is_admin?:boolean;staff_role?:string|null;id:string;name:string;email:string;role:'writer'|'beta'|'reader';preferences:{interactive_reading?:boolean}};
export type Knowledge = {text:string;state:'knows'|'does_not_know'|'believes'|'feels';reader_safe:boolean;evidence:string;subject_id?:string;secret_id?:string;truth?:string};
export type Entity = {id:string;kind:string;name:string;summary:string;evidence:string;confidence:number;reader_safe:boolean;status:'pending'|'confirmed'|'rejected';links:string[];knowledge:Knowledge[];relations?:{target_id:string;label:string;strength:number;evidence:string}[];goals?:{text:string;evidence:string;reader_safe:boolean}[];conflicts?:{text:string;evidence:string;reader_safe:boolean}[];timeline_order?:number|null;story_time?:string;thread_status?:string;character_status?:string;certainty?:string;uncertainty_reason?:string};
export type ChapterFact = {category:'relationship'|'location'|'object'|'event';text:string;evidence:string;order:number;entity_ids:string[]};
export type PromptQuestion = {review_status?:string;text:string;category:string;evidence:string;options?:string[];timing?:string;checkpoint?:number|null;target?:string};
export type Universe = {question_frequency?:string;entities:Entity[];questions?:PromptQuestion[];facts?:ChapterFact[]};
export type Snapshot = {id:string;revision:number;status:string;mode:string;universe:Universe};
export type Intent = {emotion?:string;tension?:number|null;prediction_target?:string;desired_predictability?:number|null;notes?:string;targets?:{metric:string;target:string;expected:number;reveal_chapter:number|null;notes:string}[];scenes?:{label:string;evidence:string;reaction:string}[]};
export type Chapter = {id:string;story_id:string;position:number;title:string;content:string;revision:number;intent:Intent;state:string;snapshot?:Snapshot|null};
export type Story = {id:string;title:string;description:string;genre:string;settings?:{cover?:string;status?:string;tags?:string[]};chapters:Chapter[]};
export type Invitation = {id:string;email:string;name:string;reader_id:string|null;status:string;releases:{id:string;chapter_id:string;active:boolean;progress:number}[]};
export type ReaderQuestion = {id:string;text:string;category:string;source:string;options?:string[];answer:null|{text:string;confidence:number;emotion:string;tension:number}};
export type Annotation = {id:string;start:number;end:number;quote:string;category:string;text:string};
export type Reading = {id:string;snapshot_id:string;title:string;content:string;position:number;revision:number;universe:Universe;questions:ReaderQuestion[];feedback:Annotation[];progress:number;checkpoint_pending?:boolean};
export type LibraryItem = {id:string;title:string;story_title:string;position:number;progress:number;revision:number};
export type InboxItem = {id:string;status:string;story_title:string;writer:string};
export type Memory = {chapter:number;question:string;answer:string;confidence:number;category:string;emotion:string};
export type Analytic = {chapter:number;title:string;revision:number;snapshot_id:string;released:number;completed:number;respondents:number;answers:number;intent:Intent;tension:number|null;emotion_match:number|null;prediction_respondents:number;prediction_matches:number|null;predictability:number|null;prediction_method:string;feedback:{id:string;quote:string;category:string;text:string;reader:string}[];responses:{reader:string;question:string;answer:string;confidence:number;emotion:string;tension:number}[]};
export async function api<T>(path:string,method='GET',body?:unknown):Promise<T>{
 const base = process.env.NEXT_PUBLIC_API_URL || (typeof window!=='undefined' && window.location.port==='3000' ? 'http://127.0.0.1:8000' : '');
 let response:Response;
 try{response=await fetch(base+'/api'+path,{method,credentials:'include',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});}catch{throw new Error('Cannot reach the story service. Check that the API is running and try again.');}
 if(!response.ok){const error=await response.json().catch(()=>({}));throw new Error(typeof error.detail==='string'?error.detail:response.status===401?'Please sign in':`Please check your input (${response.status})`);}
 return response.json();
}
