import os,time,json,secrets,hashlib,hmac
from typing import Literal
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .db import get_db,SessionLocal,engine,User,Story,Chapter,Snapshot,Invitation,Release,AdminEvent,Notification,UserPresence
from .security import current_user,is_admin
from .ops_models import Case,CaseReply,GuestCase,OperationEvent,OperationSetting,AIJob
from .support_delivery import CaseDetails, SupportMail, enqueue, queue_reply, notify_guest, support_settings
router=APIRouter()
def staff_role(u):
    if u.id in {v.strip() for v in os.getenv('ADMIN_USER_IDS','').split(',')}:return 'owner'
    for role in ('support','moderator','technical'):
        if u.id in {v.strip() for v in os.getenv('STAFF_'+role.upper()+'_IDS','').split(',')}:return role
    return None
def permit(*roles):
    def check(u=Depends(current_user)):
        if staff_role(u) not in ('owner',*roles):raise HTTPException(403,'Staff permission required')
        return u
    return check
def audit(db,u,action,target='',reason='',result='success'):
    db.add(OperationEvent(actor_id=u.id,action=action,target=target,reason=reason,result=result))
class Reason(BaseModel):
    reason:str=Field(min_length=3,max_length=1000)
class CaseIn(BaseModel):
    category:Literal['support','access','report','appeal','copyright','privacy_export','privacy_delete']
    subject:str=Field(min_length=3,max_length=160)
    body:str=Field(min_length=3,max_length=10000)
    urgency:Literal['low','normal','high','urgent']='normal'
    screenshot:str=Field(default='',max_length=2800000)
class ReplyIn(BaseModel):
    send_email:bool=False
    body:str=Field(min_length=3,max_length=10000)
class CaseUpdate(Reason):
    status:Literal['open','investigating','waiting_for_user','resolved','escalated']
    assigned_to:str|None=None
def can_case(u,c):
    role=staff_role(u)
    return c.user_id==u.id or role=='owner' or (role=='support' and c.category in ('support','access','privacy_export','privacy_delete')) or (role=='moderator' and c.category in ('report','appeal','copyright'))
