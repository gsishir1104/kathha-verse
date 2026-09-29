from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

Role = Literal['writer', 'beta', 'reader']
Kind = Literal['character','relationship','event','location','object','secret','clue','reveal','plot_thread','mystery']
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Auth(Strict):
    email: str = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)
    @field_validator('email')
    @classmethod
    def email_check(cls, v):
        v = v.strip().lower()
        if '@' not in v or '.' not in v.split('@')[-1] or ' ' in v: raise ValueError('Enter a valid email')
        return v
class Signup(Auth):
    name: str = Field(min_length=1, max_length=100)
    role: Role
class StoryIn(Strict):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=4000)
    genre: str = Field(default='Fiction', max_length=80)
class IntentTarget(Strict):
    metric: Literal['trust','suspicion','clue','confusion','prediction','mystery_difficulty']
    target: str = Field(min_length=1,max_length=200)
    expected: int = Field(ge=0,le=100)
    reveal_chapter: int | None = Field(default=None,ge=1)
    notes: str = Field(default='',max_length=1000)

class SceneIntent(Strict):
    label: str = Field(max_length=200)
    evidence: str = Field(max_length=3000)
    reaction: str = Field(max_length=1500)

class Intent(Strict):
    emotion: str = Field(default='Curiosity', max_length=40)
    tension: int | None = Field(default=65, ge=0, le=100)
    prediction_target: str = Field(default='', max_length=500)
    desired_predictability: int | None = Field(default=25, ge=0, le=100)
    notes: str = Field(default='', max_length=4000)
    targets: list[IntentTarget] = Field(default_factory=list,max_length=30)
    scenes: list[SceneIntent] = Field(default_factory=list,max_length=30)
class ChapterIn(Strict):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default='', max_length=120000)
    revision: int = Field(default=1, ge=1)
    intent: Intent = Field(default_factory=Intent)
class Knowledge(Strict):
    text: str = Field(max_length=2000)
    state: Literal['knows','does_not_know','believes','feels']
    reader_safe: bool
    evidence: str = Field(max_length=3000)
    subject_id: str = Field(default='',max_length=100)
    secret_id: str = Field(default='',max_length=100)
    truth: Literal['unknown','true','false'] = 'unknown'
class CharacterPoint(Strict):
    text: str = Field(max_length=1000)
    evidence: str = Field(max_length=3000)
    reader_safe: bool = False
class Relation(Strict):
    target_id: str
    label: str = Field(min_length=1,max_length=100)
    strength: int = Field(default=50,ge=0,le=100)
    evidence: str = Field(max_length=3000)
class Entity(Strict):
    id: str = Field(min_length=1, max_length=100)
    kind: Kind
    name: str = Field(min_length=1, max_length=200)
    summary: str = Field(max_length=4000)
    evidence: str = Field(max_length=3000)
    confidence: float = Field(ge=0, le=1)
    reader_safe: bool
    status: Literal['pending','confirmed','rejected']
    links: list[str] = Field(max_length=30)
    knowledge: list[Knowledge] = Field(max_length=50)
    relations: list[Relation] = Field(default_factory=list,max_length=30)
    goals: list[CharacterPoint] = Field(default_factory=list,max_length=20)
    conflicts: list[CharacterPoint] = Field(default_factory=list,max_length=20)
    timeline_order: int | None = None
    story_time: str = Field(default='',max_length=150)
    thread_status: Literal['open','resolved','unknown'] = 'unknown'
    character_status: str = Field(default='',max_length=100)
    certainty: Literal['uncertain','inferred','explicit'] = 'uncertain'
    uncertainty_reason: str = Field(default='',max_length=500)
class PromptQuestion(Strict):
    review_status: Literal['pending','approved','rejected'] = 'approved'
    text: str = Field(min_length=5, max_length=1000)
    category: Literal['prediction','trust','emotion','clue','confusion','suspicion','reasoning']
    evidence: str = Field(max_length=3000)
    options: list[str] = Field(default_factory=list, max_length=6)
    timing: Literal['after_chapter','before_reveal','after_clue'] = 'after_chapter'
    checkpoint: int | None = Field(default=None,ge=0)
    target: str = Field(default='',max_length=200)
class Universe(Strict):
    question_frequency: Literal['each_chapter','key_moments','major_reveals'] = 'each_chapter'
    entities: list[Entity] = Field(max_length=150)
    questions: list[PromptQuestion] = Field(max_length=8)
class Verification(Strict):
    revision: int
    universe: Universe
    confirm_reader_safety: bool
class InviteIn(Strict):
    email: str = Field(max_length=254)
class ReleaseIn(Strict):
    snapshot_id: str
    reader_ids: list[str] = Field(min_length=1, max_length=100)
class AnswerIn(Strict):
    text: str = Field(min_length=1, max_length=4000)
    confidence: int = Field(ge=0, le=100)
    emotion: str = Field(default='', max_length=40)
    tension: int = Field(default=50, ge=0, le=100)
class FeedbackIn(Strict):
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    quote: str = Field(max_length=120000)
    category: Literal['positive','plot','character','dialogue','pacing','worldbuilding','confusion']
    text: str = Field(min_length=1, max_length=4000)


class GraphCommentIn(Strict):
    snapshot_id: str
    entity_id: str
    target_id: str = ''
    category: Literal['positive','plot','character','pacing','worldbuilding','confusion']
    text: str = Field(min_length=1,max_length=4000)

class FeedbackStateIn(Strict):
    status: Literal['new','reviewed','addressed']

class RestoreIn(Strict):
    revision: int = Field(ge=1)
