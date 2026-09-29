import os, secrets, hashlib, hmac, time
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from .db import User, SessionToken, get_db, AccountControl, UserPresence, UserActivity

PRODUCTION = os.getenv('APP_ENV') == 'production'
DEMO_MODE = os.getenv('DEMO_MODE','false').lower() == 'true'
if PRODUCTION and DEMO_MODE: raise RuntimeError('Demo mode cannot run in production')
def password_hash(value):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(value.encode(), salt=salt, n=16384, r=8, p=1)
    return salt.hex() + ':' + digest.hex()
def password_ok(value, stored):
    salt, digest = stored.split(':')
    actual = hashlib.scrypt(value.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(actual.hex(), digest)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def is_admin(user):
    return any(user.id in {v.strip() for v in os.getenv(key,'').split(',') if v.strip()} for key in ('ADMIN_USER_IDS','STAFF_SUPPORT_IDS','STAFF_MODERATOR_IDS','STAFF_TECHNICAL_IDS'))

def ensure_active(db, user):
    control = db.get(AccountControl, user.id)
    if control and control.suspended: raise HTTPException(403,'This account is suspended. Contact support.')

def start_session(db, user, response):
    ensure_active(db, user)
    token = secrets.token_urlsafe(32)
    db.add(SessionToken(token_hash=digest(token), user_id=user.id, expires=time.time()+60*60*24*7))
    presence=db.get(UserPresence,user.id)
    if not presence: presence=UserPresence(user_id=user.id);db.add(presence)
    presence.last_active=time.time();presence.last_login=time.time()
    db.add(UserActivity(user_id=user.id,action='Signed in'))
    db.commit()
    response.set_cookie('storylens_session', token, httponly=True, secure=PRODUCTION, samesite='strict', max_age=604800, path='/')
def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('storylens_session','')
    session = db.get(SessionToken, digest(token))
    if not session or session.expires < time.time(): raise HTTPException(401,'Please sign in')
    user = db.get(User, session.user_id)
    if not user: raise HTTPException(401,'Please sign in')
    ensure_active(db, user)
    if is_admin(user) and not (request.url.path.startswith('/api/admin/') or request.url.path.startswith('/api/auth/') or request.url.path.startswith('/api/notifications') or request.url.path.startswith('/api/support/')):
        raise HTTPException(403,'Use the administrator workspace for this account')
    request.state.activity_user_id=user.id
    return user
def writer(user: User = Depends(current_user)):
    if user.role != 'writer': raise HTTPException(403,'Writer access required')
    return user
def user_dict(user): return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role, 'preferences': user.preferences, 'is_admin': is_admin(user), 'staff_role': next((role for role,key in [('owner','ADMIN_USER_IDS'),('support','STAFF_SUPPORT_IDS'),('moderator','STAFF_MODERATOR_IDS'),('technical','STAFF_TECHNICAL_IDS')] if user.id in {v.strip() for v in os.getenv(key,'').split(',') if v.strip()}),None)}
