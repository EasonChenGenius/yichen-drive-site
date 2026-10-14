import os,sys,tempfile,sqlite3,json
from pathlib import Path
os.environ['YICHEN_DATA_DIR']=tempfile.mkdtemp(prefix='yc-accounts-test-')
os.environ['YICHEN_CONFIG_FILE']=str(Path(tempfile.mkdtemp())/'empty.env')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from webapp import create_app,service
service.Handler.rate_limited=lambda *a,**k:False
app=create_app(start_mail=False);guest=app.test_client();admin=app.test_client();customer=app.test_client()
assert guest.get('/api/operator/users').status_code==401
r=customer.post('/api/auth/register',json=dict(email='qa-customer@example.com',name='QA Customer',password='fixture-only-password'));assert r.status_code==200
uid=r.get_json()['user']['id']
assert customer.get('/api/orders').status_code==200 and customer.get('/api/orders').get_json()=={'orders':[]}
assert customer.get('/api/operator/users').status_code==403
r=admin.post('/api/auth/register',json=dict(phone='13900000000',name='QA Admin',password='fixture-only-password'));aid=r.get_json()['user']['id']
with sqlite3.connect(service.DB) as db:
 db.execute('INSERT INTO operators VALUES(?,0)',(aid,))
 db.execute('INSERT INTO orders VALUES(?,?,?,?)',('DEMO-OLD',uid,json.dumps({'order':'DEMO-OLD','car':'gl8'}),0))
 db.execute('INSERT INTO inquiries VALUES(?,?,?,?)',('INQ-TEST',uid,json.dumps({'id':'INQ-TEST','created':0,'name':'QA Customer'}),0))
assert customer.get('/api/orders').get_json()['orders'][0]['order']=='DEMO-OLD'
assert customer.post('/api/orders',json={}).status_code==410
users=admin.get('/api/operator/users').get_json();assert users['total']==2
assert all(set(u)=={'id','name','email','phone','created','isOperator','inquiryCount','contactVerified'} for u in users['users'])
u=next(u for u in users['users'] if u['id']==uid);assert u['inquiryCount']==1 and not u['isOperator'] and not u['contactVerified']
a=next(u for u in users['users'] if u['id']==aid);assert a['phone']=='13900000000' and a['email'] is None
assert admin.get('/api/operator/users?q=qa-customer').get_json()['total']==1
assert admin.get('/api/operator/users?q=%25').get_json()['total']==0
assert admin.get('/api/operator/users?from=bad').status_code==400
assert admin.get('/api/operator/users?from=2026-11-02&to=2026-11-01').status_code==400
assert admin.get('/api/operator/inquiries?userId='+uid).get_json()['total']==1
assert admin.get('/api/operator/inquiries?userId='+aid).get_json()['total']==0
with sqlite3.connect(service.DB) as db:
 for i in range(51):db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(f'qa-{i}',f'{i}@example.com','Paging QA','NOT-A-PASSWORD',0))
assert len(admin.get('/api/operator/users').get_json()['users'])==50
assert len(admin.get('/api/operator/users?offset=50').get_json()['users'])==3
assert admin.get('/api/operator/users?to=1970-01-02').get_json()['total']==51
print('PASS v52: registration + historical-order reading, POST demo orders disabled, admin-only account directory, safe fields, dates/search/pagination and linked inquiries. No real accounts modified.')
