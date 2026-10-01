import os
# Database is isolated by conftest before application imports.
os.environ['DEMO_MODE']='true'
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import app, attempts
from app.db import Base,engine
from app.sample import SAMPLE_CONTENT

@pytest.fixture
def clients():
    Base.metadata.drop_all(engine);attempts.clear()
    with TestClient(app) as w, TestClient(app) as b, TestClient(app) as stranger:
        assert w.post('/api/auth/demo/writer').status_code==200
        assert b.post('/api/auth/demo/beta').status_code==200
        yield w,b,stranger
    Base.metadata.drop_all(engine)

def prepare(w,b):
    story=w.get('/api/stories').json()[0];c=story['chapters'][0]
    s=w.post(f'/api/chapters/{c["id"]}/analyze').json()
    return story,c,s
def verify(w,c,s):
    u=deepcopy(s['universe'])
    for e in u['entities']:e['status']='confirmed'
    r=w.post(f'/api/snapshots/{s["id"]}/verify',json={'revision':c['revision'],'universe':u,'confirm_reader_safety':True})
    assert r.status_code==200,r.text
    return r.json()
def invite(w,b,story):
    r=w.post(f'/api/stories/{story["id"]}/invitations',json={'email':'beta@storylens.test'})
    assert r.status_code==200,r.text
    assert b.post(f'/api/invitations/{r.json()["id"]}/accept').status_code==200
    return r.json()['id']
def release(w,b,c,s):
    bid=b.get('/api/auth/me').json()['id']
    r=w.post(f'/api/chapters/{c["id"]}/release',json={'snapshot_id':s['id'],'reader_ids':[bid]})
    assert r.status_code==200,r.text
    return b.get('/api/library').json()[0]['id']

def test_full_vertical_slice_and_private_boundary(clients):
    w,b,x=clients;story,c,s=prepare(w,b)
    # Authentication, role and chapter access are server-side checks.
    assert x.get('/api/stories').status_code==401
    assert b.get('/api/stories').status_code==403
    assert b.get(f'/api/chapters/{c["id"]}').status_code==403
    assert b.get(f'/api/stories/{story["id"]}/analytics').status_code==403
    bid=b.get('/api/auth/me').json()['id']
    assert w.post(f'/api/chapters/{c["id"]}/release',json={'snapshot_id':s['id'],'reader_ids':[bid]}).status_code==409
    for e in s['universe']['entities']:
        if e['id']=='mara':e['knowledge'].append({'text':'PRIVATE_KNOWLEDGE_CANARY','state':'does_not_know','reader_safe':False,'evidence':'Mara stopped at the edge of the harbor'})
    s=verify(w,c,s)
    assert w.post(f'/api/chapters/{c["id"]}/release',json={'snapshot_id':s['id'],'reader_ids':[bid]}).status_code==409
    invitation=invite(w,b,story);rid=release(w,b,c,s)
    reading=b.get('/api/read/'+rid);assert reading.status_code==200
    payload=reading.json();assert 'PRIVATE_KNOWLEDGE_CANARY' not in reading.text
    assert 'prediction_target' not in reading.text
    assert payload['universe']['entities']==[]
    assert b.get('/api/read/'+rid+'/story-state').status_code==409
    assert b.get('/api/read/'+rid+'/graph-changes').status_code==409
    assert x.get('/api/read/'+rid).status_code==401
    assert w.get('/api/read/'+rid).status_code==404
    assert x.post('/api/auth/register',json={'name':'Outsider','email':'outsider@example.test','password':'secure-password-123','role':'beta'}).status_code==200
    assert x.get('/api/read/'+rid).status_code==404
    assert x.get('/api/read/'+rid+'/memory').status_code==404
    # Exact anchors reject fabricated quotations.
    quote='The lighthouse had been dark for eleven years.'
    f={'start':0,'end':len(quote),'quote':quote,'category':'positive','text':'The opening made me immediately curious.'}
    assert b.post('/api/read/'+rid+'/feedback',json={**f,'quote':'invented'}).status_code==422
    assert b.post('/api/read/'+rid+'/feedback',json=f).status_code==200
    q=payload['questions'][0]
    a={'text':'I think Elias is alive. The dry letter is my clue.','confidence':72,'emotion':'Curiosity','tension':80}
    assert x.post('/api/questions/'+q['id']+'/answer',json=a).status_code==404
    assert b.post('/api/questions/'+q['id']+'/answer',json=a).status_code==200
    assert b.post('/api/questions/'+q['id']+'/answer',json={**a,'text':'Changed after reveal'}).status_code==409
    assert b.post('/api/read/'+rid+'/complete').status_code==200
    completed=b.get('/api/read/'+rid).json()
    assert {e['id'] for e in completed['universe']['entities']} == {e['id'] for e in s['universe']['entities'] if e['status']=='confirmed'}
    safe_ids={e['id'] for e in completed['universe']['entities']}
    assert all(set(e['links'])<=safe_ids for e in completed['universe']['entities'])
    assert len(b.get('/api/read/'+rid+'/memory').json())==1
    follow=b.post('/api/read/'+rid+'/follow-up');assert follow.status_code==200
    assert any('Earlier you wrote' in q['text'] for q in follow.json())
    assert len(b.post('/api/read/'+rid+'/follow-up').json())==len(follow.json())
    metrics=w.get(f'/api/stories/{story["id"]}/analytics').json()[0]
    assert metrics['respondents']==1 and metrics['tension']==80 and metrics['predictability']==100
    assert metrics['emotion_match']==100 and metrics['completed']==1 and len(metrics['feedback'])==1
    # Revocation also closes memory, follow-up, feedback and answer surfaces.
    assert w.delete('/api/invitations/'+invitation).status_code==200
    for path in ['/api/read/'+rid,'/api/read/'+rid+'/memory']:
        assert b.get(path).status_code==404
    assert b.get('/api/library').json()==[]
    assert b.post('/api/read/'+rid+'/follow-up').status_code==404
    assert b.post('/api/read/'+rid+'/feedback',json=f).status_code==404

