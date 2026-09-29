from test_vertical_slice import clients,invite

def test_private_chat_and_revocation(clients,monkeypatch):
    w,b,x=clients
    s=w.get('/api/stories').json()[0]
    pending=w.post('/api/stories/'+s['id']+'/invitations',json={'email':'beta@storylens.test'}).json()['id']
    assert w.post('/api/chat/'+pending,json={'body':'Hello'}).status_code==404
    assert b.post('/api/invitations/'+pending+'/accept').status_code==200
    assert x.get('/api/chat/'+pending).status_code==401
    x.post('/api/auth/demo/reader')
    assert x.get('/api/chat/'+pending).status_code in (403,404)
    assert w.post('/api/chat/'+pending,json={'body':'   '}).status_code==422
    assert w.post('/api/chat/'+pending,json={'body':'Hello reader'}).status_code==200
    assert b.get('/api/chat').json()[0]['unread']==1
    assert b.get('/api/chat/'+pending).json()[0]['body']=='Hello reader'
    assert b.post('/api/chat/'+pending+'/read').status_code==200
    assert b.get('/api/chat').json()[0]['unread']==0
    assert b.post('/api/chat/presence').status_code==200
    assert w.get('/api/chat').json()[0]['online']
    monkeypatch.setenv('ADMIN_USER_IDS',x.get('/api/auth/me').json()['id'])
    assert x.get('/api/chat/'+pending).status_code in (403,404)
    assert w.delete('/api/invitations/'+pending).status_code==200
    assert b.get('/api/chat/'+pending).status_code==404
    assert w.post('/api/chat/'+pending,json={'body':'Blocked'}).status_code==404

