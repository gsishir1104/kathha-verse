from sqlalchemy import String, Text, Integer, Float, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base,uid
import time

class StoryDetails(Base):
    __tablename__='story_details'
    story_id:Mapped[str]=mapped_column(ForeignKey('stories.id'),primary_key=True)
    data:Mapped[dict]=mapped_column(JSON,default=dict)

class BetaProfile(Base):
    __tablename__='beta_profiles'
    user_id:Mapped[str]=mapped_column(ForeignKey('users.id'),primary_key=True)
    data:Mapped[dict]=mapped_column(JSON,default=dict)

class ReadingPosition(Base):
    __tablename__='reading_positions'
    release_id:Mapped[str]=mapped_column(ForeignKey('releases.id'),primary_key=True)
    offset:Mapped[int]=mapped_column(Integer,default=0)

class ReaderObservation(Base):
    __tablename__='reader_observations'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    release_id:Mapped[str]=mapped_column(ForeignKey('releases.id'))
    snapshot_id:Mapped[str]=mapped_column(ForeignKey('snapshots.id'))
    reader_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    kind:Mapped[str]=mapped_column(String(30))
    target:Mapped[str]=mapped_column(String(200))
    value:Mapped[int]=mapped_column(Integer)
    confidence:Mapped[int]=mapped_column(Integer)
    explanation:Mapped[str]=mapped_column(Text)
    evidence:Mapped[str]=mapped_column(Text,default='')
    created:Mapped[float]=mapped_column(Float,default=time.time)

class OverallFeedback(Base):
    __tablename__='overall_feedback'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    story_id:Mapped[str]=mapped_column(ForeignKey('stories.id'))
    reader_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    release_id:Mapped[str|None]=mapped_column(ForeignKey('releases.id'),nullable=True)
    scope:Mapped[str]=mapped_column(String(20))
    text:Mapped[str]=mapped_column(Text)
    created:Mapped[float]=mapped_column(Float,default=time.time)

class HelpfulRating(Base):
    __tablename__='helpful_ratings'
    key:Mapped[str]=mapped_column(String(100),primary_key=True)
    writer_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    reader_id:Mapped[str]=mapped_column(ForeignKey('users.id'))
    rating:Mapped[int]=mapped_column(Integer)

class QuestionPlacement(Base):
    __tablename__='question_placements'
    question_id:Mapped[str]=mapped_column(ForeignKey('questions.id'),primary_key=True)
    data:Mapped[dict]=mapped_column(JSON)

class WritingEntry(Base):
    __tablename__='writing_entries'
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    story_id:Mapped[str]=mapped_column(ForeignKey('stories.id'))
    chapter_id:Mapped[str]=mapped_column(ForeignKey('chapters.id'))
    word_count:Mapped[int]=mapped_column(Integer)
    delta:Mapped[int]=mapped_column(Integer)
    created:Mapped[float]=mapped_column(Float,default=time.time)
