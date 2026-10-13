#!/usr/bin/env python3
"""YICHEN local account service and same-origin AMap proxy. Python 3.10+, no packages."""
import argparse, base64, hashlib, hmac, json, math, os, re, secrets, sqlite3, threading, time
from datetime import datetime
from http import cookies
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(ROOT))
import operator_backend,inquiry_mail
CONFIG_FILE=Path(os.environ.get('YICHEN_CONFIG_FILE') or ROOT/'.env').resolve()
if CONFIG_FILE==ROOT/'dist' or ROOT/'dist' in CONFIG_FILE.parents:raise RuntimeError('Private configuration cannot be inside dist/.')
for line in CONFIG_FILE.read_text().splitlines() if CONFIG_FILE.exists() else []:
    line=line.strip()
    if line and not line.startswith('#') and '=' in line:
        key,value=line.split('=',1);os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
DATA = Path((os.environ.get('YICHEN_DATA_DIR') or str(ROOT/'data'))).resolve()
if DATA==ROOT/'dist' or ROOT/'dist' in DATA.parents:raise RuntimeError('Private data cannot be inside dist/.')
DATA.mkdir(parents=True, exist_ok=True)
os.chmod(DATA, 0o700)
DB=DATA/'accounts.sqlite3'
ENQUIRY_PLACES={p['id']:p for p in json.loads((ROOT/'business/enquiry-places-v44.json').read_text())}
AMAP_KEY=os.environ.get('AMAP_JS_KEY','')
AMAP_SECURITY=os.environ.get('AMAP_SECURITY_CODE','')
PUBLIC_ORIGIN=os.environ.get('YICHEN_PUBLIC_ORIGIN','').rstrip('/')
with sqlite3.connect(DB) as db:
    db.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,created INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS user_phones(phone TEXT PRIMARY KEY,user_id TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,body TEXT NOT NULL,created INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS orders_user ON orders(user_id);
    CREATE TABLE IF NOT EXISTS inquiries(id TEXT PRIMARY KEY,user_id TEXT,body TEXT NOT NULL,created INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,user_id TEXT NOT NULL,car TEXT NOT NULL,rating INTEGER NOT NULL,content TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS reviews_car ON reviews(car,status);''')
os.chmod(DB,0o600)
operator_backend.initialize(DB)
inquiry_mail.initialize(DB)
RATE={};RATE_LOCK=threading.Lock()
def password_hash(password):
    salt=secrets.token_bytes(24)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
    return base64.b64encode(salt).decode()+':'+base64.b64encode(digest).decode()
def password_valid(password,encoded):
    salt,digest=encoded.split(':')
    test=hashlib.scrypt(password.encode(),salt=base64.b64decode(salt),n=16384,r=8,p=1,dklen=32)
    return hmac.compare_digest(test,base64.b64decode(digest))
DUMMY_PASSWORD=password_hash(secrets.token_urlsafe(20))
class Handler(SimpleHTTPRequestHandler):
    config_file=CONFIG_FILE
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.glb':'model/gltf-binary'}
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');super().end_headers()
    def reply(self,status,data,cookie=None):
        body=json.dumps(data,ensure_ascii=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store')
        if cookie:self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def error(self,status,message):self.reply(status,{'error':message})
    def session(self):
        jar=cookies.SimpleCookie()
        try:jar.load(self.headers.get('Cookie',''));token=jar['yichen_session'].value
        except (cookies.CookieError,KeyError):return None
        digest=hashlib.sha256(token.encode()).hexdigest()
        with sqlite3.connect(DB) as db:
            row=db.execute('SELECT u.id,u.email,u.name FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',(digest,int(time.time()))).fetchone()
        return self.public_user(dict(zip(['id','email','name'],row))) if row else None
    def public_user(self,user):
        with sqlite3.connect(DB) as db:
            phone=db.execute('SELECT phone FROM user_phones WHERE user_id=?',(user['id'],)).fetchone()
            user['isOperator']=bool(db.execute('SELECT 1 FROM operators WHERE user_id=?',(user['id'],)).fetchone())
        user['phone']=phone[0] if phone else None
        if phone:user['email']=None;user['phoneVerified']=False
        return user
    def new_session(self,user_id):
        token=secrets.token_urlsafe(32);expires=int(time.time())+7*86400
        with sqlite3.connect(DB) as db:
            db.execute('DELETE FROM sessions WHERE expires<=?',(int(time.time()),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,expires))
        return self.cookie(token,7*86400)
    def cookie(self,token,age):return f'yichen_session={token}; Path=/; Max-Age={age}; HttpOnly; SameSite=Lax'+('; Secure' if PUBLIC_ORIGIN.startswith('https://') else '')
    def allowed_origin(self):
        origin=self.headers.get('Origin')
        allowed={PUBLIC_ORIGIN} if PUBLIC_ORIGIN else {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        # Browser mutations require an exact same-origin Origin. CLI requests may omit it.
        return (not origin or origin in allowed) and self.headers.get('Sec-Fetch-Site','same-origin') in ('same-origin','none')
    def rate_limited(self,key,limit=12):
        now=time.time()
        with RATE_LOCK:
            if len(RATE)>5000:
                for old in list(RATE):
                    if not RATE[old] or RATE[old][-1]<now-900:RATE.pop(old,None)
            hits=[t for t in RATE.get(key,[]) if t>now-900];limited=len(hits)>=limit
            if not limited:hits.append(now)
            RATE[key]=hits
        return limited
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/operator/'):
            return operator_backend.get(self,DB,path,dict(parse_qsl(urlsplit(self.path).query)))
        if path=='/api/config':return self.reply(200,{'amapKey':AMAP_KEY if AMAP_SECURITY else '', 'amapServiceHost':'/_AMapService','authEnabled':True,'amapConfigured':bool(AMAP_KEY and AMAP_SECURITY)})
        if path=='/api/auth/me':return self.reply(200,{'user':self.session()})
        if path=='/api/reviews':
            car=dict(parse_qsl(urlsplit(self.path).query)).get('car','')
            with sqlite3.connect(DB) as db:
                rows=db.execute('SELECT u.name,r.rating,r.content,r.created FROM reviews r JOIN users u ON r.user_id=u.id WHERE r.car=? AND r.status=? ORDER BY r.created DESC LIMIT 50',(car,'approved')).fetchall()
            return self.reply(200,{'reviews':[dict(zip(['name','rating','content','created'],r)) for r in rows]})
        if path=='/api/inquiries':
            user=self.session()
            if not user:return self.error(401,'请先登录。')
            with sqlite3.connect(DB) as db:rows=db.execute('SELECT body FROM inquiries WHERE user_id=? ORDER BY created DESC LIMIT 50',(user['id'],)).fetchall()
            return self.reply(200,{'inquiries':[json.loads(r[0]) for r in rows]})
        if path=='/api/orders':
            user=self.session()
            if not user:return self.error(401,'请先登录。')
            with sqlite3.connect(DB) as db:rows=db.execute('SELECT body FROM orders WHERE user_id=? ORDER BY created DESC',(user['id'],)).fetchall()
            return self.reply(200,{'orders':[json.loads(row[0]) for row in rows]})
        if path.startswith('/_AMapService/'):
            if not AMAP_KEY or not AMAP_SECURITY:return self.error(503,'高德地图尚未配置，请先选择成都主要地点。')
            suffix=path[len('/_AMapService'):]
            if '..' in suffix or not re.fullmatch(r'/[A-Za-z0-9_./-]+',suffix):return self.error(400,'请求来源不允许。')
            if self.rate_limited(('map',self.client_address[0]),300):return self.error(429,'尝试次数过多，请稍后再试。')
            host='https://webapi.amap.com' if suffix.startswith('/v4/map/styles') else 'https://restapi.amap.com'
            args=[(k,v) for k,v in parse_qsl(urlsplit(self.path).query,keep_blank_values=True) if k!='jscode'];args.append(('jscode',AMAP_SECURITY))
            try:
                with urlopen(Request(host+suffix+'?'+urlencode(args),headers={'User-Agent':'YichenDrive/1.0'}),timeout=12) as response:
                    body=response.read(8*1024*1024+1)
                    if len(body)>8*1024*1024:return self.error(502,'高德地图未能加载，请检查配置。')
                    self.send_response(response.status);self.send_header('Content-Type',response.headers.get('Content-Type','application/json'));self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            except (HTTPError,URLError,TimeoutError):self.error(502,'高德地图未能加载，请检查配置。')
            return
        if path.startswith('/api/'):return self.error(404,'操作失败，请稍后重试。')
        if path not in ('/','/index.html') and Path(path).suffix.lower() not in {'.html','.js','.mjs','.glb','.css','.jpg','.jpeg','.png','.svg','.webp','.ico'}:return self.error(404,'操作失败，请稍后重试。')
        super().do_GET()
    def do_POST(self):
        if not self.allowed_origin():return self.error(403,'请求来源不允许。')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>16384:return self.error(400,'订单数据不完整。')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError()
        except (ValueError,json.JSONDecodeError):return self.error(400,'订单数据不完整。')
        path=urlsplit(self.path).path
        if path.startswith('/api/operator/'):
            return operator_backend.post(self,DB,path,body)
        if path in ('/api/auth/register','/api/auth/login'):
            account=str(body.get('account') or body.get('phone') or body.get('email') or '').strip().lower();password=body.get('password','');phone=account if re.fullmatch(r'1[3-9][0-9]{9}',account) else None;email='phone:'+phone if phone else account
            if self.rate_limited(('auth',self.client_address[0])):return self.error(429,'尝试次数过多，请稍后再试。')
            if not phone and (len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)):return self.error(400,'请输入有效邮箱或11位大陆手机号。')
            if not isinstance(password,str) or len(password)<10 or len(password)>128:return self.error(400,'密码至少需要 10 位字符。')
            with sqlite3.connect(DB) as db:
                row=db.execute('SELECT id,email,name,password FROM users WHERE email=?',(email,)).fetchone()
                if path.endswith('register'):
                    name=str(body.get('name','')).strip()
                    if not name or len(name)>50:return self.error(400,'请填写称呼。')
                    if row:return self.error(409,'此账号已注册，请直接登录。')
                    user={'id':secrets.token_hex(16),'email':email,'name':name}
                    try:db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(user['id'],email,name,password_hash(password),int(time.time())))
                    except sqlite3.IntegrityError:return self.error(409,'此账号已注册，请直接登录。')
                    if phone:db.execute('INSERT INTO user_phones VALUES(?,?)',(phone,user['id']))
                else:
                    valid=password_valid(password,row[3] if row else DUMMY_PASSWORD)
                    if not row or not valid:return self.error(401,'账号或密码不正确。')
                    user=dict(zip(['id','email','name'],row[:3]))
            return self.reply(200,{'user':self.public_user(user)},self.new_session(user['id']))
        if path=='/api/auth/logout':
            jar=cookies.SimpleCookie()
            try:jar.load(self.headers.get('Cookie',''));token=jar['yichen_session'].value
            except (cookies.CookieError,KeyError):token=''
            with sqlite3.connect(DB) as db:db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
            return self.reply(200,{'ok':True},self.cookie('',0))
        if path in ('/api/inquiries','/api/reviews'):
            if self.rate_limited((path,self.client_address[0]),15):return self.error(429,'提交过于频繁，请稍后重试。')
            cars={'718','x5','my','e','gl8','gl8-653','denza-d9','magotan','passat','jetta','coaster','h7'}
            user=self.session()
            if body.get('consent') is not True:return self.error(400,'请确认信息使用说明。')
            if path=='/api/reviews':
                if not user:return self.error(401,'请先登录后提交评价。')
                content=body.get('content','');rating=body.get('rating');car=body.get('car')
                if car not in cars or type(rating) is not int or not 1<=rating<=5 or not isinstance(content,str) or not 10<=len(content.strip())<=1000:return self.error(400,'请填写10至1000字的评价及有效评分。')
                identity='REV-'+secrets.token_hex(8).upper()
                with sqlite3.connect(DB) as db:db.execute('INSERT INTO reviews(id,user_id,car,rating,content,created) VALUES(?,?,?,?,?,?)',(identity,user['id'],car,rating,content.strip(),int(time.time())))
                return self.reply(201,{'review':{'id':identity,'status':'pending'}})
            try:
                clean={k:str(body.get(k,'')).strip() for k in ('service','car','city','startDate','endDate','name','phone','wechat','pickupId','returnId','destinationId','startTime','endTime')}
                cities={'成都','绵阳','德阳','乐山','宜宾','泸州','雅安','西昌','康定','南充','达州','自贡'}
                if clean['service'] not in {'自驾租车','机场接送','带司机包车','商务接待'} or clean['city'] not in cities or clean['car'] and clean['car'] not in cars:raise ValueError()
                if not 1<=len(clean['name'])<=50:raise ValueError()
                if not re.fullmatch(r'[0-9]{11}',clean['phone']):return self.error(400,'请输入11位数字的联系电话。')
                if not 2<=len(clean['wechat'])<=60:return self.error(400,'请填写微信号，至少2个字符。')
                for key in ('pickupId','returnId','destinationId'):
                    if clean[key] not in ENQUIRY_PLACES:return self.error(400,'请从选项中选择真实地点。')
                for key in ('pickupId','returnId'):
                    place=ENQUIRY_PLACES[clean[key]]
                    if place.get('kind')!='city' or ENQUIRY_PLACES.get('city-'+place.get('cityKey',''),{}).get('name')!=clean['city']:return self.error(400,'取还车地点必须属于所选服务城市。')
                times={f'{h:02d}:{minute:02d}' for h in range(24) for minute in (0,30)}
                if clean['startTime'] not in times or clean['endTime'] not in times:raise ValueError()
                from datetime import timezone,timedelta
                today=datetime.now(timezone(timedelta(hours=8))).date()
                start_day=datetime.strptime(clean['startDate'],'%Y-%m-%d').date()
                end_day=datetime.strptime(clean['endDate'],'%Y-%m-%d').date()
                duration=(end_day-start_day).days+1
                if start_day<today or (start_day-today).days>730 or not 1<=duration<=30:raise ValueError()
                start_at=datetime.fromisoformat(clean['startDate']+'T'+clean['startTime'])
                end_at=datetime.fromisoformat(clean['endDate']+'T'+clean['endTime'])
                if end_at<=start_at:return self.error(400,'结束时间须晚于开始时间。')
                requested=body.get('durationDays')
                if str(requested)!=str(duration):return self.error(400,'用车天数与开始结束日期不一致。')
                clean.update(durationDays=duration,startAt=start_at.isoformat(timespec='minutes'),endAt=end_at.isoformat(timespec='minutes'))
                people=body.get('people');bags=body.get('bags')
                if type(people) is not int or not 1<=people<=60 or type(bags) is not int or not 0<=bags<=60:raise ValueError()
                for key,label in [('pickupId','pickup'),('returnId','returnAt'),('destinationId','destination')]:clean[label]=ENQUIRY_PLACES[clean[key]]['name']
                identity='YC-INQ-'+secrets.token_hex(6).upper();clean.update(id=identity,people=people,bags=bags,status='pending',created=int(time.time()))
            except (ValueError,TypeError):return self.error(400,'请核对城市、日期、联系人、人数及行程信息。')
            with sqlite3.connect(DB) as db:
                db.execute('INSERT INTO inquiries VALUES(?,?,?,?)',(identity,user['id'] if user else None,json.dumps(clean,ensure_ascii=False),int(time.time())))
                inquiry_mail.enqueue(db,identity)
            return self.reply(201,{'inquiry':{'id':identity,'status':'pending'}})
        if path=='/api/orders':
            user=self.session()
            if not user:return self.error(401,'请先登录。')
            try:
                car=body['car'];prices={'718':1280,'x5':1080,'my':680,'e':880,'gl8':680,'magotan':420,'passat':480,'jetta':260,'coaster':1500,'h7':680}
                if car not in prices:raise ValueError()
                start=datetime.fromisoformat(body['start']);end=datetime.fromisoformat(body['end'])
                seconds=(end-start).total_seconds()
                if seconds<=0 or seconds>90*86400 or 'T' not in body['start'] or 'T' not in body['end']:raise ValueError()
                if not body.get('pickup') or not body.get('name') or not body.get('phone') or not body.get('email'):raise ValueError()
                days=max(1,math.ceil(seconds/86400));base=prices[car]*days
                protection=body.get('protection','基础保障');extras=body.get('extras',[])
                allowed_extras={'额外驾驶员','儿童座椅','额外里程','提前加油','雪地装备'}
                if not isinstance(extras,list) or any(x not in allowed_extras for x in extras):raise ValueError()
                cover={'基础保障':0,'标准保障':80,'尊享保障':150}[protection]*days
                clean={k:str(body.get(k,''))[:300] for k in ('car','pickup','pickupId','pickupDetail','start','end','returnAt','name','phone','email')}
                clean.update({'accountId':user['id'],'order':'YC-DEMO-'+secrets.token_hex(6).upper(),'timeConfirmed':True,'days':days,'protection':protection,'extras':list(set(extras)),'total':base+120+int((base+120)*.09+.5)+cover+len(set(extras))*60*days})
            except (KeyError,ValueError,TypeError):return self.error(400,'订单数据不完整。')
            with sqlite3.connect(DB) as db:db.execute('INSERT INTO orders VALUES(?,?,?,?)',(clean['order'],user['id'],json.dumps(clean,ensure_ascii=False),int(time.time())))
            return self.reply(201,{'order':clean})
        self.error(404,'操作失败，请稍后重试。')
    def list_directory(self,path):self.error(404,'操作失败，请稍后重试。');return None
    def log_message(self,format,*args):
        # Do not log AMap query strings or submitted credentials.
        if urlsplit(self.path).path.startswith('/_AMapService/'):return
        print(f'{self.client_address[0]} {self.command} {urlsplit(self.path).path}')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--host',default='127.0.0.1');args=parser.parse_args()
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'YICHEN Drive: http://{args.host}:{args.port}/ (Ctrl+C to stop)',flush=True)
    inquiry_mail.start(DB)
    server.serve_forever()
