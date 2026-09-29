from test_vertical_slice import clients
from app.db import SessionLocal, User
from sqlalchemy import select

def test_admin_access_and_suspension(clients,monkeypatch):
    w,b,guest=clients
    owner=w.get('/api/auth/me').json(); reader=b.get('/api/auth/me').json()
    assert guest.get('/api/admin/accounts').status_code==401
    assert w.get('/api/admin/accounts').status_code==403
    monkeypatch.setenv('ADMIN_USER_IDS',owner['id'])
    assert w.get('/api/auth/me').json()['is_admin']
    assert w.get('/api/stories').status_code==403
    assert w.get('/api/library').status_code==403
    assert b.get('/api/admin/accounts').status_code==403
    assert w.get('/api/admin/accounts?q=Jamie').json()['total']==1
    data=dict(name='Updated reader',role='beta',suspended=True,reason='Abuse review')
    assert w.put('/api/admin/accounts/'+reader['id'],json=data).status_code==200
    assert b.get('/api/auth/me').status_code==401
    assert b.post('/api/auth/demo/beta').status_code==403
    data['suspended']=False
    assert w.put('/api/admin/accounts/'+reader['id'],json=data).status_code==200
    assert b.post('/api/auth/demo/beta').status_code==200
    assert b.get('/api/auth/me').json()['name']=='Updated reader'
    data['suspended']=True
    assert w.put('/api/admin/accounts/'+owner['id'],json=data).status_code==409
    assert len(w.get('/api/admin/activity').json())==2
    assert w.get('/api/admin/overview').status_code==200
    assert w.post('/api/admin/accounts/'+reader['id']+'/revoke-sessions').status_code==200
    assert b.get('/api/auth/me').status_code==401

def test_suspension_blocks_existing_and_google_sessions(clients,monkeypatch):
    from app.db import AccountControl
    from app import google_login as google
    from test_google_login import configure, begin, finish
    w,b,g=clients
    configure(monkeypatch)
    monkeypatch.setattr(google,'google_profile',lambda *args:dict(sub='admin-suspension-test',email='suspended@example.test',email_verified=True,name='Test reader'))
    assert finish(g,begin(g)).headers['location']=='/'
    uid=g.get('/api/auth/me').json()['id']
    with SessionLocal() as db:
        db.add(AccountControl(user_id=uid,suspended=1));db.commit()
    assert g.get('/api/auth/me').status_code==403
    assert 'suspended' in finish(g,begin(g)).headers['location']

def test_writer_role_protection_and_validation(clients,monkeypatch):
    w,b,g=clients
    owner=w.get('/api/auth/me').json(); reader=b.get('/api/auth/me').json()
    monkeypatch.setenv('ADMIN_USER_IDS',reader['id'])
    data=dict(name='Changed writer',role='beta',suspended=False,reason='Requested change')
    assert b.put('/api/admin/accounts/'+owner['id'],json=data).status_code==409
    data['role']='admin'
    assert b.put('/api/admin/accounts/'+owner['id'],json=data).status_code==422
    assert b.put('/api/admin/accounts/missing',json={**data,'role':'writer'}).status_code==404

def test_user_activity_tracking(clients,monkeypatch):
    w,b,g=clients
    owner=w.get('/api/auth/me').json();reader=b.get('/api/auth/me').json()
    assert b.put('/api/preferences',json={'interactive_reading':False}).status_code==200
    assert b.put('/api/preferences',json={'password':'must-not-be-logged'}).status_code==422
    monkeypatch.setenv('ADMIN_USER_IDS',owner['id'])
    response=w.get('/api/admin/accounts/'+reader['id']+'/activity')
    assert response.status_code==200
    data=response.json()
    assert data['last_active'] and data['last_login'] and data['sessions']==1
    assert len([a for a in data['items'] if a['action']=='Updated reading preferences'])==1
    assert 'must-not-be-logged' not in response.text
    assert b.get('/api/admin/accounts/'+reader['id']+'/activity').status_code==403
    assert g.get('/api/admin/accounts/'+reader['id']+'/activity').status_code==401

def test_notifications_are_private(clients,monkeypatch):
    w,b,g=clients
    owner=w.get('/api/auth/me').json();reader=b.get('/api/auth/me').json()
    monkeypatch.setenv('ADMIN_USER_IDS',owner['id'])
    payload={'recipients':[reader['id'],reader['id']],'title':'Welcome','body':'Your account notification'}
    assert b.post('/api/admin/notifications',json=payload).status_code==403
    assert w.post('/api/admin/notifications',json=payload).json()['sent']==1
    inbox=b.get('/api/notifications').json()
    assert inbox['unread']==1 and len(inbox['items'])==1
    notice=inbox['items'][0]['id']
    assert w.get('/api/notifications').json()['total']==0
    assert w.post('/api/notifications/'+notice+'/read').status_code==404
    assert b.post('/api/notifications/'+notice+'/read').status_code==200
    assert b.get('/api/notifications').json()['unread']==0
    assert w.post('/api/admin/notifications',json={**payload,'recipients':['missing']}).status_code==404

def test_relationship_statistics(clients,monkeypatch):
    from test_vertical_slice import prepare,verify,invite,release
    from app.db import Release
    w,b,g=clients
    story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);rid=release(w,b,c,s)
    owner=w.get('/api/auth/me').json()
    monkeypatch.setenv('ADMIN_USER_IDS',owner['id'])
    assert b.get('/api/admin/relationships').status_code==403
    data=w.get('/api/admin/relationships').json()
    pair=data['relationships'][0]
    assert pair['released']==1 and pair['completed']==0 and not pair['all_released_read']
    assert data['readers'][0]['invited']==1 and data['readers'][0]['accepted']==1
    with SessionLocal() as db:
        r=db.get(Release,rid);r.progress=100;db.commit()
    assert w.get('/api/admin/relationships').json()['relationships'][0]['all_released_read']
    with SessionLocal() as db:
        r=db.get(Release,rid);r.active=0;db.commit()
    pair=w.get('/api/admin/relationships').json()['relationships'][0]
    assert pair['released']==0 and not pair['all_released_read']

def test_account_dashboard_scoping(clients,monkeypatch):
    from test_vertical_slice import prepare,verify,invite,release
    w,b,g=clients
    story,c,s=prepare(w,b);s=verify(w,c,s);invite(w,b,story);release(w,b,c,s)
    owner=w.get('/api/auth/me').json();reader=b.get('/api/auth/me').json()
    monkeypatch.setenv('ADMIN_USER_IDS',owner['id'])
    assert b.get('/api/admin/accounts/'+owner['id']+'/dashboard').status_code==403
    data=w.get('/api/admin/accounts/'+owner['id']+'/dashboard').json()
    assert len(data['stories'])==1 and len(data['relationships'])==1
    assert data['stories'][0]['words']>0
    assert 'content' not in data['stories'][0]['chapters'][0]
    data=w.get('/api/admin/accounts/'+reader['id']+'/dashboard').json()
    assert data['stories']==[] and len(data['relationships'])==1
    assert w.get('/api/admin/accounts/missing/dashboard').status_code==404
