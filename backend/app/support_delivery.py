"""Private ticket metadata and durable, content-free email notifications."""
import time, os, smtplib
from email.message import EmailMessage
from sqlalchemy import String, Text, Float, Integer, ForeignKey, select, update
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base,uid,SessionLocal,User,Notification
class CaseDetails(Base):
    __tablename__='support_case_details'
    case_id:Mapped[str]=mapped_column(ForeignKey('support_cases.id'),primary_key=True)
    urgency:Mapped[str]=mapped_column(String(20),default='normal')
    screenshot:Mapped[str]=mapped_column(Text,default='')
class SupportMail(Base):
    __tablename__='support_mail'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    recipient:Mapped[str]=mapped_column(String(254))
    case_id:Mapped[str]=mapped_column(String(36))
    category:Mapped[str]=mapped_column(String(30))
    urgency:Mapped[str]=mapped_column(String(20))
    status:Mapped[str]=mapped_column(String(20),default='pending')
    attempts:Mapped[int]=mapped_column(Integer,default=0)
    next_attempt:Mapped[float]=mapped_column(Float,default=0)
    event:Mapped[str]=mapped_column(String(60))

def enqueue(db,c,actor,event):
    from .operations import can_case,staff_role
    details=db.get(CaseDetails,c.id)
    recipients=[db.get(User,c.user_id)] if actor.id!=c.user_id else [u for u in db.scalars(select(User)) if staff_role(u) and can_case(u,c) and u.id!=actor.id]
    for user in recipients:
        if actor.id==c.user_id:db.add(Notification(sender_id=actor.id,user_id=user.id,title='Support request updated',body='Open Platform operations → Cases to review ticket '+c.id))
        db.add(SupportMail(recipient=user.email,case_id=c.id,category=c.category,urgency=details.urgency if details else 'normal',event=event))

def message(item,config):
    msg=EmailMessage();msg['From']=config['sender'];msg['To']=item.recipient
    msg['Subject']='Kathha Verse support · '+item.case_id
    if config.get('reply_to'):msg['Reply-To']=config['reply_to']
    msg.set_content(f'{item.event}\n\nTicket: {item.case_id}\nCategory: {item.category}\nUrgency: {item.urgency}\n\nSign in to read and reply securely:\n{config["url"].rstrip("/")}/?support_case={item.case_id}\n\nPrivate messages and attachments are available only after signing in. This notification contains no manuscript or companion conversation.')
    return msg

def process_one():
    from .welcome_email import settings,deliver
    config=settings()
    if not config:return False
    with SessionLocal() as db:
        db.execute(update(SupportMail).where(SupportMail.status=='sending',SupportMail.next_attempt<time.time()-600).values(status='uncertain'))
        row=db.scalar(select(SupportMail).where(SupportMail.status=='pending',SupportMail.next_attempt<=time.time()).order_by(SupportMail.next_attempt).limit(1))
        if not row:db.commit();return False
        claimed=db.execute(update(SupportMail).where(SupportMail.id==row.id,SupportMail.status=='pending').values(status='sending',attempts=row.attempts+1,next_attempt=time.time())).rowcount
        db.commit()
        if not claimed:return False
        db.refresh(row);item_id=row.id;msg=message(row,config)
    try:deliver(msg,config)
    except Exception as error:
        with SessionLocal() as db:
            row=db.get(SupportMail,item_id)
            uncertain=isinstance(error,smtplib.SMTPServerDisconnected) or (isinstance(error,OSError) and not isinstance(error,smtplib.SMTPException))
            row.status='uncertain' if uncertain else ('failed' if row.attempts>=5 else 'pending');row.next_attempt=time.time()+min(3600,60*2**row.attempts);db.commit()
    else:
        with SessionLocal() as db:db.execute(update(SupportMail).where(SupportMail.id==item_id).values(status='sent'));db.commit()
    return True
