from test_vertical_slice import clients
from app.db import SessionLocal,User
from app.ops_models import OperationSetting

def test_case_privacy_and_staff_scopes(clients,monkeypatch):
    w,b,g=clients
    owner=w.get('/api/auth/me').json();reader=b.get('/api/auth/me').json()
    c=b.post('/api/support/cases',json={'category':'access','subject':'Cannot read chapter','body':'Please check my invitation.'}).json()
    assert 'id' in c
    assert w.get('/api/support/cases/'+c['id']).status_code==404
    monkeypatch.setenv('STAFF_SUPPORT_IDS',owner['id'])
    assert w.get('/api/admin/accounts').status_code==403
    assert w.get('/api/admin/ops/cases').status_code==200
    assert w.get('/api/support/cases/'+c['id']).status_code==200
    assert w.put('/api/admin/ops/ai/pause',json={'enabled':True,'reason':'Test stop'}).status_code==403
    assert w.post('/api/support/cases/'+c['id']+'/replies',json={'body':'We are investigating.'}).status_code==200
    assert b.get('/api/notifications').json()['unread']==1
    assert b.get('/api/admin/ops/cases').status_code==403
    assert g.get('/api/support/cases/'+c['id']).status_code==401

def test_owner_pause_audit_and_metadata(clients,monkeypatch):
    w,b,g=clients;uid=w.get('/api/auth/me').json()['id'];monkeypatch.setenv('ADMIN_USER_IDS',uid)
    assert w.put('/api/admin/ops/ai/pause',json={'enabled':True,'reason':'Investigate failures'}).status_code==200
    assert w.get('/api/admin/ops/ai').json()['paused']
    from app.local_ai import structured,CitedUniverse
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException) as error:structured(CitedUniverse,'test',{})
    assert error.value.status_code==503
    logs=w.get('/api/admin/ops/audit?q=local_ai_paused').json()
    assert logs['total']==1 and logs['items'][0]['reason']=='Investigate failures'
    data=w.get('/api/admin/ops/stories').json()
    assert data and 'content' not in str(data)

def test_ai_jobs_capture_success_and_failure(clients,monkeypatch):
    from app import local_ai
    from app.ops_models import AIJob
    from sqlalchemy import select
    monkeypatch.setattr(local_ai,'_structured_request',lambda *args:('result',12,8))
    assert local_ai.structured(local_ai.CitedUniverse,'private text',{})=='result'
    with SessionLocal() as db:
        job=db.scalar(select(AIJob));assert job.status=='completed' and job.input_tokens==12
    def fail(*args):raise ValueError('private provider details')
    monkeypatch.setattr(local_ai,'_structured_request',fail)
    import pytest
    with pytest.raises(ValueError):local_ai.structured(local_ai.CitedUniverse,'secret manuscript',{})
    with SessionLocal() as db:
        jobs=list(db.scalars(select(AIJob)));assert len(jobs)==2
        assert any(j.status=='failed' for j in jobs)
