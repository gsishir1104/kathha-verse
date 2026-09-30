"""Durable welcome-email outbox. Credentials stay on the server."""
import logging
import os
import smtplib
import ssl
import threading
import time
import httpx
from email.message import EmailMessage
from email.utils import formataddr, formatdate
from html import escape
from urllib.parse import urlsplit
from sqlalchemy import String, Integer, Float, ForeignKey, select, update
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, SessionLocal, User

log = logging.getLogger(__name__)

class WelcomeEmail(Base):
    __tablename__ = 'welcome_emails'
    # One welcome per newly registered account, committed with that account.
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt: Mapped[float] = mapped_column(Float, default=0)
    last_error: Mapped[str] = mapped_column(String(80), default='')
    sent_at: Mapped[float | None] = mapped_column(Float, nullable=True)

def settings():
    if os.getenv('MAIL_ENABLED', 'false').lower() != 'true':
        return None
    host = os.getenv('SMTP_HOST', '').strip()
    sender = os.getenv('MAIL_FROM_ADDRESS', '').strip()
    username = os.getenv('SMTP_USERNAME', '')
    password = os.getenv('SMTP_PASSWORD', '')
    security = os.getenv('SMTP_SECURITY', 'starttls').lower()
    url = os.getenv('PUBLIC_APP_URL', '').rstrip('/')
    parts = urlsplit(url)
    local = os.getenv('APP_ENV') != 'production' and parts.hostname in ('localhost', '127.0.0.1')
    if (not host or not username or not password or security not in ('starttls', 'ssl')
        or sender.count('@') != 1 or any(c in sender for c in '\r\n<> ,')
        or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment
        or not (parts.scheme == 'https' or (local and parts.scheme == 'http'))):
        raise ValueError('Invalid welcome email configuration')
    reply_to = os.getenv('SUPPORT_EMAIL', '').strip()
    if reply_to and (reply_to.count('@') != 1 or any(c in reply_to for c in '\r\n<> ,')):
        raise ValueError('Invalid support email')
    port = int(os.getenv('SMTP_PORT', '465' if security == 'ssl' else '587'))
    if not 1 <= port <= 65535: raise ValueError('Invalid SMTP port')
    return dict(reply_to=reply_to, host=host, sender=sender, username=username, password=password, security=security, port=port, url=url)

def message(name, recipient, role, user_id, config):
    tip = {
        'writer': 'Create your story, add a chapter, and review its Story Universe before inviting beta readers.',
        'beta': 'Complete your beta-reader profile and check your invitations. Once a writer releases a chapter, you can read it and share your perspective.',
        'reader': 'Your account is ready. Public story discovery is still being prepared; published stories will appear when it becomes available.',
    }[role]
    greeting = name or 'there'
    msg = EmailMessage()
    msg['Subject'] = 'Welcome to Kathha Verse'
    msg['From'] = formataddr(('Kathha Verse', config['sender']))
    msg['To'] = recipient
    if config.get('reply_to'): msg['Reply-To'] = formataddr(('Kathha Verse Support', config['reply_to']))
    msg['Date'] = formatdate(localtime=False)
    msg['Message-ID'] = f'<welcome-{user_id}@{config["sender"].split("@")[1]}>'
    msg.set_content(f'Hi {greeting},\n\nWelcome to Kathha Verse! Your account is ready.\n\n{tip}\n\nOpen Kathha Verse: {config["url"]}\n\nAI supports the process. Real readers bring the perspective.\n\nThe Kathha Verse team\n\nYou received this welcome because an account was created with this email address. If that was not you, you can ignore this message.\n')
    msg.add_alternative(f'''<!doctype html><html><body style="margin:0;background:#f4f6fb;font-family:Arial,sans-serif;color:#1c2941"><main style="max-width:560px;margin:32px auto;padding:32px;background:#fff;border-radius:12px"><p style="font-size:24px;font-weight:bold;color:#555fc3">Kathha Verse.</p><h1 style="font-size:26px">Welcome to your next chapter.</h1><p>Hi {escape(greeting)},</p><p>Your Kathha Verse account is ready.</p><p style="line-height:1.7">{escape(tip)}</p><p style="margin:28px 0"><a href="{escape(config['url'], quote=True)}" style="display:inline-block;padding:14px 22px;background:#555fc3;color:white;text-decoration:none;border-radius:7px">Open Kathha Verse</a></p><p style="color:#647089">AI supports the process. Real readers bring the perspective.</p><p>The Kathha Verse team</p><hr style="border:0;border-top:1px solid #e3e7ef"><p style="font-size:12px;color:#647089">You received this welcome because an account was created with this email address. If that was not you, you can ignore this message.</p></main></body></html>''', subtype='html')
    return msg

