from urllib.parse import urlsplit, parse_qs
from sqlalchemy import select, func
from test_vertical_slice import clients
from app import google_login as google
from app.db import SessionLocal, User
from app.welcome_email import WelcomeEmail


def configure(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID','test-client')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET','test-secret')
    monkeypatch.setenv('PUBLIC_APP_URL','http://127.0.0.1:8000')


def begin(client, role='writer'):
    response=client.get('/api/auth/google/start',params={'role':role},follow_redirects=False)
    assert response.status_code==303
    params=parse_qs(urlsplit(response.headers['location']).query)
    assert params['code_challenge_method']==['S256']
    assert params['scope']==['openid email profile']
    return params['state'][0]


def finish(client,state):
    return client.get('/api/auth/google/callback',params={'state':state,'code':'one-use-code'},follow_redirects=False)


def test_google_new_account_welcome_and_repeat_login(clients,monkeypatch):
    configure(monkeypatch);client=clients[2]
    monkeypatch.setattr(google,'google_profile',lambda *args:dict(sub='google-123',email='google@example.test',email_verified=True,name='Google Writer'))
    state=begin(client)
    assert finish(client,state).headers['location']=='/'
    user=client.get('/api/auth/me').json()
    assert user['role']=='writer'
    assert 'expired' in finish(client,state).headers['location']
    client.post('/api/auth/logout')
    assert finish(client,begin(client,'beta')).headers['location']=='/'
    assert client.get('/api/auth/me').json()['role']=='writer'
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(WelcomeEmail))==1


def test_google_state_bound_to_browser(clients,monkeypatch):
    configure(monkeypatch);state=begin(clients[2])
    monkeypatch.setattr(google,'google_profile',lambda *args: (_ for _ in ()).throw(AssertionError('must not contact Google')))
    assert 'expired' in finish(clients[1],state).headers['location']


def test_google_rejects_unverified_and_existing_accounts(clients,monkeypatch):
    configure(monkeypatch);client=clients[2]
    monkeypatch.setattr(google,'google_profile',lambda *args:dict(sub='123',email='writer@storylens.test',email_verified=False))
    assert 'unverified' in finish(client,begin(client)).headers['location']
    monkeypatch.setattr(google,'google_profile',lambda *args:dict(sub='123',email='writer@storylens.test',email_verified=True))
    assert 'existing' in finish(client,begin(client)).headers['location']
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(google.GoogleIdentity))==0


def test_google_disabled_invalid_role_and_cancel(clients,monkeypatch):
    client=clients[2];monkeypatch.delenv('GOOGLE_CLIENT_ID',raising=False)
    assert client.get('/api/auth/google/status').json()=={'enabled':False}
    assert client.get('/api/auth/google/start').status_code==503
    configure(monkeypatch)
    assert client.get('/api/auth/google/start?role=admin').status_code==422
    state=begin(client)
    response=client.get('/api/auth/google/callback',params={'state':state,'error':'access_denied'},follow_redirects=False)
    assert 'cancelled' in response.headers['location']


def test_expired_flow_and_provider_failure(clients,monkeypatch):
    import httpx
    configure(monkeypatch);client=clients[2];state=begin(client)
    with SessionLocal() as db:
        flow=db.get(google.GoogleFlow,google.digest(state));flow.expires=0;db.commit()
    assert 'expired' in finish(client,state).headers['location']
    def fail(*args):raise httpx.ConnectError('provider unavailable')
    monkeypatch.setattr(google,'google_profile',fail)
    assert 'unavailable' in finish(client,begin(client)).headers['location']
    with SessionLocal() as db:assert db.scalar(select(func.count()).select_from(WelcomeEmail))==0
