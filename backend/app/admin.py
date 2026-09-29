"""Owner-only administration; no credential or manuscript disclosure."""
import os, time, json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from .db import get_db, User, AccountControl, SessionToken, Story, Chapter, Release, Feedback, AdminEvent as Audit, UserPresence, UserActivity, Notification, Invitation, Answer, Question
from .security import current_user, is_admin
from .welcome_email import WelcomeEmail
router = APIRouter(prefix='/api/admin')
def administrator(u=Depends(current_user)):
    from .operations import staff_role
    if staff_role(u)!='owner': raise HTTPException(403,'Owner administrator access required')
    return u
class AccountEdit(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    role: Literal['writer','beta','reader']
    suspended: bool
    reason: str = Field(min_length=3,max_length=300)
@router.get('/overview')
def overview(db:Session=Depends(get_db),u=Depends(administrator)):
    counts={name:db.scalar(select(func.count()).select_from(model)) for name,model in [('accounts',User),('stories',Story),('chapters',Chapter),('releases',Release),('feedback',Feedback)]}
    counts['active_sessions']=db.scalar(select(func.count()).select_from(SessionToken).where(SessionToken.expires>time.time()))
    return {'counts':counts,'email_enabled':os.getenv('MAIL_ENABLED','false').lower()=='true','email_status':dict(db.execute(select(WelcomeEmail.status,func.count()).group_by(WelcomeEmail.status)).all()),'ai_provider':os.getenv('AI_PROVIDER','openai')}
@router.get('/accounts')
def accounts(q:str=Query('',max_length=254),page:int=Query(1,ge=1),db:Session=Depends(get_db),u=Depends(administrator)):
    query=select(User)
    if q.strip(): query=query.where(User.email.contains(q.strip(),autoescape=True)|User.name.contains(q.strip(),autoescape=True))
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    rows=[]
    for user in db.scalars(query.order_by(User.email).offset((page-1)*25).limit(25)):
        c=db.get(AccountControl,user.id)
        presence=db.get(UserPresence,user.id)
        rows.append({'id':user.id,'name':user.name,'email':user.email,'role':user.role,'suspended':bool(c and c.suspended),'is_admin':is_admin(user),'last_active':presence.last_active if presence else None,'last_login':presence.last_login if presence else None})
    return {'items':rows,'total':total}
@router.put('/accounts/{user_id}')
def edit_account(user_id:str,data:AccountEdit,db:Session=Depends(get_db),u=Depends(administrator)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,'Account not found')
    if not data.name.strip() or not data.reason.strip(): raise HTTPException(422,'Name and reason are required')
    if is_admin(target) and (data.suspended or data.role!=target.role): raise HTTPException(409,'Administrator roles and access are managed on the server')
    if target.role=='writer' and data.role!='writer' and db.scalar(select(func.count()).select_from(Story).where(Story.writer_id==target.id)):
        raise HTTPException(409,'This writer owns stories. Keep their writer role to preserve access.')
    control=db.get(AccountControl,user_id)
    if not control: control=AccountControl(user_id=user_id);db.add(control)
    before={'name':target.name,'role':target.role,'suspended':bool(control.suspended)}
    target.name=data.name.strip();target.role=data.role;control.suspended=int(data.suspended)
    db.execute(delete(SessionToken).where(SessionToken.user_id==user_id))
    db.add(Audit(actor_id=u.id,action='admin_account_edit: '+json.dumps({'reason':data.reason.strip(),'before':before,'after':{'name':target.name,'role':target.role,'suspended':data.suspended}}),resource_id=user_id))
    db.commit();return {'ok':True}
@router.post('/accounts/{user_id}/revoke-sessions')
def revoke(user_id:str,db:Session=Depends(get_db),u=Depends(administrator)):
    if not db.get(User,user_id): raise HTTPException(404,'Account not found')
    db.execute(delete(SessionToken).where(SessionToken.user_id==user_id))
    db.add(Audit(actor_id=u.id,action='admin_sessions_revoked',resource_id=user_id));db.commit();return {'ok':True}
@router.get('/activity')
def activity(db:Session=Depends(get_db),u=Depends(administrator)):
    result=[]
    for a in db.scalars(select(Audit).order_by(Audit.created.desc()).limit(100)):
        actor=db.get(User,a.actor_id);target=db.get(User,a.resource_id)
        detail=json.loads(a.action.split(': ',1)[1]) if a.action.startswith('admin_account_edit: ') else None
        result.append({'id':a.id,'actor':actor.name if actor else a.actor_id,'action':'Account updated' if detail else ('Notification sent' if a.action=='admin_notification_sent' else 'Signed out all devices'),'resource':target.email if target else a.resource_id,'created':a.created,'detail':detail})
    return result

@router.get('/accounts/{user_id}/activity')
def user_activity(user_id:str,page:int=Query(1,ge=1),db:Session=Depends(get_db),u=Depends(administrator)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,'Account not found')
    query=select(UserActivity).where(UserActivity.user_id==user_id)
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    rows=db.scalars(query.order_by(UserActivity.created.desc(),UserActivity.id).offset((page-1)*25).limit(25))
    presence=db.get(UserPresence,user_id)
    return {'items':[{'id':a.id,'action':a.action,'resource':a.resource,'created':a.created} for a in rows],'total':total,'first_seen':presence.first_seen if presence else None,'last_login':presence.last_login if presence else None,'last_active':presence.last_active if presence else None,'sessions':db.scalar(select(func.count()).select_from(SessionToken).where(SessionToken.user_id==user_id,SessionToken.expires>time.time()))}

class NoticeIn(BaseModel):
    recipients: list[str] = Field(min_length=1,max_length=100)
    title: str = Field(min_length=1,max_length=160)
    body: str = Field(min_length=1,max_length=3000)
@router.post('/notifications')
def send_notice(data:NoticeIn,db:Session=Depends(get_db),u=Depends(administrator)):
    ids=set(data.recipients)
    if not data.title.strip() or not data.body.strip(): raise HTTPException(422,'Title and message are required')
    if db.scalar(select(func.count()).select_from(User).where(User.id.in_(ids)))!=len(ids): raise HTTPException(404,'Recipient not found')
    for uid in ids:
        db.add(Notification(sender_id=u.id,user_id=uid,title=data.title.strip(),body=data.body.strip()))
        db.add(Audit(actor_id=u.id,action='admin_notification_sent',resource_id=uid))
    db.commit();return {'sent':len(ids)}
@router.get('/relationships')
def relationships(db:Session=Depends(get_db),u=Depends(administrator)):
    users={a.id:a for a in db.scalars(select(User))};emails={a.email:a for a in users.values()}
    stories={s.id:s for s in db.scalars(select(Story))};chapters={c.id:c for c in db.scalars(select(Chapter))}
    releases=list(db.scalars(select(Release)))
    answer_counts=dict(db.execute(select(Answer.release_id,func.count()).group_by(Answer.release_id)).all())
    feedback_counts=dict(db.execute(select(Feedback.release_id,func.count()).group_by(Feedback.release_id)).all())
    rows=[];writer_sets={};reader_sets={}
    for inv in db.scalars(select(Invitation)):
        story=stories[inv.story_id];writer=users[story.writer_id];reader=emails.get(inv.email)
        sent=[r for r in releases if reader and r.reader_id==reader.id and chapters[r.chapter_id].story_id==story.id]
        active=[r for r in sent if r.active and inv.status=='accepted']
        completed=sum(r.progress>=100 for r in active)
        writer_sets.setdefault(writer.id,{'invited':set(),'accepted':set()})['invited'].add(inv.email)
        reader_sets.setdefault(inv.email,{'invited':set(),'accepted':set()})['invited'].add(writer.id)
        if inv.status=='accepted':
            writer_sets[writer.id]['accepted'].add(inv.email);reader_sets[inv.email]['accepted'].add(writer.id)
        rows.append({'id':inv.id,'story_id':story.id,'writer':writer.name,'writer_email':writer.email,'reader':reader.name if reader else 'Not registered','reader_email':inv.email,'story':story.title,'status':inv.status,'released':len(active),'completed':completed,'all_released_read':bool(active) and completed==len(active),'chapters':[{'title':chapters[r.chapter_id].title,'position':chapters[r.chapter_id].position,'progress':r.progress,'active':r in active,'answers':answer_counts.get(r.id,0),'feedback':feedback_counts.get(r.id,0)} for r in sorted(sent,key=lambda r:chapters[r.chapter_id].position)]})
    writers=[{'name':a.name,'email':a.email,'invited':len(writer_sets.get(a.id,{}).get('invited',set())),'accepted':len(writer_sets.get(a.id,{}).get('accepted',set()))} for a in users.values() if a.role=='writer' and not is_admin(a)]
    readers=[{'name':a.name,'email':a.email,'invited':len(reader_sets.get(a.email,{}).get('invited',set())),'accepted':len(reader_sets.get(a.email,{}).get('accepted',set()))} for a in users.values() if a.role=='beta' and not is_admin(a)]
    return {'relationships':rows,'writers':writers,'readers':readers}
@router.get('/accounts/{user_id}/dashboard')
def account_dashboard(user_id:str,db:Session=Depends(get_db),u=Depends(administrator)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,'Account not found')
    control=db.get(AccountControl,user_id);presence=db.get(UserPresence,user_id)
    pairs=[r for r in relationships(db,u)['relationships'] if r['writer_email']==target.email or r['reader_email']==target.email]
    stories=[]
    for story in db.scalars(select(Story).where(Story.writer_id==user_id)):
        chapters=list(db.scalars(select(Chapter).where(Chapter.story_id==story.id).order_by(Chapter.position)))
        stories.append({'id':story.id,'title':story.title,'words':sum(len(c.content.split()) for c in chapters),'chapters':[{'id':c.id,'title':c.title,'position':c.position,'state':c.state,'words':len(c.content.split()),'revision':c.revision} for c in chapters]})
    return {'account':{'id':target.id,'name':target.name,'email':target.email,'role':target.role,'is_admin':is_admin(target),'suspended':bool(control and control.suspended),'last_active':presence.last_active if presence else None,'last_login':presence.last_login if presence else None},'stories':stories,'relationships':pairs,'sessions':db.scalar(select(func.count()).select_from(SessionToken).where(SessionToken.user_id==user_id,SessionToken.expires>time.time()))}