def deliver(msg, config):
    # Some hosted networks time out on outbound SMTP ports. Resend also offers
    # HTTPS delivery, so use it when the configured credentials belong to
    # Resend while retaining SMTP for other providers and local development.
    if config['host'].lower() == 'smtp.resend.com' and config['username'] == 'resend':
        plain = msg.get_body(preferencelist=('plain',))
        html = msg.get_body(preferencelist=('html',))
        payload = {
            'from': str(msg['From']),
            'to': [str(msg['To'])],
            'subject': str(msg['Subject']),
            'text': plain.get_content() if plain else '',
            'html': html.get_content() if html else '',
        }
        if msg.get('Reply-To'):
            payload['reply_to'] = str(msg['Reply-To'])
        message_id = str(msg.get('Message-ID', '')).strip('<>')
        response = httpx.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f"Bearer {config['password']}",
                'Idempotency-Key': message_id,
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        return
    context = ssl.create_default_context()
    if config['security'] == 'ssl':
        client = smtplib.SMTP_SSL(config['host'], config['port'], timeout=15, context=context)
    else:
        client = smtplib.SMTP(config['host'], config['port'], timeout=15)
    accepted = False
    try:
        with client:
            if config['security'] == 'starttls':
                client.ehlo()
                client.starttls(context=context)
                client.ehlo()
            client.login(config['username'], config['password'])
            refused = client.send_message(msg, from_addr=config['sender'], to_addrs=[str(msg['To'])])
            if refused: raise smtplib.SMTPRecipientsRefused(refused)
            accepted = True
    except (smtplib.SMTPException, OSError):
        # A failed QUIT after successful DATA must not enqueue a duplicate.
        if not accepted: raise

def process_one():
    config = settings()
    if not config: return False
    now = time.time()
    with SessionLocal() as db:
        # A crashed send has an uncertain outcome; avoid automatically duplicating it.
        db.execute(update(WelcomeEmail).where(WelcomeEmail.status == 'sending', WelcomeEmail.next_attempt < now).values(status='uncertain', last_error='Interrupted delivery; inspect provider logs'))
        db.commit()
        item = db.scalar(select(WelcomeEmail).where(WelcomeEmail.status == 'pending', WelcomeEmail.next_attempt <= now).order_by(WelcomeEmail.next_attempt).limit(1))
        if not item: return False
        user_id = item.user_id
        claimed = db.execute(update(WelcomeEmail).where(WelcomeEmail.user_id == user_id, WelcomeEmail.status == 'pending').values(status='sending', attempts=WelcomeEmail.attempts + 1, next_attempt=now + 600))
        if claimed.rowcount != 1: db.rollback(); return True
        db.commit()
        user = db.get(User, user_id)
        name, email, role = user.name, user.email, user.role
    try:
        deliver(message(name, email, role, user_id, config), config)
    except Exception as error:
        # Never log provider error bodies, credentials, email addresses or message content.
        with SessionLocal() as db:
            item = db.get(WelcomeEmail, user_id)
            item.last_error = type(error).__name__[:80]
            # Disconnect/timeouts may happen after acceptance: operator review instead of duplicates.
            uncertain = (isinstance(error, (smtplib.SMTPServerDisconnected, httpx.TimeoutException))
                         or (isinstance(error, OSError) and not isinstance(error, smtplib.SMTPException)))
            item.status = 'uncertain' if uncertain else ('failed' if item.attempts >= 5 else 'pending')
            item.next_attempt = time.time() + min(3600, 60 * 2 ** item.attempts)
            db.commit()
        log.warning('Welcome delivery unsuccessful (%s)', type(error).__name__)
    else:
        with SessionLocal() as db:
            db.execute(update(WelcomeEmail).where(WelcomeEmail.user_id == user_id).values(status='sent', sent_at=time.time(), last_error=''))
            db.commit()
    return True

def start_worker():
    stop = threading.Event()
    def run():
        while not stop.is_set():
            try:
                from .support_delivery import process_one as process_support
                worked = process_one()
                worked = process_support() or worked
            except Exception as error:
                log.warning('Welcome email worker unavailable (%s)', type(error).__name__)
                worked = False
            stop.wait(1 if worked else 30)
    if os.getenv('MAIL_ENABLED', 'false').lower() != 'true': return stop, None
    thread = threading.Thread(target=run, name='welcome-emails', daemon=True)
    thread.start()
    return stop, thread
