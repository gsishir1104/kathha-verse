import os, time, secrets, threading
from copy import deepcopy
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal, User, SessionToken, Story, Chapter, Snapshot, Invitation, Release, Question, Answer, Feedback, Audit, ChapterHistory, GraphComment, FeedbackState
from .schemas import Signup, Auth, StoryIn, ChapterIn, IntentUpdate, Verification, InviteIn, ReleaseIn, AnswerIn, FeedbackIn, Universe, GraphCommentIn, FeedbackStateIn, RestoreIn
from .security import current_user, writer, user_dict, start_session, password_hash, password_ok, digest, DEMO_MODE, PRODUCTION
from .analysis import extract, validate_universe, reader_projection, dynamic_questions
from .sample import SAMPLE_CONTENT, SAMPLE_TITLE
from . import local_ai
from . import studio_models
from .welcome_email import WelcomeEmail, start_worker
from .google_login import router as google_router

ORIGINS = [origin.strip().rstrip('/') for origin in os.getenv(
    'FRONTEND_ORIGINS',
    'http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:8000,http://localhost:8000',
).split(',') if origin.strip()]
public_app_url = os.getenv('PUBLIC_APP_URL', '').strip().rstrip('/')
if public_app_url and public_app_url not in ORIGINS:
    ORIGINS.append(public_app_url)
if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    render_origin = 'https://'+os.environ['RENDER_EXTERNAL_HOSTNAME']
    if render_origin not in ORIGINS:
        ORIGINS.append(render_origin)
if PRODUCTION and engine.dialect.name!='postgresql':
    raise RuntimeError('Production requires an explicit PostgreSQL DATABASE_URL')

def restore_equivalent_story_universes(db:Session):
    restored=0
    for chapter in db.scalars(select(Chapter)):
        current=db.scalar(select(Snapshot.id).where(Snapshot.chapter_id==chapter.id,Snapshot.revision==chapter.revision).limit(1))
        if current: continue
        previous=db.scalar(select(Snapshot).where(Snapshot.chapter_id==chapter.id).order_by(Snapshot.revision.desc(),Snapshot.created.desc()).limit(1))
        if not previous or previous.title!=chapter.title or previous.content!=chapter.content: continue
        db.add(Snapshot(chapter_id=chapter.id,revision=chapter.revision,title=chapter.title,content=chapter.content,intent=deepcopy(chapter.intent),universe=deepcopy(previous.universe),mode=previous.mode,status='pending'))
        chapter.state='review';restored+=1
    return restored

@asynccontextmanager
async def lifespan(app):
    from .backups import backup_database
    backup_database(force=True)
    Base.metadata.create_all(engine)
    # Pending AI interpretations remain editable, so safely repair explicit
    # "the stranger is named ..." aliases produced by older deployments.
    with SessionLocal() as db:
        changed=False
        for snapshot in db.scalars(select(Snapshot).where(Snapshot.status=='pending')):
            repaired=local_ai.consolidate_explicit_identity_reveals(snapshot.universe,snapshot.content)
            if repaired!=snapshot.universe:
                snapshot.universe=repaired;changed=True
        if restore_equivalent_story_universes(db):changed=True
        if changed:db.commit()
    if DEMO_MODE:
        with SessionLocal() as db:
            if not db.scalar(select(User).where(User.email=='writer@storylens.test')):
                w = User(name='Alex Morgan',email='writer@storylens.test',role='writer',password_hash=password_hash(secrets.token_urlsafe(24)))
                b = User(name='Jamie Chen',email='beta@storylens.test',role='beta',password_hash=password_hash(secrets.token_urlsafe(24)))
                r = User(name='Sam Rivera',email='reader@storylens.test',role='reader',password_hash=password_hash(secrets.token_urlsafe(24)))
                db.add_all([w,b,r]); db.flush()
                s = Story(writer_id=w.id,title=SAMPLE_TITLE,description='A missing brother. A lighthouse that should never have lit again.',genre='Mystery')
                db.add(s); db.flush()
                db.add(Chapter(story_id=s.id,position=1,title='A light across the water',content=SAMPLE_CONTENT,intent={'emotion':'Curiosity','tension':65,'prediction_target':'Elias is alive','desired_predictability':25,'notes':'Let hope interrupt MaraÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢s suspicion. Keep Theo ambiguous.'}))
                db.commit()
    mail_stop, mail_thread = start_worker()
    try:
        yield
    finally:
        mail_stop.set()
        if mail_thread: mail_thread.join(timeout=1)

