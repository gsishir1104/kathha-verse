"""Server-side Google authorization code flow with browser binding and PKCE."""
import base64
import hashlib
import os
import secrets
import time
from urllib.parse import urlencode, urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import String, Float, ForeignKey, select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, Session
from .db import Base, User, get_db
from .security import PRODUCTION, digest, password_hash, start_session, ensure_active
from .welcome_email import WelcomeEmail

router = APIRouter(prefix='/api/auth/google')
COOKIE = 'storylens_google_flow'

class GoogleIdentity(Base):
    __tablename__ = 'google_identities'
    subject: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)

class GoogleFlow(Base):
    __tablename__ = 'google_flows'
    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    browser_hash: Mapped[str] = mapped_column(String(64))
    verifier: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20))
    expires: Mapped[float] = mapped_column(Float)

def config():
    client = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    secret = os.getenv('GOOGLE_CLIENT_SECRET', '').strip()
    url = os.getenv('PUBLIC_APP_URL', '').rstrip('/')
    parts = urlsplit(url)
    local = not PRODUCTION and parts.hostname in ('127.0.0.1', 'localhost')
    if not client or not secret or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
        return None
    if parts.scheme != 'https' and not (local and parts.scheme == 'http'):
        return None
    return client, secret, url + '/api/auth/google/callback'

@router.get('/status')
def status():
    return {'enabled': config() is not None}

@router.get('/start')
def begin(request: Request, role: str = 'beta', db: Session = Depends(get_db)):
    from .main import throttle
    throttle(request)
    settings = config()
    if not settings: raise HTTPException(503, 'Google sign-in is not set up yet.')
    if role not in ('writer', 'beta', 'reader'): raise HTTPException(422, 'Choose a valid role')
    state, browser, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    db.execute(delete(GoogleFlow).where(GoogleFlow.expires < time.time()))
    db.add(GoogleFlow(state_hash=digest(state), browser_hash=digest(browser), verifier=verifier, role=role, expires=time.time()+600))
    db.commit()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    query = urlencode(dict(client_id=settings[0], redirect_uri=settings[2], response_type='code', scope='openid email profile', state=state, code_challenge=challenge, code_challenge_method='S256', prompt='select_account'))
    response = RedirectResponse('https://accounts.google.com/o/oauth2/v2/auth?' + query, status_code=303)
    response.set_cookie(COOKIE, browser, max_age=600, httponly=True, secure=PRODUCTION, samesite='lax', path='/api/auth/google')
    return response

def google_profile(code, verifier, settings):
    # Only trust identity returned by Google's authenticated HTTPS userinfo endpoint.
    # Do not decode or trust an unverified ID token or a browser-supplied email.
    with httpx.Client(timeout=15) as client:
        token = client.post('https://oauth2.googleapis.com/token', data=dict(code=code, client_id=settings[0], client_secret=settings[1], redirect_uri=settings[2], grant_type='authorization_code', code_verifier=verifier))
        token.raise_for_status()
        access = token.json()['access_token']
        profile = client.get('https://openidconnect.googleapis.com/v1/userinfo', headers={'Authorization': 'Bearer ' + access})
        profile.raise_for_status()
        return profile.json()

@router.get('/callback')
def callback(request: Request, state: str = '', code: str = '', error: str = '', db: Session = Depends(get_db)):
    def failure(reason):
        response = RedirectResponse('/?google_error=' + reason, status_code=303)
        response.delete_cookie(COOKIE, path='/api/auth/google')
        return response
    settings = config()
    flow = db.get(GoogleFlow, digest(state))
    if not settings or not flow or flow.expires < time.time() or not secrets.compare_digest(flow.browser_hash, digest(request.cookies.get(COOKIE, ''))):
        return failure('expired')
    role, verifier = flow.role, flow.verifier
    claimed = db.execute(delete(GoogleFlow).where(GoogleFlow.state_hash == flow.state_hash))
    db.commit()
    if claimed.rowcount != 1: return failure('expired')
    if error or not code: return failure('cancelled')
    try:
        profile = google_profile(code, verifier, settings)
        subject = profile.get('sub')
        email = profile.get('email', '').strip().lower()
        if profile.get('email_verified') is not True or not isinstance(subject, str) or not subject or len(subject) > 255 or len(email) > 254 or email.count('@') != 1 or any(c in email for c in '\r\n<> ,'):
            return failure('unverified')
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        return failure('unavailable')
    identity = db.get(GoogleIdentity, subject)
    if identity:
        user = db.get(User, identity.user_id)
    else:
        # Do not silently merge an existing password account based on email alone.
        if db.scalar(select(User).where(User.email == email)):
            return failure('existing')
        user = User(email=email, name=str(profile.get('name') or 'Kathha Verse reader')[:100], role=role, password_hash=password_hash(secrets.token_urlsafe(48)))
        db.add(user)
        try:
            db.flush()
            db.add_all([GoogleIdentity(subject=subject, user_id=user.id), WelcomeEmail(user_id=user.id)])
            db.commit()
        except IntegrityError:
            db.rollback()
            return failure('existing')
    try:
        ensure_active(db, user)
    except HTTPException:
        return failure('suspended')
    response = RedirectResponse('/', status_code=303)
    response.delete_cookie(COOKIE, path='/api/auth/google')
    start_session(db, user, response)
    return response