def case_dict(c):return {k:getattr(c,k) for k in ('id','user_id','category','subject','status','assigned_to','created','updated')}
@router.post('/api/support/cases')
def create_case(data:CaseIn,db:Session=Depends(get_db),u=Depends(current_user)):
    if not data.subject.strip() or not data.body.strip():raise HTTPException(422,'Subject and message are required')
    if data.screenshot:
        import base64,binascii
        try:
            header,encoded=data.screenshot.split(',',1);raw=base64.b64decode(encoded,validate=True)
            valid=(header=='data:image/png;base64' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (header=='data:image/jpeg;base64' and raw.startswith(b'\xff\xd8\xff'))
            if not valid or len(raw)>2*1024*1024:raise ValueError()
        except (ValueError,binascii.Error):raise HTTPException(422,'Attach a PNG or JPEG screenshot smaller than 2 MB')
    c=Case(user_id=u.id,category=data.category,subject=data.subject.strip());db.add(c);db.flush()
    db.add(CaseDetails(case_id=c.id,urgency=data.urgency,screenshot=data.screenshot));db.flush()
    enqueue(db,c,u,'New support ticket')
    db.add(CaseReply(case_id=c.id,author_id=u.id,body=data.body.strip()));db.commit();return case_dict(c)
@router.get('/api/support/cases')
def my_cases(db:Session=Depends(get_db),u=Depends(current_user)):
    return [case_dict(c) for c in db.scalars(select(Case).where(Case.user_id==u.id).order_by(Case.updated.desc()).limit(100))]
@router.get('/api/support/cases/{case_id}')
def get_case(case_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(Case,case_id) or db.get(GuestCase,case_id)
    if not c or not can_case(u,c):raise HTTPException(404,'Case not found')
    if c.user_id!=u.id:audit(db,u,'case_viewed',c.id,'Support investigation');db.commit()
    if isinstance(c,GuestCase):return {**case_dict(c),'guest':True,'contact_email':c.email,'email_enabled':bool(support_settings()),'email_delivery':[m.status for m in db.scalars(select(SupportMail).where(SupportMail.case_id==c.id,SupportMail.recipient==c.email))],'replies':c.messages}
    details=db.get(CaseDetails,c.id)
    return {**case_dict(c),'urgency':details.urgency if details else 'normal','screenshot':details.screenshot if details else '', 'email_enabled':bool(support_settings()),'email_delivery':[m.status for m in db.scalars(select(SupportMail).where(SupportMail.case_id==c.id))],'replies':[{'id':r.id,'author':db.get(User,r.author_id).name,'body':r.body,'created':r.created} for r in db.scalars(select(CaseReply).where(CaseReply.case_id==c.id).order_by(CaseReply.created))]}
@router.post('/api/support/cases/{case_id}/replies')
def reply(case_id:str,data:ReplyIn,db:Session=Depends(get_db),u=Depends(current_user)):
    c=db.get(Case,case_id) or db.get(GuestCase,case_id)
    if not c or not can_case(u,c):raise HTTPException(404,'Case not found')
    if not data.body.strip():raise HTTPException(422,'Message required')
    if data.send_email:
        if staff_role(u) not in ('owner','support','moderator') or c.user_id==u.id:raise HTTPException(403,'Staff access required to email a reply')
        if not support_settings():raise HTTPException(503,'Email sending is not configured. The reply has not been sent.')
        queue_reply(db,c,data.body.strip())
    if isinstance(c,GuestCase):
        c.messages=[*c.messages,{'id':secrets.token_hex(16),'author':'Support','body':data.body.strip(),'created':time.time()}];c.updated=time.time()
        audit(db,u,'case_reply',c.id,'Reply to guest participant');db.commit();return {'ok':True}
    db.add(CaseReply(case_id=c.id,author_id=u.id,body=data.body.strip()));c.updated=time.time()
    if c.user_id!=u.id:
        audit(db,u,'case_reply',c.id,'Reply to participant')
        db.add(Notification(sender_id=u.id,user_id=c.user_id,title='Support replied: '+c.subject[:130],body='Open Help & support to read the reply.'))
    if not data.send_email:enqueue(db,c,u,'Support replied' if c.user_id!=u.id else 'Requester replied')
    db.commit();return {'ok':True}
@router.get('/api/admin/ops/cases')
def cases(category:str='',status:str='',db:Session=Depends(get_db),u=Depends(permit('support','moderator'))):
    q=select(Case).order_by(Case.updated.desc())
    if category:q=q.where(Case.category==category)
    if status:q=q.where(Case.status==status)
    guests=select(GuestCase)
    if category:guests=guests.where(GuestCase.category==category)
    if status:guests=guests.where(GuestCase.status==status)
    combined=[case_dict(c) for c in db.scalars(q) if can_case(u,c)]+[{**case_dict(c),'guest':True} for c in db.scalars(guests) if can_case(u,c)]
    return sorted(combined,key=lambda c:c['updated'],reverse=True)[:200]
@router.put('/api/admin/ops/cases/{case_id}')
def update_case(case_id:str,data:CaseUpdate,db:Session=Depends(get_db),u=Depends(permit('support','moderator'))):
    c=db.get(Case,case_id) or db.get(GuestCase,case_id)
    if not c or not can_case(u,c):raise HTTPException(404,'Case not found')
    if data.assigned_to:
        assignee=db.get(User,data.assigned_to)
        if not assignee or not staff_role(assignee) or not can_case(assignee,c):raise HTTPException(422,'Assignee needs access to this case')
    c.status=data.status
    if not isinstance(c,GuestCase):c.assigned_to=data.assigned_to
    c.updated=time.time()
    audit(db,u,'case_'+data.status,c.id,data.reason);db.commit();return case_dict(c)
@router.get('/api/admin/ops/access/{release_id}')
def access_check(release_id:str,db:Session=Depends(get_db),u=Depends(permit('support','technical'))):
    r=db.get(Release,release_id)
    if not r:raise HTTPException(404,'Release not found')
    c=db.get(Chapter,r.chapter_id);s=db.get(Snapshot,r.snapshot_id);reader=db.get(User,r.reader_id)
    inv=db.scalar(select(Invitation).where(Invitation.story_id==c.story_id,Invitation.email==reader.email))
    checks={'release_active':bool(r.active),'invitation_accepted':bool(inv and inv.status=='accepted'),'snapshot_matches_chapter':bool(s and s.chapter_id==c.id),'snapshot_verified':bool(s and s.status=='verified')}
    audit(db,u,'permission_diagnosis',r.id,'Metadata-only permission check');db.commit()
    return {'checks':checks,'allowed':all(checks.values()),'chapter_id':c.id,'snapshot_id':r.snapshot_id}
@router.post('/api/admin/ops/connections/{invitation_id}/revoke')
def revoke_connection(invitation_id:str,data:Reason,db:Session=Depends(get_db),u=Depends(permit('moderator'))):
    inv=db.get(Invitation,invitation_id)
    if not inv:raise HTTPException(404,'Invitation not found')
    inv.status='revoked'
    reader=db.scalar(select(User).where(User.email==inv.email))
    if reader:
        ids=select(Chapter.id).where(Chapter.story_id==inv.story_id)
        for r in db.scalars(select(Release).where(Release.reader_id==reader.id,Release.chapter_id.in_(ids))):r.active=0
    audit(db,u,'connection_revoked',inv.id,data.reason);db.commit();return {'ok':True}
@router.get('/api/admin/ops/stories')
def stories(db:Session=Depends(get_db),u=Depends(permit('support','technical','moderator'))):
    rows=[]
    for story in db.scalars(select(Story)):
        chapters=[]
        for c in db.scalars(select(Chapter).where(Chapter.story_id==story.id).order_by(Chapter.position)):
            snaps=[{'id':s.id,'revision':s.revision,'status':s.status,'mode':s.mode,'created':s.created,'current':s.revision==c.revision} for s in db.scalars(select(Snapshot).where(Snapshot.chapter_id==c.id).order_by(Snapshot.created.desc()))]
            chapters.append({'id':c.id,'title':c.title,'state':c.state,'revision':c.revision,'snapshots':snaps,'releases':db.scalar(select(func.count()).select_from(Release).where(Release.chapter_id==c.id,Release.active==1))})
        rows.append({'id':story.id,'title':story.title,'owner':db.get(User,story.writer_id).name,'genre':story.genre,'chapters':chapters})
    return rows
@router.get('/api/admin/ops/audit')
def logs(q:str='',after:float=0,before:float=1e20,page:int=Query(1,ge=1),db:Session=Depends(get_db),u=Depends(permit('technical'))):
    result=[{k:getattr(e,k) for k in ('id','actor_id','action','target','reason','result','created')} for e in db.scalars(select(OperationEvent).where(OperationEvent.created>=after,OperationEvent.created<=before))]
    for event in db.scalars(select(AdminEvent).where(AdminEvent.created>=after,AdminEvent.created<=before)):
        details={}
        if event.action.startswith('admin_account_edit: '):
            try: details=json.loads(event.action.split(': ',1)[1])
            except ValueError: pass
        result.append({'id':event.id,'actor_id':event.actor_id,'action':event.action.split(': ',1)[0],'target':event.resource_id,'reason':details.get('reason',''),'result':'success','created':event.created})
    if q:result=[r for r in result if q.casefold() in ' '.join(str(r[k] or '') for k in ('action','target','reason','actor_id')).casefold()]
    result.sort(key=lambda r:(r['created'],r['id']),reverse=True)
    return {'total':len(result),'items':result[(page-1)*50:page*50]}
@router.get('/api/admin/ops/health')
def health(db:Session=Depends(get_db),u=Depends(permit('technical'))):
    from .local_ai import availability,active_model,provider
    db.scalar(select(func.count()).select_from(User))
    backups=[]
    if engine.dialect.name=='sqlite':
        folder=Path(engine.url.database).resolve().parent/'backups'
        backups=sorted(folder.glob('*.sqlite3'),key=lambda p:p.stat().st_mtime,reverse=True)[:5]
    return {'database':'Available','ai_available':availability(),'ai_provider':provider(),'model':active_model(),'backups':[{'name':p.name,'created':p.stat().st_mtime,'bytes':p.stat().st_size} for p in backups],'mail_enabled':os.getenv('MAIL_ENABLED','false')=='true','roles':{'owner':'Full administration','support':'Support cases and metadata','moderator':'Reports and connection revocation','technical':'AI controls, diagnostics and audit'}}
@router.get('/api/admin/ops/ai')
def jobs(db:Session=Depends(get_db),u=Depends(permit('technical'))):
    setting=db.get(OperationSetting,'local_ai_paused')
    return {'paused':bool(setting and setting.value.get('enabled')),'jobs':[{k:getattr(j,k) for k in ('id','feature','model','status','started','ended','input_tokens','output_tokens')} for j in db.scalars(select(AIJob).order_by(AIJob.started.desc()).limit(100))]}
class PauseIn(Reason):
    enabled:bool
@router.put('/api/admin/ops/ai/pause')
def pause(data:PauseIn,db:Session=Depends(get_db),u=Depends(permit('technical'))):
    s=db.get(OperationSetting,'local_ai_paused')
    if not s:s=OperationSetting(key='local_ai_paused');db.add(s)
    s.value={'enabled':data.enabled};audit(db,u,'local_ai_paused' if data.enabled else 'local_ai_resumed','local_ai',data.reason);db.commit();return {'ok':True}

class GuestRequest(BaseModel):
    email:str=Field(min_length=3,max_length=254,pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    subject:str=Field(min_length=3,max_length=160)
    body:str=Field(min_length=3,max_length=10000)
class GuestAccess(BaseModel):
    id:str=Field(max_length=36)
    token:str=Field(min_length=32,max_length=128)
    body:str=Field(default='',max_length=10000)
@router.post('/api/support/guest')
def guest_create(data:GuestRequest,request:Request,db:Session=Depends(get_db)):
    from .main import throttle
    throttle(request)
    if len(data.subject.strip())<3 or len(data.body.strip())<3:raise HTTPException(422,'Please enter a subject and message')
    token=secrets.token_urlsafe(32)
    c=GuestCase(email=data.email.strip().lower(),subject=data.subject.strip(),token_hash=hashlib.sha256(token.encode()).hexdigest(),messages=[{'id':secrets.token_hex(16),'author':'Requester (unverified)','body':data.body.strip(),'created':time.time()}])
    db.add(c);db.flush();notify_guest(db,c);db.commit()
    return {'id':c.id,'token':token}
@router.post('/api/support/guest/check')
def guest_check(data:GuestAccess,request:Request,db:Session=Depends(get_db)):
    from .main import throttle
    throttle(request)
    c=db.get(GuestCase,data.id)
    if not c or not hmac.compare_digest(c.token_hash,hashlib.sha256(data.token.encode()).hexdigest()):raise HTTPException(404,'Request or access code not found')
    if data.body:
        if len(data.body.strip())<3:raise HTTPException(422,'Please enter a message')
        c.messages=[*c.messages,{'id':secrets.token_hex(16),'author':'Requester (unverified)','body':data.body.strip(),'created':time.time()}];c.updated=time.time();notify_guest(db,c);db.commit()
    return {**case_dict(c),'replies':c.messages}

@router.get('/api/admin/ops/case-assignees/{case_id}')
def case_assignees(case_id:str,db:Session=Depends(get_db),u=Depends(permit('support','moderator'))):
    c=db.get(Case,case_id)
    if not c or not can_case(u,c):raise HTTPException(404,'Case not found')
    return [{'id':a.id,'name':a.name} for a in db.scalars(select(User)) if staff_role(a) and can_case(a,c)]
