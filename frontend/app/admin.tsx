'use client';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Activity,BookOpen,Mail,RefreshCw,Search,ShieldCheck,Users} from 'lucide-react';
import {api} from './types';
import AccountDashboard from './admin-account';
import {Act} from './writer';

type Account={id:string;name:string;email:string;role:string;suspended:boolean;is_admin:boolean;last_active?:number|null;last_login?:number|null};
type Overview={counts:Record<string,number>;email_enabled:boolean;email_status:Record<string,number>;ai_provider:string};
type Event={id:string;actor:string;action:string;resource:string;created:number;detail?:{reason:string;before:{name:string;role:string;suspended:boolean};after:{name:string;role:string;suspended:boolean}}};
type UserLog={items:{id:string;action:string;resource:string;created:number}[];total:number;first_seen:number|null;last_login:number|null;last_active:number|null;sessions:number};
export type AdminPanel='overview'|'users'|'notifications'|'activity';

const timestamp=(v?:number|null)=>v?new Date(v*1000).toLocaleString():'Not recorded yet';
const label=(value:string)=>value.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());

export default function Admin({act,busy,userId,panel='overview',onNavigate}:{act:Act;busy:boolean;userId:string;panel?:AdminPanel;onNavigate?:(panel:AdminPanel)=>void}){
 const [selected,setSelected]=useState<string|null>(null),[detailVersion,setDetailVersion]=useState(0);
 const [overview,setOverview]=useState<Overview|null>(null),[accounts,setAccounts]=useState<Account[]>([]),[events,setEvents]=useState<Event[]>([]),[query,setQuery]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[total,setTotal]=useState(0),[editing,setEditing]=useState<Account|null>(null),[reason,setReason]=useState('');
 const [recipients,setRecipients]=useState<Record<string,string>>({}),[noticeTitle,setNoticeTitle]=useState(''),[noticeBody,setNoticeBody]=useState('');
 const [viewing,setViewing]=useState<Account|null>(null),[log,setLog]=useState<UserLog|null>(null),[logPage,setLogPage]=useState(1);
 const activityDialog=useRef<HTMLDialogElement>(null),dialog=useRef<HTMLDialogElement>(null);
 async function showActivity(account:Account,p=1){await act(async()=>{const data=await api<UserLog>('/admin/accounts/'+account.id+'/activity?page='+p);setLog(data);setLogPage(p);setViewing(account)})}
 useEffect(()=>{if(viewing&&!activityDialog.current?.open)activityDialog.current?.showModal()},[viewing]);
 useEffect(()=>{if(editing&&!dialog.current?.open)dialog.current?.showModal()},[editing]);
 async function refresh(){const [o,a,e]=await Promise.all([api<Overview>('/admin/overview'),api<{items:Account[];total:number}>('/admin/accounts?q='+encodeURIComponent(search)+'&page='+page),api<Event[]>('/admin/activity')]);setOverview(o);setAccounts(a.items);setTotal(a.total);setEvents(e)}
 useEffect(()=>{void act(refresh)},[search,page]);
 const failedEmails=useMemo(()=>Object.entries(overview?.email_status||{}).filter(([key])=>/fail|bounce|error/i.test(key)).reduce((sum,[,value])=>sum+value,0),[overview]);
 const suspendedHere=accounts.filter(account=>account.suspended).length;
 const count=(key:string)=>overview?.counts[key]??0;
 const go=(next:AdminPanel)=>{onNavigate?.(next);window.scrollTo({top:0,behavior:'smooth'})};
 const openUsers=()=>go('users');
 const statCards=[
  {key:'accounts',title:'Total users',value:count('accounts'),detail:'Manage access and roles',icon:Users,onClick:openUsers},
  {key:'stories',title:'Active stories',value:count('stories'),detail:`${count('chapters')} chapters`,icon:BookOpen},
  {key:'feedback',title:'Reader feedback',value:count('feedback'),detail:`${count('releases')} chapter releases`,icon:MessageSquareIcon},
  {key:'active_sessions',title:'Active sessions',value:count('active_sessions'),detail:'Currently signed-in sessions',icon:Activity}
 ];

 return <section className="admin-dashboard">
  {selected&&<AccountDashboard key={selected+detailVersion} id={selected} act={act} busy={busy} onBack={()=>{setSelected(null);void act(refresh)}} onEdit={a=>{setEditing({...a});setReason('')}} onActivity={a=>showActivity(a)}/>} 
  <div hidden={!!selected}>
   <div className="admin-page-tools"><p>{panel==='overview'?'A clear view of what needs attention across KathhaVerse.':panel==='users'?'Manage roles, access, and account status.':panel==='notifications'?'Send a private in-app update to selected users.':'Review changes made by administrators.'}</p><button className="button admin-refresh" disabled={busy} onClick={()=>act(refresh)}><RefreshCw size={16}/> Refresh data</button></div>

   {panel==='overview'&&<>
    <div className="admin-summary-grid">{statCards.map(({key,title,value,detail,icon:Icon,onClick})=><article className="admin-summary-card" key={key}><div className="admin-summary-icon"><Icon size={19}/></div><div><span>{title}</span><strong>{value.toLocaleString()}</strong><small>{detail}</small></div>{onClick&&<button className="text-button" onClick={onClick}>View</button>}</article>)}</div>
    <div className="admin-overview-grid">
     <section className="admin-panel admin-attention"><div className="admin-panel-heading"><div><p className="eyebrow">PRIORITY</p><h2>Needs your attention</h2></div><span className="admin-status-pill">{failedEmails+suspendedHere} items</span></div>
      {failedEmails>0&&<div className="admin-attention-row"><span className="admin-severity danger">Email</span><div><strong>{failedEmails} welcome {failedEmails===1?'email has':'emails have'} failed</strong><small>Review delivery status in Platform operations.</small></div></div>}
      {suspendedHere>0&&<button className="admin-attention-row admin-attention-button" onClick={openUsers}><span className="admin-severity warning">Account</span><div><strong>{suspendedHere} suspended {suspendedHere===1?'account':'accounts'} on this page</strong><small>Open Users to review account access.</small></div></button>}
      {!failedEmails&&!suspendedHere&&<div className="admin-empty"><ShieldCheck size={22}/><div><strong>No urgent items in this view</strong><small>Email delivery and the visible accounts do not need attention.</small></div></div>}
     </section>
     <section className="admin-panel"><div className="admin-panel-heading"><div><p className="eyebrow">SERVICES</p><h2>Current configuration</h2></div></div>
      <div className="admin-service-row"><span>AI provider</span><strong>{overview?.ai_provider||'Checking…'}</strong></div>
      <div className="admin-service-row"><span>Welcome emails</span><span className={'admin-status-pill '+(overview?.email_enabled?'success':'warning')}>{overview?.email_enabled?'Enabled':'Not enabled'}</span></div>
      {Object.entries(overview?.email_status||{}).map(([key,value])=><div className="admin-service-row" key={key}><span>{label(key)}</span><strong>{value}</strong></div>)}
      {!Object.keys(overview?.email_status||{}).length&&<p className="muted">No welcome emails are queued.</p>}
      <small>Configuration status is shown here. Live service checks remain in Platform operations.</small>
     </section>
    </div>
    <section className="admin-panel"><div className="admin-panel-heading"><div><p className="eyebrow">RECENT CHANGES</p><h2>Administrator activity</h2></div><button className="text-button" onClick={()=>go('activity')}>View all</button></div>
     <div className="admin-timeline">{events.slice(0,5).map(event=><article key={event.id}><span className="admin-timeline-dot"/><div><strong>{event.action}</strong><p>{event.resource}</p><small>{timestamp(event.created)} · {event.actor}</small></div></article>)}{!events.length&&<div className="admin-empty"><Activity size={22}/><div><strong>No administrator changes yet</strong><small>Account and notification actions will appear here.</small></div></div>}</div>
    </section>
   </>}

   {panel==='users'&&<section className="admin-panel admin-users-panel"><div className="admin-panel-heading"><div><p className="eyebrow">PEOPLE & ACCESS</p><h2>Users</h2><p className="muted">{total.toLocaleString()} accounts</p></div></div>
    <form className="admin-search" onSubmit={e=>{e.preventDefault();setPage(1);setSearch(query)}}><Search size={17}/><input aria-label="Search accounts" placeholder="Search by name or email" value={query} onChange={e=>setQuery(e.target.value)}/><button className="button primary" disabled={busy}>Search</button>{search&&<button type="button" className="button" onClick={()=>{setQuery('');setSearch('');setPage(1)}}>Clear</button>}</form>
    <div className="admin-table"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last active</th><th>Actions</th></tr></thead><tbody>{accounts.map(account=><tr key={account.id}><td><button className="text-button admin-user-name" onClick={()=>setSelected(account.id)}>{account.name}</button><small>{account.email}</small></td><td>{account.is_admin?'Administrator':account.role==='beta'?'Beta reader':account.role==='writer'?'Writer':'Reader'}</td><td><span className={'admin-status-pill '+(account.suspended?'danger':'success')}>{account.suspended?'Suspended':'Active'}</span></td><td><small>{timestamp(account.last_active)}</small></td><td><div className="admin-actions"><button className="button" onClick={()=>setSelected(account.id)}>Open</button><button className="button" disabled={busy} onClick={()=>showActivity(account)}>Activity</button>{!account.is_admin&&<button className="button" disabled={busy||account.id===userId} onClick={()=>{setEditing({...account});setReason('')}}>Edit</button>}<label className="admin-notify-check"><input type="checkbox" aria-label={'Select '+account.email+' for notification'} checked={!!recipients[account.id]} onChange={e=>setRecipients(old=>{const next={...old};if(e.target.checked)next[account.id]=account.email;else delete next[account.id];return next})}/> Notify</label></div></td></tr>)}</tbody></table></div>
    {!accounts.length&&<div className="admin-empty"><Users size={22}/><div><strong>No matching users</strong><small>Try another name or email address.</small></div></div>}
    <div className="admin-pagination"><span>Page {page}</span><div><button className="button" disabled={busy||page===1} onClick={()=>setPage(page-1)}>Previous</button><button className="button" disabled={busy||page*25>=total} onClick={()=>setPage(page+1)}>Next</button></div></div>
    {!!Object.keys(recipients).length&&<div className="admin-selection-bar"><span>{Object.keys(recipients).length} selected</span><button className="button primary" onClick={()=>go('notifications')}>Write notification</button><button className="button" onClick={()=>setRecipients({})}>Clear</button></div>}
   </section>}

   {panel==='notifications'&&<form className="admin-panel admin-notification-form form-stack" onSubmit={e=>{e.preventDefault();if(!window.confirm('Send this notification to '+Object.keys(recipients).length+' selected accounts?'))return;void act(async()=>{await api('/admin/notifications','POST',{recipients:Object.keys(recipients),title:noticeTitle,body:noticeBody});setNoticeTitle('');setNoticeBody('');setRecipients({});await refresh()},'Notification sent')}}>
    <div className="admin-panel-heading"><div><p className="eyebrow">IN-APP MESSAGE</p><h2>Send a notification</h2><p className="muted">Choose recipients from Users, then write one clear message.</p></div><Mail size={24}/></div>
    <div className="admin-recipient-box"><strong>Recipients ({Object.keys(recipients).length})</strong><p>{Object.values(recipients).join(', ')||'No users selected yet.'}</p>{!Object.keys(recipients).length&&<button type="button" className="button" onClick={openUsers}>Choose users</button>}</div>
    <label>Title<input required maxLength={160} value={noticeTitle} onChange={e=>setNoticeTitle(e.target.value)} placeholder="Short notification title"/></label>
    <label>Message<textarea required maxLength={3000} value={noticeBody} onChange={e=>setNoticeBody(e.target.value)} placeholder="Write the message users will see inside KathhaVerse"/></label>
    <div className="admin-form-footer"><small>Up to 100 accounts. This appears inside the website and is not sent by email.</small><button className="button primary" disabled={busy||!Object.keys(recipients).length||Object.keys(recipients).length>100}>Send notification</button></div>
   </form>}

   {panel==='activity'&&<section className="admin-panel"><div className="admin-panel-heading"><div><p className="eyebrow">AUDIT TRAIL</p><h2>Administrator activity</h2><p className="muted">The 100 most recent account and notification changes.</p></div></div>
    <div className="admin-activity-list">{events.map(event=><article key={event.id}><div><strong>{event.action}</strong><p>{event.resource}</p>{event.detail&&<p className="admin-change-reason">Reason: {event.detail.reason}</p>}</div><div><span>{timestamp(event.created)}</span><small>{event.actor}</small></div></article>)}{!events.length&&<div className="admin-empty"><Activity size={22}/><div><strong>No activity recorded</strong><small>Administrator actions will appear here.</small></div></div>}</div>
   </section>}
  </div>

  {viewing&&log&&<dialog ref={activityDialog} className="admin-edit-dialog" aria-labelledby="user-activity-title" onCancel={()=>setViewing(null)}><div className="admin-card form-stack"><h2 id="user-activity-title">Activity: {viewing.name}</h2><p>{viewing.email}</p><p>Last active: {timestamp(log.last_active)}<br/>Last sign-in: {timestamp(log.last_login)}<br/>Unexpired sessions: {log.sessions}</p><p className="muted">Activity tracking began for this account: {timestamp(log.first_seen)}. Earlier activity is unavailable. Last active means the last successful authenticated request.</p>{log.items.map(item=><div key={item.id}><strong>{item.action}</strong><p>{timestamp(item.created)}</p>{item.resource&&<small>Reference: {item.resource}</small>}</div>)}{!log.items.length&&<p>No recorded changes yet.</p>}<div className="row"><button className="button" disabled={busy||logPage===1} onClick={()=>showActivity(viewing,logPage-1)}>Previous</button><span>Page {logPage}</span><button className="button" disabled={busy||logPage*25>=log.total} onClick={()=>showActivity(viewing,logPage+1)}>Next</button></div><button className="button" onClick={()=>setViewing(null)}>Close</button></div></dialog>}
  {editing&&<dialog ref={dialog} className="admin-edit-dialog" aria-labelledby="admin-edit-title" onCancel={()=>setEditing(null)}><form className="admin-card form-stack" onSubmit={e=>{e.preventDefault();void act(async()=>{await api('/admin/accounts/'+editing.id,'PUT',{name:editing.name,role:editing.role,suspended:editing.suspended,reason});setEditing(null);setDetailVersion(v=>v+1);await refresh()},'Account updated and signed out')}}><h2 id="admin-edit-title">Edit {editing.email}</h2><label>Name<input required maxLength={100} value={editing.name} onChange={e=>setEditing({...editing,name:e.target.value})}/></label><label>Role<select disabled={editing.is_admin} value={editing.role} onChange={e=>setEditing({...editing,role:e.target.value})}><option value="writer">Writer</option><option value="beta">Beta reader</option><option value="reader">Reader</option></select></label><label>Status<select disabled={editing.is_admin} value={editing.suspended?'suspended':'active'} onChange={e=>setEditing({...editing,suspended:e.target.value==='suspended'})}><option value="active">Active</option><option value="suspended">Suspended</option></select></label><label>Reason for change<textarea required minLength={3} maxLength={300} value={reason} onChange={e=>setReason(e.target.value)}/></label><p>Saving signs the account out of all devices. Suspension preserves its stories and feedback.</p><div className="row"><button className="button primary" disabled={busy}>Save changes</button><button type="button" className="button" onClick={()=>setEditing(null)}>Cancel</button></div></form></dialog>}
 </section>
}

function MessageSquareIcon({size=19}:{size?:number}){
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>
}

