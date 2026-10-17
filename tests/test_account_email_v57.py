"""Isolated account ownership/recovery audit. No real SMTP, data, or account changes."""
import os,sys,tempfile,sqlite3,time,concurrent.futures,json,threading
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1];tmp=Path(tempfile.mkdtemp(prefix='yc-email-v57-'))
os.environ['YICHEN_DATA_DIR']=str(tmp);os.environ['YICHEN_CONFIG_FILE']=str(tmp/'none.env')
for key in list(os.environ):
 if key.startswith('YICHEN_SMTP_') or key in ('YICHEN_NOTIFY_EMAIL','YICHEN_AUTH_SECRET'):os.environ.pop(key)
sys.path.insert(0,str(root))
from webapp import create_app,service
mail=service.account_email;clock=[int(time.time())];mail.time=SimpleNamespace(time=lambda:clock[0]);ready=[False];mail.mail_ready=lambda:ready[0]
production_deliver=mail.deliver_code
production_dispatch=mail.dispatch_delivery
mail.dispatch_delivery=lambda *args:mail.finish_delivery(*args)
sent=[];mail.deliver_code=lambda email,code,purpose:sent.append((email,code,purpose));app=create_app(start_mail=False)
service.Handler.rate_limited=lambda *a,**k:False
counter=[0];checks=[]
def check(name,value):assert value,name;checks.append(name)
def send(client,email,purpose='register',**extra):
 counter[0]+=1
 return client.post('/api/auth/email/send-code',json=dict(email=email,purpose=purpose,**extra),environ_base={'REMOTE_ADDR':'192.0.2.'+str(counter[0]%250+1)})
def advance():clock[0]+=61
def challenge(client,email,purpose='register',**extra):
 advance();r=send(client,email,purpose,**extra);assert r.status_code==200,r.json;return r.json['challengeId'],sent[-1][1]
def register(client,email='qa-v57@example.com',name='QA 邮箱（虚构）'):
 identity,code=challenge(client,email);return client.post('/api/auth/register',json=dict(email=email,name=name,password='QA-original-password',challengeId=identity,code=code))
c=app.test_client();other=app.test_client()
check('mail configuration fails closed',send(c,'qa@example.com').status_code==503)
check('registration requires proof',c.post('/api/auth/register',json=dict(email='qa@example.com',name='QA',password='QA-original-password')).status_code==400)
check('new unverified phone registration disabled',c.post('/api/auth/register',json=dict(phone='13900000000',name='QA',password='QA-original-password')).status_code==503)
ready[0]=True
for invalid in ['qa,other@example.com','qa@example.com;other@example.com','QA <qa@example.com>','qa@example.com\nBcc: other@example.com']:
 check('multi-recipient or header syntax rejected '+str(len(checks)),send(c,invalid).status_code==400)
r=register(c);check('verified email registration succeeds',r.status_code==200 and r.json['user']['emailVerified']);uid=r.json['user']['id']
check('verified flag persists',c.get('/api/auth/me').json['user']['emailVerified'])
with sqlite3.connect(service.DB) as db:
 row=db.execute('SELECT code_hash,status FROM email_challenges ORDER BY created DESC LIMIT 1').fetchone();check('only hashed consumed challenge stored',len(row[0])==64 and row[1]=='consumed')
