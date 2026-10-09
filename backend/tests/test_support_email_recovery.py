from test_vertical_slice import clients
from app.db import SessionLocal,User,SessionToken
from app.support_delivery import SupportMail,SupportMailContent,message
from app.support_recovery import PasswordRecovery
from app.security import password_ok
from sqlalchemy import select
import time

def setup_case(clients,monkeypatch,email='beta@storylens.test'):
    w,b,g=clients
    monkeypatch.setenv('STAFF_SUPPORT_IDS',w.get('/api/auth/me').json()['id'])
    config={'sender':'support@kathhaverse.org','reply_to':'support@kathhaverse.org','url':'https://www.kathhaverse.org'}
    monkeypatch.setattr('app.operations.support_settings',lambda:config)
    monkeypatch.setattr('app.support_recovery.support_settings',lambda:config)
    case=g.post('/api/support/guest',json={'email':email,'subject':'Forgot password','body':'Please help me sign in'}).json()
    return w,b,g,case,config

def test_guest_email_reply_and_admin_notification(clients,monkeypatch):
    w,b,g,c,config=setup_case(clients,monkeypatch)
    assert w.get('/api/notifications').json()['unread']>=1
    assert b.post('/api/support/cases/'+c['id']+'/replies',json={'body':'Not staff','send_email':True}).status_code==404
    assert w.post('/api/support/cases/'+c['id']+'/replies',json={'body':'Here is your support response.','send_email':True}).status_code==200
    with SessionLocal() as db:
        mail=db.scalar(select(SupportMail).where(SupportMail.recipient=='beta@storylens.test'))
        content=db.get(SupportMailContent,mail.id)
        msg=message(mail,config,content.body)
        assert 'support@kathhaverse.org' in msg['From']
        assert 'Here is your support response.' in msg.get_content()
        assert msg['Message-ID']
    assert g.post('/api/support/guest/check',json=c).json()['replies'][-1]['body']=='Here is your support response.'

def test_reset_link_private_single_use_and_revokes_sessions(clients,monkeypatch):
    w,b,g,c,config=setup_case(clients,monkeypatch)
    url='/api/admin/ops/cases/'+c['id']+'/password-reset'
    assert b.post(url).status_code==403
    result=w.post(url);assert result.status_code==200
    assert 'token' not in result.text
    with SessionLocal() as db:
        row=db.scalar(select(SupportMail).where(SupportMail.recipient=='beta@storylens.test'))
        text=db.get(SupportMailContent,row.id).body
        token=text.split('#token=')[1].split('\n')[0]
        assert token not in str(w.get('/api/support/cases/'+c['id']).json())
        assert token not in db.scalar(select(PasswordRecovery)).token_hash
    assert w.post(url).status_code==429
    assert g.post('/api/auth/password-reset',json={'token':token,'password':'new-secret-password'}).status_code==200
    assert g.post('/api/auth/password-reset',json={'token':token,'password':'other-secret-password'}).status_code==400
    assert b.get('/api/auth/me').status_code==401
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email=='beta@storylens.test'))
        assert password_ok('new-secret-password',user.password_hash)

def test_expired_reset_and_mail_disabled(clients,monkeypatch):
    w,b,g,c,config=setup_case(clients,monkeypatch)
    assert w.post('/api/admin/ops/cases/'+c['id']+'/password-reset').status_code==200
    with SessionLocal() as db:
        row=db.scalar(select(SupportMail).where(SupportMail.recipient=='beta@storylens.test'))
        token=db.get(SupportMailContent,row.id).body.split('#token=')[1].split('\n')[0]
        db.scalar(select(PasswordRecovery)).expires=time.time()-1;db.commit()
    assert g.post('/api/auth/password-reset',json={'token':token,'password':'new-secret-password'}).status_code==400
    monkeypatch.setattr('app.operations.support_settings',lambda:None)
    assert w.post('/api/support/cases/'+c['id']+'/replies',json={'body':'Cannot send','send_email':True}).status_code==503
    assert len(g.post('/api/support/guest/check',json=c).json()['replies'])==1

def test_worker_sends_from_support_and_clears_queued_content(clients,monkeypatch):
    from app import support_delivery,welcome_email
    w,b,g,c,config=setup_case(clients,monkeypatch)
    monkeypatch.setattr(welcome_email,'settings',lambda:{**config,'sender':'welcome@kathhaverse.org'})
    delivered=[]
    monkeypatch.setattr(welcome_email,'deliver',lambda msg,cfg:delivered.append((msg,cfg)))
    assert w.post('/api/support/cases/'+c['id']+'/replies',json={'body':'Support email contents','send_email':True}).status_code==200
    while support_delivery.process_one():pass
    assert all(cfg['sender']=='support@kathhaverse.org' for _,cfg in delivered)
    assert any('Support email contents' in msg.get_content() for msg,_ in delivered)
    with SessionLocal() as db:
        assert db.scalar(select(SupportMailContent)) is None
        assert all(m.status=='sent' for m in db.scalars(select(SupportMail)))
