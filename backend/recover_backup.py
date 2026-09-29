"""Validate a backup and recover it into a NEW database file; never overwrite."""
import argparse
import sqlite3
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('backup',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
source=args.backup.resolve();target=args.output.resolve()
if not source.is_file():parser.error('Backup does not exist')
if target.exists():parser.error('Output already exists; choose a new filename')
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src:
    if src.execute('pragma integrity_check').fetchone()[0]!='ok':parser.error('Backup failed integrity check')
    with sqlite3.connect(target) as dest:
        src.backup(dest)
        if dest.execute('pragma integrity_check').fetchone()[0]!='ok':raise RuntimeError('Recovered copy failed integrity check')
print('Recovered copy created:',target)
print('Stop Storylens before changing DATABASE_URL to this recovered copy. Keep the original database.')