app = FastAPI(title='Kathha Verse API',version='0.1.0',lifespan=lifespan)
app.include_router(google_router)
from .admin import router as admin_router
app.include_router(admin_router)
from .operations import router as operations_router
app.include_router(operations_router)
from .chat import router as chat_router
app.include_router(chat_router)
from .companion import router as companion_router
app.include_router(companion_router)
from .product import router as product_router
app.include_router(product_router)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type'])
@app.middleware('http')
async def boundaries(request, call_next):
    if request.method in {'POST','PUT','DELETE','PATCH'}:
        origin = request.headers.get('origin')
        if origin and origin not in ORIGINS:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Untrusted origin'},status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Cross-site mutations are not allowed'},status_code=403)
    if request.method in {'POST','PUT','DELETE','PATCH'} and request.url.path.startswith('/api'):
        from .backups import backup_database
        from starlette.concurrency import run_in_threadpool
        await run_in_threadpool(backup_database)
    response = await call_next(request)
    failed_invitation=response.status_code>=400 and '/invitations' in request.url.path
    denied_read=response.status_code==404 and request.url.path.startswith('/api/read/')
    unsafe_question=response.status_code==422 and request.url.path.startswith('/api/snapshots/')
    if response.status_code in (401,403,429) or response.status_code>=500 or denied_read or unsafe_question or failed_invitation:
        from .ops_models import OperationEvent
        with SessionLocal() as security_db:
            security_db.add(OperationEvent(actor_id=getattr(request.state,'activity_user_id',None),action='invitation_action_failed' if failed_invitation else ('story_safety_validation_failed' if unsafe_question else ('request_denied' if response.status_code<500 else 'request_failed')),target=getattr(request.scope.get('route'),'path','unknown'),result=str(response.status_code)))
            security_db.commit()
    actor=getattr(request.state,'activity_user_id',None)
    if actor and 200 <= response.status_code < 300 and not (request.method=='GET' and request.url.path=='/api/notifications'):
        from .activity import record
        from starlette.concurrency import run_in_threadpool
        route=getattr(request.scope.get('route'),'path','')
        try:
            await run_in_threadpool(record,actor,request.method,route,request.path_params)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Could not record account activity')
    if request.url.path.startswith('/api') or not request.url.path.startswith('/_next/static/'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['X-Frame-Options']='DENY'
    return response

attempts = defaultdict(list)
attempt_lock = threading.Lock()
def throttle(request):
    key = request.client.host if request.client else 'unknown'
    now = time.time()
    with attempt_lock:
        attempts[key] = [x for x in attempts[key] if now-x < 300]
        if len(attempts[key])>=30: raise HTTPException(429,'Too many attempts; try again in five minutes')
        attempts[key].append(now)

def owned_story(db, story_id, user):
    story = db.get(Story,story_id)
    if not story or story.writer_id != user.id: raise HTTPException(404,'Story not found')
    return story
def owned_chapter(db, chapter_id, user, lock=False):
    q = select(Chapter).where(Chapter.id==chapter_id)
    if lock: q = q.with_for_update()
    c = db.scalar(q)
    if not c: raise HTTPException(404,'Chapter not found')
    owned_story(db,c.story_id,user)
    return c
def release_for(db, release_id, user):
    r = db.get(Release,release_id)
    if not r or r.reader_id != user.id or not r.active: raise HTTPException(404,'Released chapter not found')
    c = db.get(Chapter,r.chapter_id)
    inv = db.scalar(select(Invitation).where(Invitation.story_id==c.story_id, Invitation.email==user.email,Invitation.status=='accepted'))
    if not inv: raise HTTPException(404,'Released chapter not found')
    return r
def latest_snapshot(db,c):
    return db.scalar(select(Snapshot).where(Snapshot.chapter_id==c.id, Snapshot.revision==c.revision).order_by(Snapshot.created.desc()))
def snapshot_dict(s):
    return {'id':s.id,'revision':s.revision,'status':s.status,'mode':s.mode,'universe':s.universe,'created':s.created} if s else None
def chapter_dict(c):
    return {k:getattr(c,k) for k in ['id','story_id','position','title','content','revision','intent','state']}
def audit(db,u,action,id): db.add(Audit(actor_id=u.id,action=action,resource_id=id))

@app.get('/api/health')
def health(): return {'ok':True,'demo_mode':DEMO_MODE,'ai_connected':local_ai.availability(),'ai_provider':'local' if local_ai.enabled() else local_ai.provider(),'ai_model':local_ai.active_model(),'ai_max_chars':local_ai.MAX_CHARS,'ai_daily_limit':local_ai.DAILY_LIMIT,'database':'sqlite-local' if engine.dialect.name=='sqlite' else 'postgresql'}
@app.post('/api/auth/register')
def register(data:Signup, request:Request,response:Response,db:Session=Depends(get_db)):
    throttle(request)
    u=User(email=data.email,name=data.name.strip(),role=data.role,password_hash=password_hash(data.password))
    db.add(u)
    try:
        db.flush()
        db.add(WelcomeEmail(user_id=u.id))
        db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,'An account already uses this email')
    start_session(db,u,response); return user_dict(u)
