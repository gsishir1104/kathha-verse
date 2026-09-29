from fastapi import Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from .db import get_db, Chapter, Snapshot, Release, User, Feedback, GraphComment, FeedbackState, ChapterHistory
from .schemas import GraphCommentIn, FeedbackStateIn, RestoreIn
from .security import current_user, writer
from .analysis import reader_projection
from .studio import visible_universe


def graph_delta(previous, current):
    def entries(universe):
        entities=universe['entities']
        names={e['id']:(e['kind'],e['name'].strip().casefold()) for e in entities}
        return {names[e['id']]: (e, (e['summary'], sorted(names[x] for x in e['links'] if x in names), e['knowledge'])) for e in entities}
    old,new=entries(previous),entries(current)
    return {'added':[v[0]['name'] for k,v in new.items() if k not in old],
            'changed':[v[0]['name'] for k,v in new.items() if k in old and v[1]!=old[k][1]],
            'absent':[v[0]['name'] for k,v in old.items() if k not in new]}


def install_features(app):
    from .main import owned_chapter, owned_story, release_for, save_chapter
    from .schemas import ChapterIn

    @app.get('/api/chapters/{chapter_id}/history')
    def history(chapter_id:str, db:Session=Depends(get_db),u=Depends(writer)):
        owned_chapter(db,chapter_id,u)
        return [{'id':h.id,'revision':h.revision,'title':h.title,'content':h.content,'created':h.created} for h in db.scalars(select(ChapterHistory).where(ChapterHistory.chapter_id==chapter_id).order_by(ChapterHistory.created.desc()))]

    @app.post('/api/chapters/{chapter_id}/restore/{history_id}')
    def restore(chapter_id:str,history_id:str,data:RestoreIn,db:Session=Depends(get_db),u=Depends(writer)):
        c=owned_chapter(db,chapter_id,u)
        h=db.get(ChapterHistory,history_id)
        if not h or h.chapter_id!=c.id: raise HTTPException(404,'Saved version not found')
        return save_chapter(chapter_id,ChapterIn(title=h.title,content=h.content,intent=h.intent,revision=data.revision),db,u)

    @app.get('/api/read/{release_id}/graph-comments')
    def comments(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
        r=release_for(db,release_id,u)
        return [{'id':g.id,'entity_id':g.entity_id,'target_id':g.target_id,'category':g.category,'text':g.text} for g in db.scalars(select(GraphComment).where(GraphComment.snapshot_id==r.snapshot_id,GraphComment.reader_id==u.id,GraphComment.release_id==r.id).order_by(GraphComment.created))]

    @app.post('/api/read/{release_id}/graph-comments')
    def comment(release_id:str,data:GraphCommentIn,db:Session=Depends(get_db),u=Depends(current_user)):
        r=release_for(db,release_id,u)
        if r.snapshot_id!=data.snapshot_id: raise HTTPException(409,'This chapter was re-released. Reopen it before commenting.')
        s=db.get(Snapshot,r.snapshot_id)
        entities={e['id']:e for e in visible_universe(db,r,beta=u.role=='beta')['entities']}
        if data.entity_id not in entities: raise HTTPException(422,'Choose an entity in this released graph')
        if data.target_id and (data.target_id not in entities or data.target_id not in entities[data.entity_id]['links']): raise HTTPException(422,'Choose a visible connection from this entity')
        if not data.text.strip(): raise HTTPException(422,'Write a comment first')
        g=GraphComment(release_id=r.id,reader_id=u.id,**data.model_dump());db.add(g);db.commit();return {'id':g.id}

    @app.get('/api/read/{release_id}/graph-changes')
    def changes(release_id:str,db:Session=Depends(get_db),u=Depends(current_user)):
        r=release_for(db,release_id,u);c=db.get(Chapter,r.chapter_id);s=db.get(Snapshot,r.snapshot_id)
        previous=db.execute(select(Release,Chapter).join(Chapter,Release.chapter_id==Chapter.id).where(Release.reader_id==u.id,Release.active==1,Chapter.story_id==c.story_id,Chapter.position<c.position).order_by(Chapter.position.desc())).first()
        if not previous:return {'previous_chapter':None,'added':[],'changed':[],'absent':[]}
        prior,chapter=previous;release_for(db,prior.id,u)
        old=db.get(Snapshot,prior.snapshot_id)
        return {'previous_chapter':chapter.position,**graph_delta(visible_universe(db,prior,beta=u.role=='beta'),visible_universe(db,r,beta=u.role=='beta'))}

    @app.get('/api/chapters/{chapter_id}/graph-changes')
    def writer_changes(chapter_id:str,db:Session=Depends(get_db),u=Depends(writer)):
        c=owned_chapter(db,chapter_id,u)
        current=db.scalar(select(Snapshot).where(Snapshot.chapter_id==c.id,Snapshot.revision==c.revision).order_by(Snapshot.created.desc()))
        prior=db.execute(select(Snapshot,Chapter).join(Chapter,Snapshot.chapter_id==Chapter.id).where(Chapter.story_id==c.story_id,Chapter.position<c.position,Snapshot.status=='verified').order_by(Chapter.position.desc(),Snapshot.created.desc())).first()
        if not current or not prior:return {'previous_chapter':None,'added':[],'changed':[],'absent':[]}
        old,chapter=prior
        return {'previous_chapter':chapter.position,**graph_delta(reader_projection(old.universe,beta_graph=True),reader_projection(current.universe,beta_graph=True))}

    @app.get('/api/stories/{story_id}/feedback-board')
    def board(story_id:str,db:Session=Depends(get_db),u=Depends(writer)):
        owned_story(db,story_id,u);items=[]
        for f,r,c in db.execute(select(Feedback,Release,Chapter).join(Release,Feedback.release_id==Release.id).join(Chapter,Release.chapter_id==Chapter.id).where(Chapter.story_id==story_id)):
            key='inline:'+f.id;state=db.get(FeedbackState,key)
            items.append({'key':key,'chapter':c.position,'target':f.quote,'category':f.category,'text':f.text,'reader':db.get(User,f.reader_id).name,'status':state.status if state else 'new'})
        for g,s,c in db.execute(select(GraphComment,Snapshot,Chapter).join(Snapshot,GraphComment.snapshot_id==Snapshot.id).join(Chapter,Snapshot.chapter_id==Chapter.id).where(Chapter.story_id==story_id)):
            names={e['id']:e['name'] for e in s.universe['entities']};key='graph:'+g.id;state=db.get(FeedbackState,key)
            target=names.get(g.entity_id,'Entity')+(' → '+names.get(g.target_id,'Connection') if g.target_id else '')
            items.append({'key':key,'chapter':c.position,'revision':s.revision,'target':target,'category':g.category,'text':g.text,'reader':db.get(User,g.reader_id).name,'status':state.status if state else 'new'})
        return items

    @app.put('/api/stories/{story_id}/feedback-board/{key}')
    def review_feedback(story_id:str,key:str,data:FeedbackStateIn,db:Session=Depends(get_db),u=Depends(writer)):
        items=board(story_id,db,u)
        if not any(i['key']==key for i in items):raise HTTPException(404,'Feedback not found')
        state=db.get(FeedbackState,key)
        if state:state.status=data.status
        else:db.add(FeedbackState(key=key,status=data.status))
        db.commit();return {'status':data.status}
