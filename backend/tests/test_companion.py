from test_vertical_slice import clients
from app import local_ai
from app.companion import CompanionAnswer
from app.db import SessionLocal,Story,Chapter,Snapshot
from app.support_delivery import SupportMail,message
from sqlalchemy import select

def test_companion_isolation_and_retrieval(clients,monkeypatch):
    w,b,x=clients
    s=w.get('/api/companion').json()['stories'][0];cid=s['chapters'][0]['id'];sid=s['id']
    owner=w.get('/api/auth/me').json()['id']
    with SessionLocal() as db:
        c=db.get(Chapter,cid)
        db.add(Snapshot(chapter_id=cid,revision=c.revision,title=c.title,content=c.content,mode='manual',status='verified',universe={'entities':[{'name':'Canon','status':'confirmed'},{'name':'Unapproved','status':'pending'}]},intent={}))
        other=Story(writer_id=owner,title='Different book');db.add(other);db.commit();other_id=other.id
    payloads=[]
    def generate(schema,system,payload):
        payloads.append(payload)
        return CompanionAnswer(response='Interpretation: review Chapter 1. New idea: try another opening.',source_ids=[1])
    monkeypatch.setattr(local_ai,'structured',generate)
    r=w.post('/api/companion/'+sid,json={'question':'Explore the character arc','chapter_id':cid})
    assert r.status_code==200,r.text
    assert r.json()['sources'][0]['chapter']==1 and r.json()['verified_fact_count']==1
    assert 'Unapproved' not in str(payloads)
    assert len(w.get('/api/companion/'+sid).json()['turns'])==1
    assert w.get('/api/companion/'+other_id).json()['turns']==[]
    assert b.get('/api/companion/'+sid).status_code==403
    assert x.get('/api/companion/'+sid).status_code==401
    assert w.post('/api/companion/'+other_id,json={'question':'Question','chapter_id':cid}).status_code==404
    monkeypatch.setenv('ADMIN_USER_IDS',owner)
    assert w.get('/api/companion/'+sid).status_code==403

def test_invalid_reference_refunds_and_does_not_save(clients,monkeypatch):
    w,_,_=clients;s=w.get('/api/companion').json()['stories'][0]
    monkeypatch.setattr(local_ai,'structured',lambda *args:CompanionAnswer(response='Invalid reference',source_ids=[999]))
    assert w.post('/api/companion/'+s['id'],json={'question':'Suggest a twist'}).status_code==502
    result=w.get('/api/companion/'+s['id']).json()
    assert result['turns']==[] and result['usage']['used']==0
    monkeypatch.setattr(local_ai,'DAILY_LIMIT',0)
    assert w.post('/api/companion/'+s['id'],json={'question':'Suggest a twist'}).status_code==429

def test_support_metadata_privacy_and_assignment(clients,monkeypatch):
    w,b,x=clients;admin=w.get('/api/auth/me').json()['id'];monkeypatch.setenv('ADMIN_USER_IDS',admin)
    r=b.post('/api/support/cases',json={'subject':'Access problem','category':'access','body':'PRIVATE_EVIDENCE','urgency':'high'})
    assert r.status_code==200,r.text
    cid=r.json()['id']
    assert x.get('/api/support/cases/'+cid).status_code==401
    assert b.get('/api/support/cases/'+cid).json()['urgency']=='high'
    with SessionLocal() as db:
        row=db.scalar(select(SupportMail));assert row and row.urgency=='high'
        msg=message(row,{'sender':'support@example.com','url':'https://example.com','reply_to':''})
        assert 'PRIVATE_EVIDENCE' not in str(msg) and cid in str(msg)
    assert w.get('/api/admin/ops/case-assignees/'+cid).json()==[{'id':admin,'name':'Alex Morgan'}]
    assert w.put('/api/admin/ops/cases/'+cid,json={'status':'investigating','reason':'Checking access','assigned_to':admin}).status_code==200
    assert b.get('/api/support/cases/'+cid).json()['assigned_to']==admin
    assert b.post('/api/support/cases',json={'subject':'Screenshot','category':'support','body':'Please help','screenshot':'data:image/svg+xml;base64,PHN2Zz4='}).status_code==422

def test_support_outbox_delivers_once_without_private_content(clients,monkeypatch):
    from app import welcome_email,support_delivery
    w,b,_=clients;monkeypatch.setenv('ADMIN_USER_IDS',w.get('/api/auth/me').json()['id'])
    monkeypatch.setattr(welcome_email,'settings',lambda:{'sender':'support@example.com','url':'https://example.com','reply_to':''})
    sent=[];monkeypatch.setattr(welcome_email,'deliver',lambda msg,config:sent.append(str(msg)))
    b.post('/api/support/cases',json={'subject':'PRIVATE_SUBJECT','category':'support','body':'PRIVATE_BODY'})
    assert support_delivery.process_one()
    assert not support_delivery.process_one()
    assert len(sent)==1 and 'PRIVATE_BODY' not in sent[0] and 'PRIVATE_SUBJECT' not in sent[0]

def test_other_writer_cannot_read_or_prompt_private_story(clients):
    w,b,x=clients;sid=w.get('/api/companion').json()['stories'][0]['id']
    r=x.post('/api/auth/register',json={'name':'Other writer','email':'other@example.com','password':'SafePassword123!','role':'writer'})
    assert r.status_code==200,r.text
    assert x.get('/api/companion/'+sid).status_code==404
    assert x.post('/api/companion/'+sid,json={'question':'Tell me about this story'}).status_code==404
    assert x.get('/api/companion').json()['stories']==[]