check('code absent from public response',set(send(c,'unknown@example.com','reset').json)=={'challengeId','expiresIn','retryAfter','message'})
count=len(sent);advance();unknown=send(c,'no-user@example.com','reset');check('unknown reset is generic without delivery',unknown.status_code==200 and len(sent)==count)
# Legacy account stays unverified; email alone cannot recover it.
with sqlite3.connect(service.DB) as db:db.execute('INSERT INTO users VALUES(?,?,?,?,?)',('legacy','qa-legacy@example.com','QA Legacy',service.password_hash('QA-legacy-password'),int(time.time())))
legacy=app.test_client();legacy.post('/api/auth/login',json=dict(email='qa-legacy@example.com',password='QA-legacy-password'))
check('legacy remains unverified',legacy.get('/api/auth/me').json['user']['emailVerified'] is False)
count=len(sent);advance();unverified=send(other,'qa-legacy@example.com','reset');check('unverified reset does not send',unverified.status_code==200 and len(sent)==count and unverified.json['message']==unknown.json['message'])
check('verification requires login',send(other,'qa-legacy@example.com','verify',password='QA-legacy-password').status_code==401)
check('verification binds current email',send(legacy,'someone@example.com','verify',password='QA-legacy-password').status_code==400)
check('verification requires current password',send(legacy,'qa-legacy@example.com','verify',password='wrong').status_code==401)
id,code=challenge(legacy,'qa-legacy@example.com','verify',password='QA-legacy-password')
check('another session cannot verify legacy account',c.post('/api/auth/email/verify',json=dict(challengeId=id,code=code)).status_code==400)
check('legacy proof succeeds',legacy.post('/api/auth/email/verify',json=dict(challengeId=id,code=code)).json['user']['emailVerified'])
check('verify cannot be replayed',legacy.post('/api/auth/email/verify',json=dict(challengeId=id,code=code)).status_code==400)
# Purpose, address binding, expiry and failed-attempt cap.
id,code=challenge(c,'qa-binding@example.com')
check('register code cannot reset',other.post('/api/auth/password/reset',json=dict(email='qa-binding@example.com',challengeId=id,code=code,password='QA-new-password')).status_code==400)
check('code binds email',other.post('/api/auth/register',json=dict(email='changed@example.com',name='QA',challengeId=id,code=code,password='QA-new-password')).status_code==400)
with sqlite3.connect(service.DB) as db:db.execute('UPDATE email_challenges SET expires=0 WHERE id=?',(id,))
check('expired code rejected',other.post('/api/auth/register',json=dict(email='qa-binding@example.com',name='QA',challengeId=id,code=code,password='QA-new-password')).status_code==400)
id,code=challenge(c,'qa-attempts@example.com');wrong='000000' if code!='000000' else '999999'
for i in range(5):check('wrong code rejected '+str(i+1),other.post('/api/auth/register',json=dict(email='qa-attempts@example.com',name='QA',challengeId=id,code=wrong,password='QA-new-password')).status_code==400)
check('five attempts block even correct code',other.post('/api/auth/register',json=dict(email='qa-attempts@example.com',name='QA',challengeId=id,code=code,password='QA-new-password')).status_code==400)
id,old=challenge(c,'qa-resend@example.com');check('cooldown enforced',send(c,'qa-resend@example.com').status_code==429)
newid,new=challenge(c,'qa-resend@example.com')
check('resend supersedes old code',other.post('/api/auth/register',json=dict(email='qa-resend@example.com',name='QA',challengeId=id,code=old,password='QA-new-password')).status_code==400)
check('replacement code works',other.post('/api/auth/register',json=dict(email='qa-resend@example.com',name='QA',challengeId=newid,code=new,password='QA-new-password')).status_code==200)
# Concurrent redemptions create one identity, never two.
id,code=challenge(c,'qa-concurrent@example.com')
def redeem_registration(_):
 with app.test_client() as client:return client.post('/api/auth/register',json=dict(email='qa-concurrent@example.com',name='QA',challengeId=id,code=code,password='QA-new-password')).status_code
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(redeem_registration,range(2)))
check('concurrent single-use enforcement',results.count(200)==1 and all(x in (200,400,409) for x in results))
# Reset verified account and invalidate every prior session.
other.post('/api/auth/login',json=dict(email='qa-v57@example.com',password='QA-original-password'))
id,code=challenge(c,'qa-v57@example.com','reset')
with sqlite3.connect(service.DB) as db:
 db.execute("INSERT INTO email_challenges SELECT 'pending-reset-test',email,purpose,user_id,code_hash,created,expires,attempts,'pending',ip_hash FROM email_challenges WHERE id=?",(id,))
r=app.test_client().post('/api/auth/password/reset',json=dict(email='qa-v57@example.com',challengeId=id,code=code,password='QA-updated-password'))
with sqlite3.connect(service.DB) as db:check('reset invalidates pending deliveries',db.execute("SELECT status FROM email_challenges WHERE id='pending-reset-test'").fetchone()[0]=='superseded')
check('verified reset succeeds',r.status_code==200)
check('all sessions invalidated',c.get('/api/auth/me').json['user'] is None and other.get('/api/auth/me').json['user'] is None)
check('old password fails',c.post('/api/auth/login',json=dict(email='qa-v57@example.com',password='QA-original-password')).status_code==401)
check('new password works',c.post('/api/auth/login',json=dict(email='qa-v57@example.com',password='QA-updated-password')).status_code==200)
check('reset cannot replay',c.post('/api/auth/password/reset',json=dict(email='qa-v57@example.com',challengeId=id,code=code,password='QA-another-password')).status_code==400)
# Delivery errors must not enable registration or disclose transport credentials.
original=mail.deliver_code
def broken(*a):raise RuntimeError('PRIVATE AUTHORIZATION CODE MUST NOT LEAK')
mail.deliver_code=broken;advance();r=send(c,'qa-delivery@example.com');check('delivery failure safe',r.status_code==200 and 'PRIVATE' not in r.get_data(as_text=True));mail.deliver_code=original
with sqlite3.connect(service.DB) as db:check('delivery failed code unusable',db.execute("SELECT status FROM email_challenges WHERE email='qa-delivery@example.com'").fetchone()[0]=='failed')
check('cross-origin request rejected',c.post('/api/auth/email/send-code',json=dict(email='qa@example.com',purpose='reset'),headers={'Origin':'https://evil.example','Sec-Fetch-Site':'cross-site'}).status_code==403)
check('malformed payload rejected',c.post('/api/auth/password/reset',json=[]).status_code==400)
check('verification key private',os.stat(tmp/'auth-challenge.key').st_mode&0o777==0o600)
# Existing phone accounts can log in, but no email-based recovery is invented.
with sqlite3.connect(service.DB) as db:
 db.execute('INSERT INTO users VALUES(?,?,?,?,?)',('legacy-phone','phone:13900000000','QA Phone',service.password_hash('QA-phone-password'),int(time.time())))
 db.execute('INSERT INTO user_phones VALUES(?,?)',('13900000000','legacy-phone'))
