"""Local, transaction-consistent backups. No browser endpoint exposes account data."""
import sqlite3
from contextlib import closing
import threading
import time
from pathlib import Path
from datetime import datetime, timezone
from .db import engine

_lock = threading.Lock()
_last = 0.0

def backup_database(force=False):
    global _last
    if engine.dialect.name != 'sqlite': return None
    source = Path(engine.url.database).resolve()
    if not source.exists(): return None
    with _lock:
        if not force and time.monotonic()-_last < 300: return None
        directory=source.parent/'backups'
        directory.mkdir(exist_ok=True)
        target=directory/('storylens-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
        with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(target)) as dest:
            src.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Backup integrity verification failed')
        _last=time.monotonic()
        return target
