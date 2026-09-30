import smtplib
import httpx
from sqlalchemy import select, func
from test_vertical_slice import clients
from app.db import SessionLocal
from app import welcome_email as mail

def signup(client):
    response=client.post('/api/auth/register',json={'name':'New Writer','email':'new@example.test','password':'long-password-123','role':'writer'})
    assert response.status_code==200,response.text
    return response.json()['id']

def configure(monkeypatch):
    for k,v in {'MAIL_ENABLED':'true','SMTP_HOST':'smtp.example.test','SMTP_USERNAME':'smtp-user','SMTP_PASSWORD':'secret-test-only','MAIL_FROM_ADDRESS':'hello@example.test','PUBLIC_APP_URL':'https://story.example.test','SMTP_SECURITY':'starttls','SMTP_PORT':'587'}.items():monkeypatch.setenv(k,v)

def test_signup_queues_once_not_login_or_demo(clients):
    w,b,x=clients;uid=signup(x)
    assert x.post('/api/auth/register',json={'name':'Duplicate','email':'new@example.test','password':'long-password-123','role':'writer'}).status_code==409
    assert x.post('/api/auth/login',json={'email':'new@example.test','password':'long-password-123'}).status_code==200
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(mail.WelcomeEmail))==1
        assert db.get(mail.WelcomeEmail,uid).status=='pending'
    assert mail.process_one() is False

def test_worker_sends_once_after_configuration(clients,monkeypatch):
    w,b,x=clients;uid=signup(x);configure(monkeypatch);sent=[]
    monkeypatch.setattr(mail,'deliver',lambda msg,config:sent.append(msg))
    assert mail.process_one() is True
    assert mail.process_one() is False
    assert len(sent)==1 and sent[0]['To']=='new@example.test'
    assert str(sent[0]['From'])=='Kathha Verse <hello@example.test>'
    assert 'Create your story' in sent[0].get_body(preferencelist=('plain',)).get_content()
    with SessionLocal() as db:assert db.get(mail.WelcomeEmail,uid).status=='sent'

def test_delivery_failure_does_not_remove_account_and_retries(clients,monkeypatch):
    w,b,x=clients;uid=signup(x);configure(monkeypatch)
    def fail(*args):raise smtplib.SMTPAuthenticationError(535,b'private provider detail')
    monkeypatch.setattr(mail,'deliver',fail)
    assert mail.process_one()
    assert x.get('/api/auth/me').json()['id']==uid
    with SessionLocal() as db:
        item=db.get(mail.WelcomeEmail,uid)
        assert item.status=='pending' and item.attempts==1 and item.next_attempt>0
        assert item.last_error=='SMTPAuthenticationError'
    assert mail.process_one() is False

def test_ambiguous_delivery_requires_review(clients,monkeypatch):
    w,b,x=clients;uid=signup(x);configure(monkeypatch)
    def fail(*args):raise smtplib.SMTPServerDisconnected('connection lost')
    monkeypatch.setattr(mail,'deliver',fail)
    mail.process_one()
    with SessionLocal() as db:assert db.get(mail.WelcomeEmail,uid).status=='uncertain'
    assert mail.process_one() is False

def test_email_html_escapes_names_and_role_content(monkeypatch):
    configure(monkeypatch)
    msg=mail.message('<script>alert(1)</script>','beta@example.test','beta','id',mail.settings())
    html=msg.get_body(preferencelist=('html',)).get_content()
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'beta-reader profile' in html
    assert 'https://story.example.test' in html
    reader=mail.message('Reader','reader@example.test','reader','id',mail.settings())
    assert 'still being prepared' in reader.get_body(preferencelist=('plain',)).get_content()

def test_smtp_requires_tls_before_login(monkeypatch):
    configure(monkeypatch);calls=[]
    class FakeSMTP:
        def __init__(self,*args,**kwargs):calls.append('connect')
        def __enter__(self):return self
        def __exit__(self,*args):raise smtplib.SMTPResponseException(500,b'QUIT failed after acceptance')
        def ehlo(self):calls.append('ehlo')
        def starttls(self,**kwargs):calls.append('tls')
        def login(self,*args):calls.append('login')
        def send_message(self,*args,**kwargs):calls.append('send');return {}
    monkeypatch.setattr(mail.smtplib,'SMTP',FakeSMTP)
    config=mail.settings();mail.deliver(mail.message('Name','name@example.test','writer','id',config),config)
    assert calls==['connect','ehlo','tls','ehlo','login','send']

def test_resend_credentials_use_https_api(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv('SMTP_HOST','smtp.resend.com')
    monkeypatch.setenv('SMTP_USERNAME','resend')
    monkeypatch.setenv('SUPPORT_EMAIL','support@example.test')
    calls=[]
    class Response:
        def raise_for_status(self):calls.append('status')
    def post(url,headers,json,timeout):
        calls.append((url,headers,json,timeout));return Response()
    monkeypatch.setattr(mail.httpx,'post',post)
    config=mail.settings()
    msg=mail.message('Name','name@example.test','writer','user-1',config)
    mail.deliver(msg,config)
    url,headers,payload,timeout=calls[0]
    assert url=='https://api.resend.com/emails' and timeout==15
    assert headers['Authorization']=='Bearer secret-test-only'
    assert headers['Idempotency-Key']=='welcome-user-1@example.test'
    assert payload['from']=='Kathha Verse <hello@example.test>'
    assert payload['to']==['name@example.test']
    assert payload['reply_to']=='Kathha Verse Support <support@example.test>'
    assert 'Create your story' in payload['text'] and '<html>' in payload['html']
    assert calls[1]=='status'

def test_resend_timeout_is_uncertain(clients,monkeypatch):
    w,b,x=clients;uid=signup(x);configure(monkeypatch)
    monkeypatch.setenv('SMTP_HOST','smtp.resend.com')
    monkeypatch.setenv('SMTP_USERNAME','resend')
    def timeout(*args,**kwargs):raise httpx.ReadTimeout('timed out')
    monkeypatch.setattr(mail.httpx,'post',timeout)
    assert mail.process_one()
    with SessionLocal() as db:
        assert db.get(mail.WelcomeEmail,uid).status=='uncertain'


def test_support_reply_address(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv('SUPPORT_EMAIL','support@example.test')
    msg=mail.message('Writer','writer@example.test','writer','id',mail.settings())
    assert str(msg['Reply-To'])=='Kathha Verse Support <support@example.test>'
