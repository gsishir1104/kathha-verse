from test_vertical_slice import clients

def test_guest_support(clients,monkeypatch):
    w,b,g=clients
    r=g.post('/api/support/guest',json={'email':'guest@example.com','subject':'Cannot sign in','body':'Please help with login'})
    assert r.status_code==200
    access=r.json()
    assert g.post('/api/support/guest/check',json={**access,'token':'x'*43}).status_code==404
    assert g.get('/api/support/cases/'+access['id']).status_code==401
    assert b.get('/api/support/cases/'+access['id']).status_code==404
    monkeypatch.setenv('STAFF_SUPPORT_IDS',w.get('/api/auth/me').json()['id'])
    assert any(c['id']==access['id'] and c['guest'] for c in w.get('/api/admin/ops/cases').json())
    detail=w.get('/api/support/cases/'+access['id']).json()
    assert detail['contact_email']=='guest@example.com' and 'token' not in detail
    assert w.post('/api/support/cases/'+access['id']+'/replies',json={'body':'Please describe the error'}).status_code==200
    assert w.put('/api/admin/ops/cases/'+access['id'],json={'status':'waiting_for_user','reason':'Need details'}).status_code==200
    response=g.post('/api/support/guest/check',json=access).json()
    assert response['status']=='waiting_for_user' and len(response['replies'])==2
    assert g.post('/api/support/guest/check',json={**access,'body':'Here is the error'}).status_code==200
    assert len(w.get('/api/support/cases/'+access['id']).json()['replies'])==3
