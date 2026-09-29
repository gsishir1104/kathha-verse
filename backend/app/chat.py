"""Private, invitation-scoped conversations. No manuscript content is fetched."""
import time
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import select,String,Float,Text,ForeignKey,func
from sqlalchemy.orm import Mapped,mapped_column,Session
from .db import Base,uid,get_db,User,Story,Invitation,AccountControl
from .security import current_user,is_admin
router=APIRouter()
class ChatMessage(Base):
    __tablename__='chat_messages'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    invitation_id:Mapped[str]=mapped_column(ForeignKey('invitations.id'),index=True)
    sender_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    body:Mapped[str]=mapped_column(Text)
    created:Mapped[float]=mapped_column(Float,default=time.time,index=True)
class ChatPresence(Base):
    __tablename__='chat_presence'
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    seen:Mapped[float]=mapped_column(Float,default=time.time)
class ChatRead(Base):
    __tablename__='chat_reads'
    invitation_id:Mapped[str]=mapped_column(ForeignKey('invitations.id'),primary_key=True)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    seen:Mapped[float]=mapped_column(Float,default=0)
class MessageIn(BaseModel):
    body:str=Field(min_length=1,max_length=4000)
def participants(db,i,u):
    if not i or i.status!='accepted' or is_admin(u):raise HTTPException(404,'Conversation unavailable')
    s=db.get(Story,i.story_id);b=db.scalar(select(User).where(User.email==i.email,User.role=='beta'))
    if not s or not b or u.id not in (s.writer_id,b.id):raise HTTPException(404,'Conversation unavailable')
    other=db.get(User,b.id if u.id==s.writer_id else s.writer_id)
    control=db.get(AccountControl,other.id)
    if control and control.suspended:raise HTTPException(404,'Conversation unavailable')
    return s,other
@router.post('/api/chat/presence')
def presence(db:Session=Depends(get_db),u=Depends(current_user)):
    if is_admin(u) or u.role not in ('writer','beta'):raise HTTPException(403,'Writer or beta reader required')
    p=db.get(ChatPresence,u.id)
    if not p:p=ChatPresence(user_id=u.id);db.add(p)
    p.seen=time.time();db.commit();return {'ok':True}
@router.get('/api/chat')
def conversations(db:Session=Depends(get_db),u=Depends(current_user)):
    rows=[]
    for i in db.scalars(select(Invitation).where(Invitation.status=='accepted')):
        try:s,other=participants(db,i,u)
        except HTTPException:continue
        p=db.get(ChatPresence,other.id);r=db.get(ChatRead,(i.id,u.id));seen=r.seen if r else 0
        unread=db.scalar(select(func.count()).select_from(ChatMessage).where(ChatMessage.invitation_id==i.id,ChatMessage.sender_id!=u.id,ChatMessage.created>seen))
        rows.append({'id':i.id,'story':s.title,'name':other.name,'online':bool(p and time.time()-p.seen<65),'last_seen':p.seen if p else None,'unread':unread})
    return rows
@router.get('/api/chat/{invitation_id}')
def messages(invitation_id:str,before:float|None=None,db:Session=Depends(get_db),u=Depends(current_user)):
    participants(db,db.get(Invitation,invitation_id),u)
    q=select(ChatMessage).where(ChatMessage.invitation_id==invitation_id)
    if before:q=q.where(ChatMessage.created<before)
    rows=list(db.scalars(q.order_by(ChatMessage.created.desc()).limit(100)))
    return [{'id':m.id,'body':m.body,'mine':m.sender_id==u.id,'created':m.created} for m in reversed(rows)]
@router.post('/api/chat/{invitation_id}/read')
def mark_read(invitation_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    participants(db,db.get(Invitation,invitation_id),u)
    latest=db.scalar(select(func.max(ChatMessage.created)).where(ChatMessage.invitation_id==invitation_id)) or 0
    r=db.get(ChatRead,(invitation_id,u.id))
    if not r:r=ChatRead(invitation_id=invitation_id,user_id=u.id);db.add(r)
    r.seen=latest;db.commit();return {'ok':True}
@router.post('/api/chat/{invitation_id}')
def send(invitation_id:str,data:MessageIn,request:Request,db:Session=Depends(get_db),u=Depends(current_user)):
    from .main import throttle
    throttle(request);participants(db,db.get(Invitation,invitation_id),u)
    if not data.body.strip():raise HTTPException(422,'Message cannot be empty')
    m=ChatMessage(invitation_id=invitation_id,sender_id=u.id,body=data.body.strip());db.add(m);db.commit();return {'id':m.id}
