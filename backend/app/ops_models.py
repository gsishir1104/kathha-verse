"""Platform operations metadata and participant-submitted support evidence."""
import time
from sqlalchemy import String,Text,Float,ForeignKey,JSON
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base,uid
class Case(Base):
    __tablename__='support_cases'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    category:Mapped[str]=mapped_column(String(30))
    subject:Mapped[str]=mapped_column(String(160))
    status:Mapped[str]=mapped_column(String(30),default='open')
    assigned_to:Mapped[str|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    created:Mapped[float]=mapped_column(Float,default=time.time)
    updated:Mapped[float]=mapped_column(Float,default=time.time)
class CaseReply(Base):
    __tablename__='case_replies'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    case_id:Mapped[str]=mapped_column(ForeignKey('support_cases.id'))
    author_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    body:Mapped[str]=mapped_column(Text)
    created:Mapped[float]=mapped_column(Float,default=time.time)
class OperationEvent(Base):
    __tablename__='operation_events'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    actor_id:Mapped[str|None]=mapped_column(ForeignKey('users.id'),nullable=True)
    action:Mapped[str]=mapped_column(String(120))
    target:Mapped[str]=mapped_column(String(160),default='')
    reason:Mapped[str]=mapped_column(Text,default='')
    result:Mapped[str]=mapped_column(String(30),default='success')
    created:Mapped[float]=mapped_column(Float,default=time.time,index=True)
class OperationSetting(Base):
    __tablename__='operation_settings'
    key:Mapped[str]=mapped_column(String(50),primary_key=True)
    value:Mapped[dict]=mapped_column(JSON,default=dict)
class AIJob(Base):
    __tablename__='ai_jobs'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    feature:Mapped[str]=mapped_column(String(100))
    model:Mapped[str]=mapped_column(String(100))
    status:Mapped[str]=mapped_column(String(20),default='running')
    started:Mapped[float]=mapped_column(Float,default=time.time)
    ended:Mapped[float|None]=mapped_column(Float,nullable=True)
    input_tokens:Mapped[int|None]=mapped_column(nullable=True)
    output_tokens:Mapped[int|None]=mapped_column(nullable=True)

class GuestCase(Base):
    __tablename__='guest_support_cases'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    token_hash:Mapped[str]=mapped_column(String(64))
    email:Mapped[str]=mapped_column(String(254))
    subject:Mapped[str]=mapped_column(String(160))
    category:Mapped[str]=mapped_column(String(30),default='access')
    status:Mapped[str]=mapped_column(String(30),default='open')
    created:Mapped[float]=mapped_column(Float,default=time.time)
    updated:Mapped[float]=mapped_column(Float,default=time.time)
    messages:Mapped[list]=mapped_column(JSON,default=list)
    @property
    def user_id(self):return None
    @property
    def assigned_to(self):return None