@app.post('/api/auth/login')
def login(data:Auth,request:Request,response:Response,db:Session=Depends(get_db)):
    throttle(request)
    u=db.scalar(select(User).where(User.email==data.email))
    if not u or not password_ok(data.password,u.password_hash): raise HTTPException(401,'Email or password is incorrect')
    start_session(db,u,response); return user_dict(u)
@app.post('/api/auth/demo/{role}')
def demo_login(role:str,response:Response,db:Session=Depends(get_db)):
    if not DEMO_MODE or role not in ['writer','beta','reader']: raise HTTPException(404)
    u=db.scalar(select(User).where(User.email==f'{role}@storylens.test'))
    start_session(db,u,response); return user_dict(u)
@app.get('/api/auth/me')
def me(u=Depends(current_user)): return user_dict(u)
@app.post('/api/auth/logout')
def logout(request:Request,response:Response,db:Session=Depends(get_db)):
    token=db.get(SessionToken,digest(request.cookies.get('storylens_session','')))
    if token:
        request.state.activity_user_id=token.user_id
        db.delete(token); db.commit()
    response.delete_cookie('storylens_session',path='/'); return {'ok':True}
@app.put('/api/preferences')
def preferences(data:dict,db:Session=Depends(get_db),u=Depends(current_user)):
    if type(data.get('interactive_reading')) is not bool or len(data)!=1: raise HTTPException(422,'Expected interactive_reading boolean')
    u.preferences={'interactive_reading':data['interactive_reading']}; db.commit(); return user_dict(u)

@app.get('/api/notifications')
def notifications(page:int=1,db:Session=Depends(get_db),u=Depends(current_user)):
    from .db import Notification
    if page<1: raise HTTPException(422,'Invalid page')
    query=select(Notification).where(Notification.user_id==u.id)
    return {'unread':db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id==u.id,Notification.read_at.is_(None))),'total':db.scalar(select(func.count()).select_from(query.subquery())),'items':[{'id':n.id,'title':n.title,'body':n.body,'created':n.created,'read_at':n.read_at} for n in db.scalars(query.order_by(Notification.created.desc(),Notification.id).offset((page-1)*20).limit(20))]}
