from test_vertical_slice import clients,prepare,verify,invite,release

def test_publication_gate_private_projection_and_unpublish(clients):
    w,b,g=clients;story,c,s=prepare(w,b)
    assert b.get('/api/discover').json()==[]
    path='/api/chapters/'+c['id']+'/publication'
    assert w.put(path,json={'snapshot_id':s['id'],'active':True}).status_code==409
    s=verify(w,c,s)
    assert b.put(path,json={'snapshot_id':s['id'],'active':True}).status_code==403
    assert w.put(path,json={'snapshot_id':s['id'],'active':True}).status_code==200
    assert len(b.get('/api/discover').json())==1
    read=b.get('/api/public/read/'+c['id']);assert read.status_code==200
    assert 'intent' not in read.json()
    assert read.json()['universe']['entities']==[]
    assert all(e['reader_safe'] for e in read.json()['universe']['entities'])
    assert b.get('/api/snapshots/'+s['id']+'/preview').status_code==403
    assert w.get('/api/snapshots/'+s['id']+'/preview').status_code==200
    assert b.put('/api/preferences',json={'interactive_reading':True}).status_code==200
    assert b.put('/api/public/read/'+c['id'],json={'progress':50,'bookmark':0,'theory':'PRIVATE_THEORY'}).status_code==200
    assert 'PRIVATE_THEORY' not in w.get('/api/public/read/'+c['id']).text
    assert b.get('/api/public/read/'+c['id']+'/discussion').status_code==409
    assert b.post('/api/public/read/'+c['id']+'/recap').status_code==409
    assert b.put('/api/public/read/'+c['id'],json={'progress':100,'bookmark':0,'theory':'PRIVATE_THEORY'}).status_code==200
    assert b.get('/api/public/read/'+c['id']).json()['universe']['entities']
    assert b.post('/api/public/read/'+c['id']+'/discussion',json={'body':'A compelling opening.'}).status_code==200
    assert len(b.get('/api/public/read/'+c['id']+'/discussion').json())==1
    assert w.get('/api/public/read/'+c['id']+'/discussion').status_code==403
    assert w.put(path,json={'snapshot_id':s['id'],'active':False}).status_code==200
    assert b.get('/api/public/read/'+c['id']).status_code==404

def test_question_review_and_frequency(clients):
    w,b,g=clients;story,c,s=prepare(w,b)
    s['universe']['questions'][0]['review_status']='pending'
    for e in s['universe']['entities']:e['status']='confirmed'
    body={'revision':c['revision'],'universe':s['universe'],'confirm_reader_safety':True}
    assert w.post('/api/snapshots/'+s['id']+'/verify',json=body).status_code==422
    s['universe']['questions'][0]['review_status']='rejected'
    s['universe']['question_frequency']='major_reveals'
    s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    assert b.get('/api/read/'+rid).json()['questions']==[]

def test_incidents_permissions_and_audit(clients,monkeypatch):
    w,b,g=clients
    b.get('/api/stories')
    uid=w.get('/api/auth/me').json()['id'];monkeypatch.setenv('ADMIN_USER_IDS',uid)
    assert b.get('/api/admin/ops/incidents').status_code==403
    rows=w.get('/api/admin/ops/incidents').json();assert rows
    r=w.put('/api/admin/ops/incidents/'+rows[0]['id'],json={'status':'investigating','severity':'high','reason':'Check permission boundary'})
    assert r.status_code==200
    assert w.get('/api/admin/ops/audit?q=incident_investigating').json()['total']==1
