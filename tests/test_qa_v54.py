"""Prelaunch regression, temporary DB only; fake outbox delivery, never real SMTP."""
import os,sys,tempfile,sqlite3,json,subprocess,concurrent.futures
from pathlib import Path
from datetime import datetime,timedelta,timezone
ROOT=Path(__file__).resolve().parents[1]
qa=Path(tempfile.mkdtemp(prefix='yc-v54-test-'))
os.environ['YICHEN_DATA_DIR']=str(qa);os.environ['YICHEN_CONFIG_FILE']=str(qa/'none.env')
sys.path.insert(0,str(ROOT))
from webapp import create_app,service
app=create_app(start_mail=False);guest=app.test_client();a=app.test_client();b=app.test_client()
original_rate_limited=service.Handler.rate_limited
service.Handler.rate_limited=lambda *args,**kwargs:False
start=datetime.now(timezone(timedelta(hours=8))).date()+timedelta(days=2)
base=dict(service='自驾租车',car='gl8',city='成都',startDate=str(start),endDate=str(start+timedelta(days=5)),startTime='10:00',endTime='10:00',people=5,bags=3,name='<img src=x onerror=alert(1)> QA',phone='13800138000',phoneRegion='CN',wechat='qa_only',pickupId='place-tianfu',returnId='place-tianfu',destinationId='city-chengdu',consent=True)
def post(c=guest,**extra):return c.post('/api/inquiries',json={**base,**extra})
for days,endtime,expected in [(0,'18:00',1),(1,'10:00',1),(1,'10:30',2),(30,'10:00',30)]:
 r=post(endDate=str(start+timedelta(days=days)),endTime=endtime,durationDays=999);assert r.status_code==201,r.get_json();assert r.json['inquiry']['durationDays']==expected
for changes in [dict(endDate=str(start),endTime='10:00'),dict(endDate=str(start),endTime='09:30'),dict(endDate=str(start+timedelta(days=30)),endTime='10:30'),dict(startDate='2020-01-01'),dict(city='重庆'),dict(pickupId='invalid'),dict(returnId='city-leshan'),dict(people=True),dict(consent=False)]:assert post(**changes).status_code==400,changes
for d1,d2 in [('2026-12-30','2027-01-02'),('2027-01-30','2027-02-02')]:
 r=post(startDate=d1,endDate=d2);assert r.status_code==201 and r.json['inquiry']['durationDays']==3
for region,phone in [('CN','00000000000'),('CN','138001'),('US','1111111111'),('ZZ','2025550123'),('CN','+12025550123')]:assert post(phoneRegion=region,phone=phone).status_code==400
for region,phone in [('CN','13800138000'),('HK','61234567'),('US','2025550123'),('GB','02079460018')]:assert post(phoneRegion=region,phone=phone).status_code==201
assert guest.post('/api/inquiries',data='[]',content_type='application/json').status_code==400
assert guest.post('/api/inquiries',data='x'*17000,content_type='application/json').status_code==413
assert guest.post('/api/inquiries',json=base,headers={'Origin':'https://evil.example','Sec-Fetch-Site':'cross-site'}).status_code==403
assert guest.post('/api/orders',json={}).status_code==410
for c,email in [(a,'qa-a@example.com'),(b,'qa-b@example.com')]:assert c.post('/api/auth/register',json=dict(email=email,name='QA',password='QA-test-password-only')).status_code==200
r=post(a,requestId='qa-v54-unique-key-01');identity=r.json['inquiry']['id'];assert r.status_code==201
assert post(a,requestId='qa-v54-unique-key-01').json['inquiry']['id']==identity
assert post(a,requestId='qa-v54-unique-key-01',bags=4).status_code==409
assert post(b,requestId='qa-v54-unique-key-01').status_code==409
# Concurrent retries of the exact same anonymous payload must create one record/outbox entry.
def retry(_):
 with app.test_client() as c:return post(c,requestId='qa-v54-concurrent-key').json['inquiry']['id']
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:ids=list(pool.map(retry,range(4)))
assert len(set(ids))==1
assert len(a.get('/api/inquiries').json['inquiries'])==1
assert not b.get('/api/inquiries').json['inquiries']
assert a.get('/api/operator/inquiries').status_code==403
assert guest.get('/api/inquiries').status_code==401
uid=a.get('/api/auth/me').json['user']['id']
with sqlite3.connect(service.DB) as db:
 db.execute('INSERT INTO operators VALUES(?,0)',(uid,))
 db.execute('INSERT INTO inquiry_followup VALUES(?,?,?,?,?)',(identity,'quoted','PRIVATE OPERATOR NOTE',1,0))