@app.post('/api/notifications/{notice_id}/read')
def read_notification(notice_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    from .db import Notification
    n=db.get(Notification,notice_id)
    if not n or n.user_id!=u.id: raise HTTPException(404,'Notification not found')
    if not n.read_at: n.read_at=time.time();db.commit()
    return {'ok':True}

@app.get('/api/stories')
def stories(db:Session=Depends(get_db),u=Depends(writer)):
    result=[]
    for s in db.scalars(select(Story).where(Story.writer_id==u.id)):
        chapters=list(db.scalars(select(Chapter).where(Chapter.story_id==s.id).order_by(Chapter.position)))
        result.append({'id':s.id,'title':s.title,'description':s.description,'genre':s.genre,'settings':(db.get(studio_models.StoryDetails,s.id).data if db.get(studio_models.StoryDetails,s.id) else {}),'chapters':[chapter_dict(c) for c in chapters]})
    return result
@app.post('/api/stories')
def create_story(data:StoryIn,db:Session=Depends(get_db),u=Depends(writer)):
    s=Story(writer_id=u.id,**data.model_dump()); db.add(s);db.flush()
    c=Chapter(story_id=s.id,position=1,title='Chapter one',content='',intent={});db.add(c);db.commit()
    return {'id':s.id}
@app.post('/api/stories/{story_id}/chapters')
def create_chapter(story_id:str,data:ChapterIn,db:Session=Depends(get_db),u=Depends(writer)):
    owned_story(db,story_id,u)
    db.scalar(select(Story).where(Story.id==story_id).with_for_update())
    position=(db.scalar(select(func.max(Chapter.position)).where(Chapter.story_id==story_id)) or 0)+1
    c=Chapter(story_id=story_id,position=position,title=data.title,content=data.content,intent=data.intent.model_dump());db.add(c);db.commit();return chapter_dict(c)
@app.get('/api/chapters/{chapter_id}')
def get_chapter(chapter_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u);return {**chapter_dict(c),'snapshot':snapshot_dict(latest_snapshot(db,c))}
@app.put('/api/chapters/{chapter_id}')
def save_chapter(chapter_id:str,data:ChapterIn,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u)
    if any(scene.evidence and scene.evidence not in data.content for scene in data.intent.scenes):raise HTTPException(422,'Scene intent evidence must match the saved manuscript')
    db.add(ChapterHistory(chapter_id=c.id,revision=c.revision,title=c.title,content=c.content,intent=c.intent))
    db.add(studio_models.WritingEntry(story_id=c.story_id,chapter_id=c.id,word_count=len(data.content.split()),delta=len(data.content.split())-len(c.content.split())))
    result=db.execute(update(Chapter).where(Chapter.id==c.id,Chapter.revision==data.revision).values(title=data.title,content=data.content,intent=data.intent.model_dump(),revision=data.revision+1,state='draft'))
    if result.rowcount != 1: db.rollback();raise HTTPException(409,'This chapter changed in another tab. Reload before saving.')
    audit(db,u,'chapter_saved',c.id);db.commit();db.refresh(c);return chapter_dict(c)
@app.put('/api/chapters/{chapter_id}/intent')
def save_chapter_intent(chapter_id:str,data:IntentUpdate,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u,lock=True)
    if c.revision!=data.revision: raise HTTPException(409,'This chapter changed in another tab. Reload before saving intent.')
    if any(scene.evidence and scene.evidence not in c.content for scene in data.intent.scenes):raise HTTPException(422,'Scene intent evidence must match the saved manuscript')
    intent=data.intent.model_dump()
    c.intent=intent
    current=latest_snapshot(db,c)
    if current and current.status=='pending': current.intent=intent
    audit(db,u,'chapter_intent_saved',c.id);db.commit();db.refresh(c)
    return {**chapter_dict(c),'snapshot':snapshot_dict(latest_snapshot(db,c))}
@app.post('/api/chapters/{chapter_id}/analyze')
def analyze_chapter(chapter_id:str,detailed:bool=False,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u)
    if not c.content.strip(): raise HTTPException(422,'Write a chapter first')
    revision,content,title,intent=c.revision,c.content,c.title,c.intent
    db.commit() # Do not hold a database transaction during a model request.
    if not (DEMO_MODE and content==SAMPLE_CONTENT):
        with local_ai.allowance(u.id,'analysis'):
            universe,mode=local_ai.extract_detailed(content) if detailed else extract(content)
            from .graph_connections import enrich_graph
            universe=enrich_graph(universe,content)
    else: universe,mode=extract(content)
    db.refresh(c)
    if c.revision!=revision: raise HTTPException(409,'The manuscript changed during analysis. Analyze the saved version again.')
    s=Snapshot(chapter_id=c.id,revision=revision,title=title,content=content,intent=intent,universe=universe,mode=mode)
    changed=db.execute(update(Chapter).where(Chapter.id==c.id,Chapter.revision==revision).values(state='review'))
    if changed.rowcount!=1: db.rollback();raise HTTPException(409,'The manuscript changed during analysis. Analyze the saved version again.')
    db.add(s);db.flush();audit(db,u,'analysis_created',s.id);db.commit();return snapshot_dict(s)
@app.post('/api/chapters/{chapter_id}/suggest-intent')
def suggest_chapter_intent(chapter_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u)
    revision, content = c.revision, c.content
    if not content.strip(): raise HTTPException(422,'Write and save a chapter first.')
    db.commit()
    with local_ai.allowance(u.id,'intent'):
        suggestion=local_ai.suggest_intent(content)
        db.refresh(c)
        if c.revision != revision: raise HTTPException(409,'The chapter changed while AI was working. Try again on the saved version.')
    return {'intent':suggestion,'revision':revision}

@app.post('/api/chapters/{chapter_id}/manual')
def manual_snapshot(chapter_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u)
    if not c.content.strip(): raise HTTPException(422,'Write a chapter first')
    s=Snapshot(chapter_id=c.id,revision=c.revision,title=c.title,content=c.content,intent=c.intent,universe={'entities':[],'questions':[]},mode='manual')
    c.state='review';db.add(s);db.commit();return snapshot_dict(s)
@app.put('/api/snapshots/{snapshot_id}')
def edit_snapshot(snapshot_id:str,data:Universe,db:Session=Depends(get_db),u=Depends(writer)):
    s=db.get(Snapshot,snapshot_id)
    if not s: raise HTTPException(404)
    c=owned_chapter(db,s.chapter_id,u,lock=True)
    if s.status=='verified' or c.revision!=s.revision: raise HTTPException(409,'This snapshot is frozen or outdated. Analyze the current draft to create a new review.')
    validate_universe(data,s.content)
    changed=db.execute(update(Snapshot).where(Snapshot.id==s.id,Snapshot.status=='pending').values(universe=data.model_dump()))
    if changed.rowcount!=1: db.rollback();raise HTTPException(409,'This review was verified in another request and is now frozen')
    db.commit();db.refresh(s);return snapshot_dict(s)
@app.post('/api/snapshots/{snapshot_id}/verify')
def verify(snapshot_id:str,data:Verification,db:Session=Depends(get_db),u=Depends(writer)):
    s=db.get(Snapshot,snapshot_id)
    if not s: raise HTTPException(404)
    c=owned_chapter(db,s.chapter_id,u,lock=True)
    if s.status=='verified': raise HTTPException(409,'Verified snapshots cannot be edited')
    if c.revision!=s.revision or data.revision!=c.revision: raise HTTPException(409,'Review is outdated. Analyze the latest manuscript first.')
    if not data.confirm_reader_safety: raise HTTPException(422,'Confirm reader safety and question wording before verification')
    validate_universe(data.universe,s.content,reviewed=True)
    changed=db.execute(update(Snapshot).where(Snapshot.id==s.id,Snapshot.status=='pending').values(universe=data.universe.model_dump(),status='verified'))
    if changed.rowcount!=1: db.rollback();raise HTTPException(409,'This snapshot is already verified')
    chapter_changed=db.execute(update(Chapter).where(Chapter.id==c.id,Chapter.revision==s.revision).values(state='verified'))
    if chapter_changed.rowcount!=1: db.rollback();raise HTTPException(409,'The manuscript changed during verification. Review the latest draft.')
    audit(db,u,'snapshot_verified',s.id);db.commit();db.refresh(s);return snapshot_dict(s)

@app.get('/api/stories/{story_id}/readers')
def readers(story_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    owned_story(db,story_id,u); result=[]
    for i in db.scalars(select(Invitation).where(Invitation.story_id==story_id)):
        reader=db.scalar(select(User).where(User.email==i.email))
        releases=list(db.scalars(select(Release).join(Chapter).where(Chapter.story_id==story_id,Release.reader_id==reader.id))) if reader else []
        result.append({'id':i.id,'email':i.email,'name':reader.name if reader else i.email.split('@')[0],'reader_id':reader.id if reader else None,'status':i.status,'releases':[{'id':r.id,'chapter_id':r.chapter_id,'active':bool(r.active),'progress':r.progress} for r in releases]})
    return result
@app.post('/api/stories/{story_id}/invitations')
def invite(story_id:str,data:InviteIn,db:Session=Depends(get_db),u=Depends(writer)):
    owned_story(db,story_id,u);email=data.email.strip().lower()
    if '@' not in email or '.' not in email.split('@')[-1]: raise HTTPException(422,'Enter a valid email address')
    target=db.scalar(select(User).where(User.email==email))
    if target and target.role!='beta': raise HTTPException(422,'Invite an account with the Beta Reader role')
    old=db.scalar(select(Invitation).where(Invitation.story_id==story_id,Invitation.email==email))
    if old:
        if old.status not in ['revoked','declined']: raise HTTPException(409,'This reader already has an invitation')
        old.status='pending';i=old
    else: i=Invitation(story_id=story_id,email=email);db.add(i)
    db.flush();audit(db,u,'reader_invited',i.id);db.commit();return {'id':i.id,'status':i.status}
@app.delete('/api/invitations/{invitation_id}')
def revoke(invitation_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    i=db.get(Invitation,invitation_id)
    if not i: raise HTTPException(404)
    owned_story(db,i.story_id,u);i.status='revoked'
    target=db.scalar(select(User).where(User.email==i.email))
    if target:
        for r in db.scalars(select(Release).join(Chapter).where(Chapter.story_id==i.story_id,Release.reader_id==target.id)): r.active=0
    audit(db,u,'access_revoked',i.id);db.commit();return {'ok':True}
@app.get('/api/inbox')
def inbox(db:Session=Depends(get_db),u=Depends(current_user)):
    if u.role!='beta': return []
    return [{'id':i.id,'status':i.status,'story_title':s.title,'writer':w.name} for i,s,w in db.execute(select(Invitation,Story,User).join(Story,Invitation.story_id==Story.id).join(User,Story.writer_id==User.id).where(Invitation.email==u.email))]
@app.post('/api/invitations/{invitation_id}/{decision}')
def decide(invitation_id:str,decision:str,db:Session=Depends(get_db),u=Depends(current_user)):
    i=db.get(Invitation,invitation_id)
    if not i or i.email!=u.email or u.role!='beta': raise HTTPException(404)
    if decision not in ['accept','decline'] or i.status!='pending': raise HTTPException(409,'Invitation is no longer pending')
    i.status='accepted' if decision=='accept' else 'declined';db.commit();return {'status':i.status}
@app.post('/api/chapters/{chapter_id}/release')
def release_chapter(chapter_id:str,data:ReleaseIn,db:Session=Depends(get_db),u=Depends(writer)):
    c=owned_chapter(db,chapter_id,u,lock=True);s=db.get(Snapshot,data.snapshot_id)
    if not s or s.chapter_id!=c.id or s.status!='verified' or s.revision!=c.revision: raise HTTPException(409,'A verified snapshot of the current draft is required')
    ready=[]
    for id in set(data.reader_ids):
        target=db.get(User,id)
        if not target or target.role!='beta': raise HTTPException(422,'Select a beta reader')
        i=db.scalar(select(Invitation).where(Invitation.story_id==c.story_id,Invitation.email==target.email,Invitation.status=='accepted'))
        if not i: raise HTTPException(409,'Every selected reader must accept the invitation first')
        old=db.scalar(select(Release).where(Release.chapter_id==c.id,Release.reader_id==id))
        if old and old.snapshot_id!=s.id: raise HTTPException(409,'This reader already has a frozen version. Use a fresh beta reader to test the revision.')
        ready.append((id,old))
    for id,old in ready:
        if old: old.active=1;continue
        r=Release(chapter_id=c.id,snapshot_id=s.id,reader_id=id);db.add(r);db.flush()
        for q in s.universe['questions']:
            if q.get('review_status','approved')!='approved':continue
            frequency=s.universe.get('question_frequency','each_chapter')
            if frequency=='key_moments' and q.get('timing','after_chapter')=='after_chapter':continue
            if frequency=='major_reveals' and q.get('timing')!='before_reveal':continue
            question=Question(release_id=r.id,text=q['text'],category=q['category'],source='writer-approved');db.add(question);db.flush()
            db.add(studio_models.QuestionPlacement(question_id=question.id,data={'timing':q.get('timing','after_chapter'),'checkpoint':q.get('checkpoint'),'target':q.get('target',''),'options':q.get('options',[])}))
    c.state='released';audit(db,u,'chapter_released',s.id);db.commit();return {'released':len(ready)}

@app.get('/api/library')
def library(db:Session=Depends(get_db),u=Depends(current_user)):
    if u.role!='beta': return [] # Public reading follows the MVP; drafts never appear here.
    rows=db.execute(select(Release,Snapshot,Chapter,Story).join(Snapshot,Release.snapshot_id==Snapshot.id).join(Chapter,Release.chapter_id==Chapter.id).join(Story,Chapter.story_id==Story.id).join(Invitation,(Invitation.story_id==Story.id)&(Invitation.email==u.email)).where(Release.reader_id==u.id,Release.active==1,Invitation.status=='accepted').order_by(Story.title,Chapter.position))
    return [{'id':r.id,'snapshot_id':s.id,'title':s.title,'story_title':story.title,'position':c.position,'progress':r.progress,'revision':s.revision} for r,s,c,story in rows]
@app.get('/api/read/{release_id}')
def read_chapter(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    r=release_for(db,release_id,u);s=db.get(Snapshot,r.snapshot_id);c=db.get(Chapter,r.chapter_id)
    return {'id':r.id,'snapshot_id':s.id,'title':s.title,'content':s.content[:boundary(db,r)],'checkpoint_pending':boundary(db,r)<len(s.content),'position':c.position,'revision':s.revision,'universe':visible_universe(db,r,beta=u.role=='beta'),'questions':question_rows(db,r.id,u.id),'feedback':feedback_rows(db,r.id),'progress':r.progress}
def question_rows(db,release_id,user_id):
    result=[]
    for q in db.scalars(select(Question).where(Question.release_id==release_id)):
        a=db.scalar(select(Answer).where(Answer.question_id==q.id,Answer.reader_id==user_id))
        r=db.get(Release,release_id);end=boundary(db,r);placement=db.get(studio_models.QuestionPlacement,q.id)
        checkpoint=placement.data.get('checkpoint') if placement else None
        if not a and end<len(db.get(Snapshot,r.snapshot_id).content) and (checkpoint is None or checkpoint>end):continue
        result.append({'id':q.id,'text':q.text,'category':q.category,'source':q.source,'options':placement.data.get('options',[]) if placement else [],'answer':{'text':a.text,'confidence':a.confidence,'emotion':a.emotion,'tension':a.tension} if a else None})
    return result
def feedback_rows(db,release_id):
    return [{k:getattr(f,k) for k in ['id','start','end','quote','category','text']} for f in db.scalars(select(Feedback).where(Feedback.release_id==release_id))]
@app.post('/api/read/{release_id}/complete')
def complete(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    r=release_for(db,release_id,u)
    if boundary(db,r)<len(db.get(Snapshot,r.snapshot_id).content):raise HTTPException(409,'Answer the reading checkpoint before continuing')
    r.progress=100;db.commit();return {'ok':True}
@app.post('/api/read/{release_id}/feedback')
def feedback(release_id:str,data:FeedbackIn,db:Session=Depends(get_db),u=Depends(current_user)):
    r=release_for(db,release_id,u);s=db.get(Snapshot,r.snapshot_id)
    if data.end<=data.start or data.end>boundary(db,r) or s.content[data.start:data.end]!=data.quote: raise HTTPException(422,'The selected passage no longer matches this released version')
    f=Feedback(release_id=r.id,reader_id=u.id,**data.model_dump());db.add(f);db.commit();return {'id':f.id}
@app.post('/api/questions/{question_id}/answer')
def answer(question_id:str,data:AnswerIn,db:Session=Depends(get_db),u=Depends(current_user)):
    q=db.get(Question,question_id)
    if not q: raise HTTPException(404)
    r=release_for(db,q.release_id,u)
    if q.id not in {x['id'] for x in question_rows(db,r.id,u.id)}:raise HTTPException(403,'This question is not available yet')
    a=Answer(question_id=q.id,release_id=r.id,reader_id=u.id,**data.model_dump());db.add(a)
    try: db.commit()
    except IntegrityError: db.rollback();raise HTTPException(409,'Submitted answers are locked to preserve prediction history')
    return {'id':a.id}

def safe_memory(db,u,story_id,position,current_release=None):
    rows=db.execute(select(Answer,Question,Chapter,Release,Invitation).join(Question,Answer.question_id==Question.id).join(Release,Answer.release_id==Release.id).join(Chapter,Release.chapter_id==Chapter.id).join(Invitation,(Invitation.story_id==Chapter.story_id)&(Invitation.email==u.email)).where(Answer.reader_id==u.id,Chapter.story_id==story_id,Chapter.position<=position,Release.active==1,Invitation.status=='accepted').order_by(Chapter.position,Answer.created))
    entries=[{'chapter':c.position,'question':q.text,'answer':a.text,'confidence':a.confidence,'category':q.category,'emotion':a.emotion,'created':a.created} for a,q,c,r,i in rows if current_release is None or r.id!=current_release]
    observations=db.execute(select(studio_models.ReaderObservation,Chapter,Release).join(Release,Release.id==studio_models.ReaderObservation.release_id).join(Chapter,Chapter.id==Release.chapter_id).join(Invitation,(Invitation.story_id==Chapter.story_id)&(Invitation.email==u.email)).where(studio_models.ReaderObservation.reader_id==u.id,Chapter.story_id==story_id,Chapter.position<=position,Release.active==1,Invitation.status=='accepted'))
    entries.extend({'chapter':c.position,'question':'Observation: '+o.target,'answer':o.explanation,'confidence':o.confidence,'category':o.kind,'emotion':o.target if o.kind=='emotion' else '', 'created':o.created} for o,c,r in observations if current_release is None or r.id!=current_release)
    return sorted(entries,key=lambda x:(x['chapter'],x['created']))[-20:]
@app.get('/api/read/{release_id}/memory')
def memory(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    r=release_for(db,release_id,u);c=db.get(Chapter,r.chapter_id);return safe_memory(db,u,c.story_id,c.position)
@app.post('/api/read/{release_id}/follow-up')
def followup(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
    r=release_for(db,release_id,u);c=db.get(Chapter,r.chapter_id);s=db.get(Snapshot,r.snapshot_id)
    existing=list(db.scalars(select(Question).where(Question.release_id==r.id,Question.source!='writer-approved')))
    if boundary(db,r)<len(s.content):raise HTTPException(409,'Finish the reading checkpoints before continuing the interview')
    if any(not db.scalar(select(Answer.id).where(Answer.question_id==q.id,Answer.reader_id==u.id)) for q in existing):return question_rows(db,r.id,u.id)
    if len(existing)>=5:raise HTTPException(422,'This interview has reached five follow-up questions. You can add observations and overall feedback.')
    memory=safe_memory(db,u,c.story_id,c.position)
    if not memory: raise HTTPException(422,'Answer a question first so the interview can build on your perspective')
    sample=s.mode in ['sample','manual']
    db.commit()
    if not sample:
        with local_ai.allowance(u.id,'follow-up'):
            generated=dynamic_questions(reader_projection(s.universe),memory,s.content,sample=False)
    else: generated=dynamic_questions(reader_projection(s.universe),memory,s.content,sample=sample)
    db.expire_all()
    release_for(db,release_id,u)
    for q in generated[:max(0,5-len(existing))]:
        question=Question(release_id=r.id,text=q['text'],category=q['category'],source=q['source']);db.add(question);db.flush()
        db.add(studio_models.QuestionPlacement(question_id=question.id,data={'timing':'after_chapter','checkpoint':None,'target':'','options':q.get('options',[])}))
    db.commit();return question_rows(db,r.id,u.id)

@app.get('/api/stories/{story_id}/analytics')
def analytics(story_id:str,db:Session=Depends(get_db),u=Depends(writer)):
    owned_story(db,story_id,u);result=[]
    for c in db.scalars(select(Chapter).where(Chapter.story_id==story_id).order_by(Chapter.position)):
        snapshots=list(db.scalars(select(Snapshot).where(Snapshot.chapter_id==c.id,Snapshot.status=='verified').order_by(Snapshot.created)))
        for s in snapshots:
            releases=list(db.scalars(select(Release).where(Release.snapshot_id==s.id)))
            ids=[r.id for r in releases]
            answers=list(db.scalars(select(Answer).where(Answer.release_id.in_(ids)))) if ids else []
            by_reader={}
            predictions={}
            for a in sorted(answers,key=lambda a:a.created):
                by_reader[a.reader_id]=a
                q=db.get(Question,a.question_id)
                if q.category=='prediction': predictions[a.reader_id]=a
            target=s.intent.get('prediction_target','').strip().casefold()
            correct=sum(target in a.text.casefold() for a in predictions.values()) if target else None
            reactions=list(by_reader.values());n=len(reactions)
            feedback=list(db.scalars(select(Feedback).where(Feedback.release_id.in_(ids)))) if ids else []
            result.append({'chapter':c.position,'title':s.title,'revision':s.revision,'snapshot_id':s.id,'released':len(releases),'completed':sum(r.progress==100 for r in releases),'respondents':n,'answers':len(answers),'intent':s.intent,'tension':round(sum(a.tension for a in reactions)/n) if n else None,'emotion_match':round(100*sum(a.emotion.casefold()==s.intent.get('emotion','').casefold() for a in reactions)/n) if n else None,'prediction_respondents':len(predictions),'prediction_matches':correct,'predictability':round(100*correct/len(predictions)) if target and predictions else None,'prediction_method':'Exact phrase match; author review required. Not an AI judgment of correctness.','feedback':[{'id':f.id,'quote':f.quote,'category':f.category,'text':f.text,'reader':db.get(User,f.reader_id).name} for f in feedback],'responses':[{'reader':db.get(User,a.reader_id).name,'question':db.get(Question,a.question_id).text,'answer':a.text,'confidence':a.confidence,'emotion':a.emotion,'tension':a.tension} for a in answers]})
    return result

from .features import install_features
install_features(app)
from .studio import install_studio, boundary, visible_universe
install_studio(app)

# A single-origin production container serves the static Next export and API.
# This also keeps the HttpOnly session cookie same-site without cross-domain workarounds.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
static_dir=Path(os.getenv('FRONTEND_DIST','../frontend/out'))
if static_dir.is_dir(): app.mount('/',StaticFiles(directory=static_dir,html=True),name='frontend')


