"""Support-issued recovery links: delivered only to the account mailbox."""
import secrets,time
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import String,Float,ForeignKey,select,update,delete
from sqlalchemy.orm import Mapped,mapped_column,Session
from .db import Base,User,SessionToken,get_db
from .security import digest,password_hash
from .operations import permit,can_case,audit
from .ops_models import Case,GuestCase
from .support_delivery import queue_reply,support_settings

router=APIRouter()
class PasswordRecovery(Base):
    __tablename__='password_recovery'
    token_hash:Mapped[str]=mapped_column(String(64),primary_key=True)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    expires:Mapped[float]=mapped_column(Float)
    used:Mapped[float|None]=mapped_column(Float,nullable=True)

@router.post('/api/admin/ops/cases/{case_id}/password-reset')
def issue_reset(case_id:str,db:Session=Depends(get_db),u=Depends(permit('support'))):
    c=db.get(Case,case_id) or db.get(GuestCase,case_id)
    if not c or not can_case(u,c):raise HTTPException(404,'Case not found')
    config=support_settings()
    if not config:raise HTTPException(503,'Email sending is not configured.')
    email=c.email if isinstance(c,GuestCase) else db.get(User,c.user_id).email
    account=db.scalar(select(User).where(User.email==email))
    if not account:raise HTTPException(422,'No account matches this ticket email. Reply with sign-in or registration guidance instead.')
    recent=db.scalar(select(PasswordRecovery).where(PasswordRecovery.user_id==account.id,PasswordRecovery.expires>time.time()+14*60,PasswordRecovery.used.is_(None)))
    if recent:raise HTTPException(429,'A reset link was just requested. Wait one minute before sending another.')
    token=secrets.token_urlsafe(32)
    db.add(PasswordRecovery(token_hash=digest(token),user_id=account.id,expires=time.time()+15*60))
    link=config['url']+'/reset-password.html#token='+token
    queue_reply(db,c,'Support received a request to reset your KathhaVerse password.\n\nChoose a new password using this one-use link (expires in 15 minutes):\n'+link+'\n\nIf you did not request help, ignore this message. Never share this link or your password. Resetting a password does not remove account restrictions.')
    audit(db,u,'support_password_reset_requested',c.id,'Reset link queued to account email')
    db.commit()
    return {'ok':True,'delivery':'queued'}

class ResetIn(BaseModel):
    token:str=Field(min_length=32,max_length=128)
    password:str=Field(min_length=10,max_length=128)

@router.post('/api/auth/password-reset')
def reset(data:ResetIn,request:Request,db:Session=Depends(get_db)):
    from .main import throttle
    throttle(request)
    row=db.get(PasswordRecovery,digest(data.token))
    if not row or row.used or row.expires<=time.time():raise HTTPException(400,'This reset link is invalid or expired. Contact support for a new link.')
    password=password_hash(data.password)
    claimed=db.execute(update(PasswordRecovery).where(PasswordRecovery.token_hash==row.token_hash,PasswordRecovery.used.is_(None),PasswordRecovery.expires>time.time()).values(used=time.time())).rowcount
    if claimed!=1:db.rollback();raise HTTPException(400,'This reset link has already been used or expired.')
    db.execute(update(User).where(User.id==row.user_id).values(password_hash=password))
    db.execute(delete(SessionToken).where(SessionToken.user_id==row.user_id))
    db.execute(update(PasswordRecovery).where(PasswordRecovery.user_id==row.user_id,PasswordRecovery.used.is_(None)).values(used=time.time()))
    db.commit()
    return {'ok':True}