def test_reviews_require_explicit_decisions_evidence_and_safety(clients):
    w,b,x=clients;story,c,s=prepare(w,b)
    url=f'/api/snapshots/{s["id"]}/verify'
    data={'revision':1,'universe':s['universe'],'confirm_reader_safety':True}
    assert w.post(url,json=data).status_code==422
    for e in data['universe']['entities']:e['status']='confirmed'
    data['confirm_reader_safety']=False
    assert w.post(url,json=data).status_code==422
    data['confirm_reader_safety']=True;data['universe']['entities'][0]['evidence']='fabricated'
    assert w.post(url,json=data).status_code==422
    data['universe']['entities'][0]['evidence']='Tonight, someone had lit it.'
    data['universe']['entities'][0]['links']=['unknown-id']
    assert w.post(url,json=data).status_code==422

def test_edits_invalidate_reviews_but_never_mutate_released_snapshots(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    assert w.put('/api/snapshots/'+s['id'],json=s['universe']).status_code==409
    new={k:c[k] for k in ['title','content','revision','intent']};new['content']+='\n\nFUTURE_CANARY'
    assert w.put('/api/chapters/'+c['id'],json=new).status_code==200
    assert w.put('/api/chapters/'+c['id'],json=new).status_code==409
    assert 'FUTURE_CANARY' not in b.get('/api/read/'+rid).text
    assert b.get('/api/read/'+rid).json()['content']==SAMPLE_CONTENT
    bid=b.get('/api/auth/me').json()['id']
    assert w.post('/api/chapters/'+c['id']+'/release',json={'snapshot_id':s['id'],'reader_ids':[bid]}).status_code==409
    new_snapshot=w.post('/api/chapters/'+c['id']+'/manual').json()
    new['revision']=2
    assert w.put('/api/chapters/'+c['id'],json=new).status_code==200
    assert w.post('/api/snapshots/'+new_snapshot['id']+'/verify',json={'revision':2,'universe':new_snapshot['universe'],'confirm_reader_safety':True}).status_code==409

def test_later_chapter_memory_never_appears_in_earlier_chapter(clients):
    w,b,x=clients;story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    c2=w.post('/api/stories/'+story['id']+'/chapters',json={'title':'Later','content':'FUTURE_CANARY is visible here.'}).json()
    s2=w.post('/api/chapters/'+c2['id']+'/manual').json()
    s2['universe']['questions']=[{'text':'What did you think about FUTURE_CANARY?','category':'trust','evidence':'FUTURE_CANARY'}]
    s2=verify(w,c2,s2)
    bid=b.get('/api/auth/me').json()['id']
    assert w.post('/api/chapters/'+c2['id']+'/release',json={'snapshot_id':s2['id'],'reader_ids':[bid]}).status_code==200
    rid2=next(r['id'] for r in b.get('/api/library').json() if r['position']==2)
    q=b.get('/api/read/'+rid2).json()['questions'][0]
    assert b.post('/api/questions/'+q['id']+'/answer',json={'text':'FUTURE_CANARY','confidence':90}).status_code==200
    assert b.get('/api/read/'+rid+'/memory').json()==[]
    assert 'FUTURE_CANARY' not in b.get('/api/read/'+rid).text
    assert b.post('/api/read/'+rid+'/follow-up').status_code==422

def test_auth_csrf_ownership_and_reader_defaults(clients):
    w,b,x=clients
    data={'name':'New author','email':'author@example.test','password':'1234567890X','role':'writer'}
    assert x.post('/api/auth/register',json=data).status_code==200
    assert x.get('/api/stories').json()==[]
    story=w.get('/api/stories').json()[0]
    assert x.get('/api/stories/'+story['id']+'/analytics').status_code==404
    assert x.get('/api/chapters/'+story['chapters'][0]['id']).status_code==404
    assert x.post('/api/stories',json={'title':'test'},headers={'Origin':'https://evil.test'}).status_code==403
    assert x.post('/api/auth/logout').status_code==200
    assert x.get('/api/stories').status_code==401
    assert x.post('/api/auth/login',json={'email':data['email'],'password':'incorrectxx'}).status_code==401
    assert x.post('/api/auth/login',json={'email':data['email'],'password':data['password']}).status_code==200
    cookie=x.cookies.get('storylens_session');assert cookie and len(cookie)>30
    assert x.post('/api/auth/demo/reader').status_code==200
    assert x.get('/api/library').json()==[]
    assert not x.get('/api/auth/me').json()['preferences'].get('interactive_reading',False)
    assert x.put('/api/preferences',json={'interactive_reading':True}).json()['preferences']['interactive_reading'] is True

def test_private_fields_absent_from_question_generator_context(clients,monkeypatch):
    w,b,x=clients;story,c,s=prepare(w,b);s['universe']['entities'][-1]['reader_safe']=False
    s['universe']['entities'][-1]['summary']='AUTHOR_SECRET_CANARY'
    s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    q=b.get('/api/read/'+rid).json()['questions'][0]
    b.post('/api/questions/'+q['id']+'/answer',json={'text':'My answer','confidence':30})
    def fake(safe_universe,memory,content,sample=False):
        import json
        serialized=json.dumps([safe_universe,memory,content])
        assert 'AUTHOR_SECRET_CANARY' not in serialized
        assert 'prediction_target' not in serialized
        return []
    monkeypatch.setattr('app.main.dynamic_questions',fake)
    assert b.post('/api/read/'+rid+'/follow-up').status_code==200
