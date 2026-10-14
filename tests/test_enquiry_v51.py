"""Isolated API regression; never opens a mail worker or the live database."""
import os,tempfile,sys,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['YICHEN_DATA_DIR']=tempfile.mkdtemp(prefix='yc-v51-test-')
os.environ['YICHEN_CONFIG_FILE']=str(Path(tempfile.mkdtemp())/'empty.env')
sys.path.insert(0,str(ROOT))
from webapp import create_app,service
service.Handler.rate_limited=lambda *a,**k:False
app=create_app(start_mail=False);guest=app.test_client();admin=app.test_client()
def post(v):
 r=guest.post('/api/inquiries',json=v);return r.status_code,r.get_json()
base=dict(service='自驾租车',car='gl8',city='成都',startDate='2026-10-16',endDate='2026-10-21',startTime='10:00',endTime='10:00',durationDays='999',people=5,bags=3,name='QA ONLY',phone='13800138000',phoneRegion='CN',wechat='qa_only',pickupId='place-tianfu',returnId='place-tianfu',destinationId='city-chengdu',consent=True)
status,data=post(base);assert status==201,data;assert data['inquiry']['durationDays']==5
identity=data['inquiry']['id']
with sqlite3.connect(service.DB) as db:
 v=json.loads(db.execute('SELECT body FROM inquiries WHERE id=?',(identity,)).fetchone()[0]);assert v['durationDays']==5 and v['phone']=='+8613800138000'
 assert db.execute('SELECT COUNT(*) FROM inquiry_mail WHERE id=?',(identity,)).fetchone()[0]==1
for dates,expected in [(('2026-10-16','10:00','2026-10-16','18:00'),1),(('2026-10-16','10:00','2026-10-17','10:00'),1),(('2026-10-16','10:00','2026-10-17','10:30'),2),(('2026-10-30','10:00','2026-11-02','10:00'),3)]:
 v=dict(base,**dict(zip(['startDate','startTime','endDate','endTime'],dates)));status,d=post(v);assert status==201,d;assert d['inquiry']['durationDays']==expected
for edits in [dict(endDate='2026-10-16',endTime='09:00'),dict(startDate='2020-01-01'),dict(endDate='2026-11-16')]:assert post(dict(base,**edits))[0]==400
for region,phone in [('CN','00000000000'),('CN','138001'),('US','1111111111'),('ZZ','2025550123'),('CN','+12025550123')]:assert post(dict(base,phoneRegion=region,phone=phone))[0]==400
for region,phone,normalized in [('HK','61234567','+85261234567'),('US','2025550123','+12025550123'),('GB','02079460018','+442079460018')]:
 status,d=post(dict(base,phoneRegion=region,phone=phone));assert status==201,d
 with sqlite3.connect(service.DB) as db:assert json.loads(db.execute('SELECT body FROM inquiries WHERE id=?',(d['inquiry']['id'],)).fetchone()[0])['phone']==normalized
old=dict(base);old.pop('phoneRegion');assert post(old)[0]==201
assert guest.post('/api/orders',json={}).status_code==410
assert guest.get('/api/operator/inquiries').status_code==401
r=admin.post('/api/auth/register',json=dict(email='v51@example.com',name='QA',password='fixture-only-password'));assert r.status_code==200
with sqlite3.connect(service.DB) as db:db.execute('INSERT INTO operators VALUES(?,0)',(r.get_json()['user']['id'],))
d=admin.get('/api/operator/detail?id='+identity).get_json()['inquiry'];assert d['people']==5 and d['bags']==3 and d['startAt']=='2026-10-16T10:00'
cal=admin.get('/api/operator/summary?month=2026-10').get_json()['calendar'];assert all(next(x['count'] for x in cal if x['date']==f'2026-10-{i:02}')>0 for i in range(16,22))
print('PASS v51: server-authoritative 24h duration, international E.164 validation, rejected invalid phones/dates, legacy country default, admin permissions and mail enqueue; demo-order creation disabled.')
