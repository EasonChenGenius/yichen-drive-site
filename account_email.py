"""Email ownership challenges. No plaintext codes in SQLite, logs, URLs or API replies."""
import hashlib,hmac,os,re,secrets,sqlite3,time
from pathlib import Path
from email.message import EmailMessage
from email.utils import parseaddr
import inquiry_mail
from concurrent.futures import ThreadPoolExecutor
DELIVERY_POOL=ThreadPoolExecutor(max_workers=2,thread_name_prefix="account-email")
TTL=600
COOLDOWN=60
MAX_ATTEMPTS=5
GENERIC='如果该邮箱符合条件，系统将发送验证码。请检查收件箱及垃圾邮件；未收到可稍后重试。旧账号需先登录完成邮箱验证。'
class ChallengeError(Exception):
    def __init__(self,message,status=400):self.message=message;self.status=status

def initialize(path):
    with sqlite3.connect(path) as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS verified_emails(user_id TEXT PRIMARY KEY,email TEXT NOT NULL,verified_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS email_challenges(id TEXT PRIMARY KEY,email TEXT NOT NULL,purpose TEXT NOT NULL,user_id TEXT,code_hash TEXT NOT NULL,created INTEGER NOT NULL,expires INTEGER NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL,ip_hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS email_challenge_recipient ON email_challenges(email,created);
        CREATE INDEX IF NOT EXISTS email_challenge_ip ON email_challenges(ip_hash,created);''')

def mail_ready():return all(os.environ.get(k) for k in ('YICHEN_SMTP_HOST','YICHEN_SMTP_USER','YICHEN_SMTP_PASSWORD'))
def normalize_email(value):
    if not isinstance(value,str):raise ChallengeError('请填写有效邮箱。')
    value=value.strip().lower()
    if any(char in value for char in ',;<>()[\\]\"'):raise ChallengeError('请填写单个有效邮箱，不要包含显示名或多个收件人。')
    name,address=parseaddr(value)
    if name or address!=value:raise ChallengeError('请填写单个有效邮箱。')
    if len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise ChallengeError('请填写有效邮箱。')
    return value

def secret(path):
    supplied=os.environ.get('YICHEN_AUTH_SECRET','')
    if supplied:
        if len(supplied)<32:raise ChallengeError('账户验证服务配置不完整。',503)
        return supplied.encode()
    target=Path(path).parent/'auth-challenge.key'
    try:
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(secrets.token_bytes(48))
    except FileExistsError:pass
    value=target.read_bytes()
    if len(value)<32:raise ChallengeError('账户验证服务配置不完整。',503)
    return value

def digest(key,value):return hmac.new(key,value.encode(),hashlib.sha256).hexdigest()
def deliver_code(email,code,purpose):
    label={'register':'创建账户','verify':'验证邮箱','reset':'重设密码'}[purpose]
    msg=EmailMessage();msg['Subject']='YICHEN Drive · '+label+'验证码';msg['From']=os.environ['YICHEN_SMTP_USER'];msg['To']=email
    msg.set_content(f'你正在申请{label}。\n\n验证码：{code}\n10分钟内有效，仅可使用一次。请勿向他人提供验证码。\n\n如果不是你本人操作，请忽略这封邮件。此邮件不表示租车预约或付款成立。')
    inquiry_mail.deliver_message(msg)

def request_code(path,email,purpose,ip,*,user_id=None):
    email=normalize_email(email)
    if purpose not in ('register','verify','reset'):raise ChallengeError('请选择有效的验证用途。')
    if not mail_ready():raise ChallengeError('邮件验证服务尚未配置，请稍后再试或联系经营者。',503)
    key=secret(path);now=int(time.time());identity=secrets.token_urlsafe(24);code=f'{secrets.randbelow(1000000):06d}';ip_hash=digest(key,ip)
    with sqlite3.connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM email_challenges WHERE created<?',(now-7*86400,))
        recent=db.execute('SELECT MAX(created),COUNT(*) FROM email_challenges WHERE email=? AND created>?',(email,now-86400)).fetchone()
        if recent[0] is not None and recent[0]>now-COOLDOWN:raise ChallengeError('请等待60秒后再获取验证码。',429)
        if recent[1]>=10 or db.execute('SELECT COUNT(*) FROM email_challenges WHERE ip_hash=? AND created>?',(ip_hash,now-3600)).fetchone()[0]>=20 or db.execute('SELECT COUNT(*) FROM email_challenges WHERE created>?',(now-86400,)).fetchone()[0]>=100:raise ChallengeError('验证码请求过于频繁，请稍后再试。',429)
        row=db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
        eligible=(purpose=='register' and not row) or (purpose=='verify' and row and row[0]==user_id) or (purpose=='reset' and row and db.execute('SELECT 1 FROM verified_emails WHERE user_id=? AND email=?',(row[0],email)).fetchone())
        bound=user_id if purpose=='verify' else row[0] if row else None
        db.execute('INSERT INTO email_challenges(id,email,purpose,user_id,code_hash,created,expires,status,ip_hash) VALUES(?,?,?,?,?,?,?,?,?)',(identity,email,purpose,bound,digest(key,identity+':'+code),now,now+TTL,'pending' if eligible else 'ineligible',ip_hash))
    dispatch_delivery(path,identity,email,code,purpose,bool(eligible))
    return {'challengeId':identity,'expiresIn':TTL,'retryAfter':COOLDOWN,'message':GENERIC}

def finish_delivery(path,identity,email,code,purpose,eligible):
    if not eligible:return
    with sqlite3.connect(path) as db:
        row=db.execute('SELECT status,expires FROM email_challenges WHERE id=?',(identity,)).fetchone()
    if not row or row[0]!='pending' or row[1]<=int(time.time()):return
    try:deliver_code(email,code,purpose)
    except Exception:
        with sqlite3.connect(path) as db:db.execute("UPDATE email_challenges SET status='failed' WHERE id=?",(identity,))
        return
    with sqlite3.connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT created,expires,status FROM email_challenges WHERE id=?',(identity,)).fetchone()
        if not row or row[2]!='pending':return
        newer=db.execute("SELECT 1 FROM email_challenges WHERE email=? AND purpose=? AND created>? AND status IN ('pending','sent')",(email,purpose,row[0])).fetchone()
        if newer or row[1]<=int(time.time()):
            db.execute("UPDATE email_challenges SET status='superseded' WHERE id=?",(identity,));return
        db.execute("UPDATE email_challenges SET status='superseded' WHERE email=? AND purpose=? AND status IN ('sent','pending') AND id<>? AND created<=?",(email,purpose,identity,row[0]))
        db.execute("UPDATE email_challenges SET status='sent' WHERE id=?",(identity,))

def dispatch_delivery(*args):
    # Identical response path for known and unknown accounts. SMTP runs off-request.
    DELIVERY_POOL.submit(finish_delivery,*args)

def consume(db,path,identity,code,email,purpose,*,user_id=None):
    """Caller owns an IMMEDIATE transaction; return an error rather than rollback attempts."""
    if not isinstance(identity,str) or len(identity)>100 or not isinstance(code,str) or not re.fullmatch(r'\d{6}',code):return '请输入6位有效验证码。'
    row=db.execute('SELECT email,purpose,user_id,code_hash,expires,attempts,status FROM email_challenges WHERE id=?',(identity,)).fetchone()
    if not row or row[0]!=email or row[1]!=purpose or (user_id is not None and row[2]!=user_id) or row[4]<=int(time.time()) or row[5]>=MAX_ATTEMPTS or row[6]!='sent':return '验证码无效、已过期或已使用，请重新获取。'
    db.execute('UPDATE email_challenges SET attempts=attempts+1 WHERE id=?',(identity,))
    if not hmac.compare_digest(row[3],digest(secret(path),identity+':'+code)):return '验证码不正确，请重试；最多可尝试5次。'
    db.execute("UPDATE email_challenges SET status='consumed' WHERE id=?",(identity,))
    return None
