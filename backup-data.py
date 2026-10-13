#!/usr/bin/env python3
"""Private, consistent SQLite backup. Never package backups with the public site."""
import argparse,os,sqlite3,secrets
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser(description='Backup the private YC account and enquiry database.')
p.add_argument('--data-dir',required=True);p.add_argument('--backup-dir',required=True)
a=p.parse_args();source=Path(a.data_dir).resolve()/'accounts.sqlite3';folder=Path(a.backup_dir).resolve()
if not source.is_file():p.error('Database not found; no backup created.')
site=Path(__file__).resolve().parent
if folder==site/'dist' or site/'dist' in folder.parents:p.error('Backup directory must be outside public dist/.')
folder.mkdir(parents=True,exist_ok=True);os.chmod(folder,0o700)
name='accounts-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3)+'.sqlite3';target=folder/name
fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
try:
 with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(target) as dst:
  src.backup(dst)
  if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Backup integrity check failed')
except Exception:
 target.unlink(missing_ok=True);raise
print('Private backup created and integrity verified: '+str(target))
