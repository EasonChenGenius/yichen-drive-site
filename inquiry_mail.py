"""Durable enquiry notification outbox. Credentials stay in server environment."""
import os,sqlite3,time,threading,smtplib,ssl,re,tempfile
from pathlib import Path
from email.message import EmailMessage
from urllib.parse import urlsplit

def initialize(path):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS inquiry_mail(id TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'pending',attempts INTEGER NOT NULL DEFAULT 0,next_attempt INTEGER NOT NULL DEFAULT 0,locked_at INTEGER NOT NULL DEFAULT 0,sent_at INTEGER,last_error TEXT NOT NULL DEFAULT '')")
def configured():
    return all(os.environ.get(k) for k in ('YICHEN_SMTP_HOST','YICHEN_SMTP_USER','YICHEN_SMTP_PASSWORD','YICHEN_NOTIFY_EMAIL'))
def enqueue(db,identity):db.execute('INSERT OR IGNORE INTO inquiry_mail(id) VALUES(?)',(identity,))
def status(path):
    with sqlite3.connect(path) as db:
        counts=dict(db.execute('SELECT status,COUNT(*) FROM inquiry_mail GROUP BY status'))
    return {'configured':configured(),'pending':counts.get('pending',0)+counts.get('sending',0),'sent':counts.get('sent',0)}
def send(identity):
    msg=EmailMessage();msg['Subject']=('YC 邮件提醒测试 · ' if identity.startswith('YC-MAIL-TEST-') else 'YC 新的用车需求 · ')+identity;msg['From']=os.environ['YICHEN_SMTP_USER'];msg['To']=os.environ['YICHEN_NOTIFY_EMAIL'];msg['Message-ID']='<'+identity+'@yichen-notification.local>'
    origin=os.environ.get('YICHEN_PUBLIC_ORIGIN','').rstrip('/');parts=urlsplit(origin)
    link=origin+'/operator.html' if parts.scheme=='https' and parts.netloc else '登录管理后台查看详情。'
    msg.set_content(('这是一封邮件提醒测试，不是客户需求。编号：' if identity.startswith('YC-MAIL-TEST-') else '有一条新的用车需求，编号：')+identity+'\n\n'+link+'\n\n请在后台核对客户联系方式、行程和车辆。此邮件不表示预约已成立。')
    port=int(os.environ.get('YICHEN_SMTP_PORT','465'));host=os.environ['YICHEN_SMTP_HOST'];context=ssl.create_default_context()
    if port==465:
        with smtplib.SMTP_SSL(host,port,timeout=15,context=context) as smtp:
            smtp.login(os.environ['YICHEN_SMTP_USER'],os.environ['YICHEN_SMTP_PASSWORD']);smtp.send_message(msg)
    elif port==587:
        with smtplib.SMTP(host,port,timeout=15) as smtp:
            smtp.ehlo();smtp.starttls(context=context);smtp.ehlo();smtp.login(os.environ['YICHEN_SMTP_USER'],os.environ['YICHEN_SMTP_PASSWORD']);smtp.send_message(msg)
    else:raise ValueError('Encrypted SMTP port required')
def process_one(path,sender=send):
    now=int(time.time())
    with sqlite3.connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute("UPDATE inquiry_mail SET status='pending',locked_at=0 WHERE status='sending' AND locked_at<?",(now-300,))
        row=db.execute("SELECT id,attempts FROM inquiry_mail WHERE status='pending' AND next_attempt<=? ORDER BY rowid LIMIT 1",(now,)).fetchone()
        if not row:return False
        identity,attempts=row;db.execute("UPDATE inquiry_mail SET status='sending',locked_at=? WHERE id=?",(now,identity));db.commit()
    try:sender(identity)
    except Exception as error:
        # Do not persist exception messages: some SMTP errors include credentials.
        kind=type(error).__name__
        with sqlite3.connect(path) as db:db.execute("UPDATE inquiry_mail SET status='pending',attempts=?,next_attempt=?,locked_at=0,last_error=? WHERE id=?",(attempts+1,now+min(3600,30*2**min(attempts,7)),kind,identity))
    else:
        with sqlite3.connect(path) as db:db.execute("UPDATE inquiry_mail SET status='sent',sent_at=?,locked_at=0,last_error='' WHERE id=?",(int(time.time()),identity))
    return True
WORKER=None
WORKER_LOCK=threading.Lock()
def configure(root,secret,*,config_path=None):
    if not isinstance(secret,str) or not re.fullmatch(r'[A-Za-z0-9]{16}',secret.strip()):raise ValueError('QQ authorization code must contain 16 characters')
    values={'YICHEN_SMTP_HOST':'smtp.qq.com','YICHEN_SMTP_PORT':'465','YICHEN_SMTP_USER':'2712723487@qq.com','YICHEN_SMTP_PASSWORD':secret.strip(),'YICHEN_NOTIFY_EMAIL':'2712723487@qq.com'}
    path=Path(config_path).resolve() if config_path else Path(root)/'.env';lines=path.read_text().splitlines() if path.exists() else []
    lines=[line for line in lines if line.split('=',1)[0].strip() not in values]
    lines.extend(k+'='+v for k,v in values.items())
    fd,name=tempfile.mkstemp(prefix='.mail-config-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write('\n'.join(lines)+'\n')
        os.chmod(name,0o600);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
    os.environ.update(values)
def start(path):
    global WORKER
    if not configured():return None
    with WORKER_LOCK:
        if WORKER and WORKER.is_alive():return WORKER
        def run():
            while True:
                try:busy=process_one(path)
                except Exception:busy=False
                time.sleep(1 if busy else 10)
        WORKER=threading.Thread(target=run,daemon=True,name='inquiry-mail');WORKER.start();return WORKER