assert a.get('/api/inquiries').json['inquiries'][0]['status']=='quoted'
assert 'PRIVATE OPERATOR NOTE' not in a.get('/api/inquiries').text
assert a.post('/api/reviews',json=dict(car=[],rating=5,content='a sufficient test review',consent=True)).status_code==400
assert a.post('/api/reviews',json=dict(car='gl8',rating=5,content='<script>alert(1)</script>',consent=True)).status_code==201
assert guest.get('/api/reviews?car=gl8').json['reviews']==[]
assert a.post('/api/auth/logout',json={}).status_code==200
assert a.get('/api/operator/inquiries').status_code==401
# Restart-equivalent application instance shares persisted records, not volatile browser state.
assert create_app(start_mail=False).test_client().post('/api/auth/login',json=dict(email='qa-a@example.com',password='QA-test-password-only')).status_code==200
sent=[]
while service.inquiry_mail.process_one(service.DB,sender=sent.append):pass
assert len(sent)==len(set(sent))
with sqlite3.connect(service.DB) as db:
 assert db.execute('SELECT COUNT(*) FROM inquiry_mail WHERE status="pending"').fetchone()[0]==0
 assert db.execute('SELECT COUNT(*) FROM inquiry_mail WHERE id=?',(ids[0],)).fetchone()[0]==1
# Use the actual backup command, restore to a different private DB, compare contents and mode.
subprocess.run([sys.executable,str(ROOT/'backup-data.py'),'--data-dir',str(qa),'--backup-dir',str(qa/'backup')],check=True,capture_output=True)
backup=next((qa/'backup').glob('*.sqlite3'))
with sqlite3.connect(service.DB) as src,sqlite3.connect(backup) as restored:
 assert restored.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for table in ['users','inquiries','inquiry_mail','inquiry_followup','inquiry_requests','reviews']:assert src.execute('SELECT COUNT(*) FROM '+table).fetchone()==restored.execute('SELECT COUNT(*) FROM '+table).fetchone()
assert backup.stat().st_mode&0o777==0o600
import gzip
plain=guest.get('/app.js');compressed=guest.get('/app.js',headers={'Accept-Encoding':'gzip'})
assert compressed.headers['Content-Encoding']=='gzip'
assert gzip.decompress(compressed.data)==plain.data
assert 'Accept-Encoding' in compressed.headers['Vary']
assert compressed.headers['X-Frame-Options']=='DENY'
assert 'object-src' in compressed.headers['Content-Security-Policy']
assert guest.get('/does-not-exist').status_code==404
assert '页面未找到' in guest.get('/does-not-exist').text
for private in ['/.env','/server.py','/accounts.sqlite3','/../server.py']:
 assert guest.get(private).status_code==404
service.AMAP_KEY='QA_PUBLIC_KEY';service.AMAP_SECURITY='QA_SECRET_NEVER_PUBLIC'
assert guest.get('/api/config').json['cloudSyncEnabled'] is False
assert 'workbuddy-cloud-sdk@dev' not in guest.get('/').text
assert 'QA_SECRET_NEVER_PUBLIC' not in guest.get('/api/config').text
assert guest.get('/api/config').json['amapKey']=='QA_PUBLIC_KEY'
with sqlite3.connect(service.DB) as db:db.execute('UPDATE sessions SET expires=0')
assert b.get('/api/inquiries').status_code==401
service.PUBLIC_ORIGIN='https://qa.yichen.test'
secure=app.test_client().post('/api/auth/login',base_url=service.PUBLIC_ORIGIN,json=dict(email='qa-b@example.com',password='QA-test-password-only'))
assert 'Secure' in secure.headers['Set-Cookie'] and 'HttpOnly' in secure.headers['Set-Cookie'] and 'SameSite=Lax' in secure.headers['Set-Cookie']
service.PUBLIC_ORIGIN='';service.RATE.clear();service.Handler.rate_limited=original_rate_limited
attempts=[guest.post('/api/auth/login',json=dict(email='missing@example.com',password='QA-wrong-password')).status_code for _ in range(13)]
assert attempts==[401]*12+[429],attempts
print('PASS v54: duration/region/phone boundaries; concurrent idempotent retries; ownership and CSRF; malformed input; moderated reviews; session logout; fake mail delivery; persistence; backup restore integrity.')
