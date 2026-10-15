import os, sys, tempfile, sqlite3, time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
qa=Path(tempfile.mkdtemp(prefix='yc-qa-v54-'))
os.environ['YICHEN_DATA_DIR']=str(qa)
os.environ['YICHEN_CONFIG_FILE']=str(qa/'none.env')
for key in list(os.environ):
 if key.startswith('YICHEN_SMTP_') or key in ('YICHEN_NOTIFY_EMAIL','AMAP_JS_KEY','AMAP_SECURITY_CODE','YICHEN_PUBLIC_ORIGIN'):os.environ.pop(key)
sys.path.insert(0,str(root))
from webapp import create_app,service
with sqlite3.connect(service.DB) as db:
 db.execute('INSERT INTO users VALUES(?,?,?,?,?)',('qa-operator','qa-operator@example.com','验收管理员（虚构）',service.password_hash('QA-only-password-54'),int(time.time())))
 db.execute('INSERT INTO operators VALUES(?,?)',('qa-operator',int(time.time())))
print('ISOLATED QA DATA: '+str(qa),flush=True)
create_app(start_mail=False).run(host='127.0.0.1',port=8767,threaded=True,use_reloader=False)
