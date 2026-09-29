from typing import Literal
from pydantic import Field,field_validator
from .schemas import Strict

class StorySettings(Strict):
    title:str=Field(min_length=1,max_length=200)
    description:str=Field(default='',max_length=4000)
    genre:str=Field(default='Fiction',max_length=80)
    status:Literal['draft','beta_testing','revision','ready_to_publish']='draft'
    tags:list[str]=Field(default_factory=list,max_length=20)
    content_notes:str=Field(default='',max_length=2000)
    cover:str=Field(default='',max_length=1500000)
    word_goal:int=Field(default=50000,ge=0,le=10000000)
    daily_goal:int=Field(default=500,ge=0,le=100000)
    @field_validator('cover')
    @classmethod
    def image_only(cls,v):
        if v and not v.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):raise ValueError('Use a PNG, JPEG, or WebP cover')
        return v
    @field_validator('tags')
    @classmethod
    def clean_tags(cls,v):return list(dict.fromkeys(x.strip()[:60] for x in v if x.strip()))

class ProfileIn(Strict):
    bio:str=Field(default='',max_length=2000)
    genres:list[str]=Field(default_factory=list,max_length=20)
    specialties:list[str]=Field(default_factory=list,max_length=20)
    availability:Literal['available','limited','unavailable']='available'
    listed:bool=False

class ImportIn(Strict):
    filename:str=Field(max_length=200)
    data:str=Field(max_length=6000000)

class PositionIn(Strict):
    snapshot_id:str
    offset:int=Field(ge=0)

class ObservationIn(Strict):
    snapshot_id:str
    kind:Literal['prediction','belief','suspicion','trust','clue','confusion','emotion','mystery_difficulty']
    target:str=Field(min_length=1,max_length=200)
    value:int=Field(ge=0,le=100)
    confidence:int=Field(ge=0,le=100)
    explanation:str=Field(min_length=1,max_length=4000)
    evidence:str=Field(default='',max_length=3000)

class OverallIn(Strict):
    scope:Literal['chapter','manuscript']
    text:str=Field(min_length=1,max_length=12000)

class RatingIn(Strict):
    rating:int=Field(ge=1,le=5)

class MergeIn(Strict):
    keep_id:str
    remove_id:str

class QuestionGenerationIn(Strict):
    revision:int

class FollowupIn(Strict):
    another:bool=False
