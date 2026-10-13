#!/usr/bin/env python3
"""Local operator inbox. Run on the server host; no public admin endpoint."""
import argparse,json,os,sqlite3
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('action',choices=['inbox','reviews','approve-review','reject-review','grant-admin','revoke-admin']);p.add_argument('--id');p.add_argument('--email');p.add_argument('--data-dir',default=os.environ.get('YICHEN_DATA_DIR',str(Path(__file__).parent/'data')));a=p.parse_args()
dbfile=Path(a.data_dir)/'accounts.sqlite3'
if not dbfile.exists():p.error('Data directory not found; use the same YICHEN_DATA_DIR as server.py.')
with sqlite3.connect(dbfile) as db:
 if a.action in ('grant-admin','revoke-admin'):
  if not a.email:p.error('--email is required')
  import operator_backend,time
  operator_backend.initialize(dbfile)
  user=db.execute('SELECT id FROM users WHERE email=?',(a.email.strip().lower(),)).fetchone()
  if not user:p.error('Register this account first.')
  if a.action=='grant-admin':db.execute('INSERT OR IGNORE INTO operators VALUES(?,?)',(user[0],int(time.time())))
  else:db.execute('DELETE FROM operators WHERE user_id=?',(user[0],))
  print('Administrator permission updated.')
 elif a.action=='inbox':
  for row in db.execute('SELECT body FROM inquiries ORDER BY created DESC LIMIT 100'):print(json.dumps(json.loads(row[0]),ensure_ascii=False,indent=2))
 elif a.action=='reviews':
  for row in db.execute('SELECT id,car,rating,content,status,created FROM reviews ORDER BY created DESC LIMIT 100'):print(json.dumps(dict(zip(['id','car','rating','content','status','created'],row)),ensure_ascii=False,indent=2))
 else:
  if not a.id:p.error('--id is required')
  changed=db.execute('UPDATE reviews SET status=? WHERE id=?',('approved' if a.action=='approve-review' else 'rejected',a.id)).rowcount
  print('Updated' if changed else 'Review not found')
