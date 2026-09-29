import os
import uuid
import time
from sqlalchemy import create_engine, String, Text, Integer, Float, ForeignKey, JSON, UniqueConstraint, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def normalize_database_url(value):
    # Managed hosts commonly provide a generic PostgreSQL URL. Select the
    # installed psycopg v3 driver explicitly without changing credentials.
    if value.startswith('postgres://'):
        return 'postgresql+psycopg://' + value.removeprefix('postgres://')
    if value.startswith('postgresql://'):
        return 'postgresql+psycopg://' + value.removeprefix('postgresql://')
    return value

DATABASE_URL = normalize_database_url(os.getenv('DATABASE_URL', 'sqlite:///./storylens.db'))
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_setup(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=10000')
SessionLocal = sessionmaker(engine, expire_on_commit=False)
def uid(): return str(uuid.uuid4())
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
class SessionToken(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    expires: Mapped[float] = mapped_column(Float)
class Story(Base):
    __tablename__ = 'stories'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    writer_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default='')
    genre: Mapped[str] = mapped_column(String(80), default='Fiction')
class Chapter(Base):
    __tablename__ = 'chapters'
    __table_args__ = (UniqueConstraint('story_id', 'position'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    story_id: Mapped[str] = mapped_column(ForeignKey('stories.id'))
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default='')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    intent: Mapped[dict] = mapped_column(JSON, default=dict)
    state: Mapped[str] = mapped_column(String(20), default='draft')
class Snapshot(Base):
    __tablename__ = 'snapshots'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    chapter_id: Mapped[str] = mapped_column(ForeignKey('chapters.id'))
    revision: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    universe: Mapped[dict] = mapped_column(JSON)
    intent: Mapped[dict] = mapped_column(JSON)
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created: Mapped[float] = mapped_column(Float, default=time.time)
class Invitation(Base):
    __tablename__ = 'invitations'
    __table_args__ = (UniqueConstraint('story_id', 'email'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    story_id: Mapped[str] = mapped_column(ForeignKey('stories.id'))
    email: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(20), default='pending')
class Release(Base):
    __tablename__ = 'releases'
    __table_args__ = (UniqueConstraint('chapter_id', 'reader_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    chapter_id: Mapped[str] = mapped_column(ForeignKey('chapters.id'))
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('snapshots.id'))
    reader_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    active: Mapped[int] = mapped_column(Integer, default=1)
    progress: Mapped[int] = mapped_column(Integer, default=0)
class Question(Base):
    __tablename__ = 'questions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    release_id: Mapped[str] = mapped_column(ForeignKey('releases.id'))
    text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(30))
class Answer(Base):
    __tablename__ = 'answers'
    __table_args__ = (UniqueConstraint('question_id', 'reader_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    question_id: Mapped[str] = mapped_column(ForeignKey('questions.id'))
    release_id: Mapped[str] = mapped_column(ForeignKey('releases.id'))
    reader_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[int] = mapped_column(Integer)
    emotion: Mapped[str] = mapped_column(String(40), default='')
    tension: Mapped[int] = mapped_column(Integer, default=50)
    created: Mapped[float] = mapped_column(Float, default=time.time)
class Feedback(Base):
    __tablename__ = 'feedback'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    release_id: Mapped[str] = mapped_column(ForeignKey('releases.id'))
    reader_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int] = mapped_column(Integer)
    quote: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)
class Audit(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[str] = mapped_column(String(36))
    created: Mapped[float] = mapped_column(Float, default=time.time)
def get_db():
    with SessionLocal() as db:
        yield db


class ChapterHistory(Base):
    __tablename__ = 'chapter_history'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    chapter_id: Mapped[str] = mapped_column(ForeignKey('chapters.id'))
    revision: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[dict] = mapped_column(JSON)
    created: Mapped[float] = mapped_column(Float, default=time.time)

class GraphComment(Base):
    __tablename__ = 'graph_comments'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey('snapshots.id'))
    release_id: Mapped[str] = mapped_column(ForeignKey('releases.id'))
    reader_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    entity_id: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(100), default='')
    category: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)

class FeedbackState(Base):
    __tablename__ = 'feedback_states'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default='new')

class AccountControl(Base):
    __tablename__ = 'account_controls'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    suspended: Mapped[int] = mapped_column(Integer, default=0)

class AdminEvent(Base):
    __tablename__ = 'admin_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    resource_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)

class UserPresence(Base):
    __tablename__ = 'user_presence'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    first_seen: Mapped[float] = mapped_column(Float, default=time.time)
    last_active: Mapped[float] = mapped_column(Float, default=time.time)
    last_login: Mapped[float | None] = mapped_column(Float, nullable=True)
class UserActivity(Base):
    __tablename__ = 'user_activity'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    action: Mapped[str] = mapped_column(String(100))
    resource: Mapped[str] = mapped_column(String(100), default='')
    created: Mapped[float] = mapped_column(Float, default=time.time, index=True)

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    sender_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)
    read_at: Mapped[float | None] = mapped_column(Float, nullable=True)