phone=app.test_client();r=phone.post('/api/auth/login',json=dict(phone='13900000000',password='QA-phone-password'));check('legacy phone login retained',r.status_code==200 and not r.json['user']['phoneVerified'])
# Production dispatch must return before SMTP completes, for both eligible and unknown identities.
advance();started=threading.Event();release=threading.Event();finished=threading.Event()
def blocking_fake(email,code,purpose):
 started.set();release.wait(3);finished.set()
mail.deliver_code=blocking_fake;mail.dispatch_delivery=production_dispatch
r=send(c,'qa-v57@example.com','reset')
check('SMTP work runs outside request',r.status_code==200 and started.wait(1) and not finished.is_set())
unknown_async=send(c,'async-unknown@example.com','reset');check('unknown and known async reply shape identical',set(r.json)==set(unknown_async.json) and r.json['message']==unknown_async.json['message'])
release.set();check('async mail task finishes',finished.wait(1))
for _ in range(100):
 with sqlite3.connect(service.DB) as db:status=db.execute('SELECT status FROM email_challenges WHERE id=?',(r.json['challengeId'],)).fetchone()[0]
 if status=='sent':break
 time.sleep(.01)
check('asynchronous delivery marks challenge ready',status=='sent')
mail.deliver_code=original;mail.dispatch_delivery=lambda *args:mail.finish_delivery(*args)
check('fake mailbox is not a production route',c.get('/__qa__/mailbox').status_code==404)
check('client cannot assert verified status',c.post('/api/auth/register',json=dict(email='claimed@example.com',name='QA',password='QA-new-password',emailVerified=True)).status_code==400)
# A fresh day isolates durable IP/hour and recipient/day quotas.
clock[0]+=86401
for i in range(20):
 r=c.post('/api/auth/email/send-code',json=dict(email=f'quota-{i}@example.com',purpose='reset'),environ_base={'REMOTE_ADDR':'198.51.100.1'});assert r.status_code==200,r.json
check('durable IP hourly quota',c.post('/api/auth/email/send-code',json=dict(email='quota-last@example.com',purpose='reset'),environ_base={'REMOTE_ADDR':'198.51.100.1'}).status_code==429)
for i in range(10):advance();assert send(c,'recipient-quota@example.com','reset').status_code==200
advance();check('recipient daily quota',send(c,'recipient-quota@example.com','reset').status_code==429)
# Actual message builder and shared TLS transport, using a fake SMTP object only.
transport=[];smtp_original=service.inquiry_mail.smtplib.SMTP_SSL
class FakeSMTP:
 def __init__(self,host,port,timeout,context):assert host=='smtp.example.com' and port==465 and context.check_hostname
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def login(self,user,password):assert user=='qa-sender@example.com' and password=='FAKE-TEST-ONLY'
 def send_message(self,message):transport.append(message)
os.environ.update(YICHEN_SMTP_HOST='smtp.example.com',YICHEN_SMTP_PORT='465',YICHEN_SMTP_USER='qa-sender@example.com',YICHEN_SMTP_PASSWORD='FAKE-TEST-ONLY',YICHEN_NOTIFY_EMAIL='qa-operator@example.com')
service.inquiry_mail.smtplib.SMTP_SSL=FakeSMTP
try:production_deliver('qa-recipient@example.com','123456','reset')
finally:service.inquiry_mail.smtplib.SMTP_SSL=smtp_original
check('verification email uses requested recipient over TLS',len(transport)==1 and transport[0]['To']=='qa-recipient@example.com' and transport[0]['From']=='qa-sender@example.com')
check('verification email contains purpose code expiry but no password','123456' in transport[0].get_content() and '10分钟' in transport[0].get_content() and 'QA-original-password' not in transport[0].get_content())
result={'checks':checks,'count':len(checks),'isolated':True,'realEmailSent':False};target=root/'output/playwright/auth-v57';target.mkdir(parents=True,exist_ok=True);(target/'api-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('PASS v57: '+str(len(checks))+' ownership, recovery, transport, concurrency and quota checks; no real SMTP.')
