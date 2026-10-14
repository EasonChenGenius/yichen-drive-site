"""Authenticated operator inbox; role grants are available only through local CLI."""
import json,sqlite3,time,inquiry_mail,secrets
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
import calendar,re
STATUSES={'pending':'待联系','quoted':'已报价','reserved':'已预约','completed':'已完成','cancelled':'已取消'}
def initialize(path):
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS operators(user_id TEXT PRIMARY KEY,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS inquiry_followup(id TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'pending',note TEXT NOT NULL DEFAULT '',revision INTEGER NOT NULL DEFAULT 0,updated INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS inquiry_history(seq INTEGER PRIMARY KEY AUTOINCREMENT,inquiry_id TEXT NOT NULL,actor TEXT NOT NULL,status TEXT NOT NULL,note TEXT NOT NULL,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS inquiry_reads(user_id TEXT NOT NULL,inquiry_id TEXT NOT NULL,PRIMARY KEY(user_id,inquiry_id));
        ''')
def authorize(h,path):
    user=h.session()
    if not user:h.error(401,'请先登录管理员账号。');return None
    with sqlite3.connect(path) as db:
        if not db.execute('SELECT 1 FROM operators WHERE user_id=?',(user['id'],)).fetchone():h.error(403,'此账号没有管理权限。');return None
    return user
def item(row):
    value=json.loads(row[0]);value.update(status=row[1] or 'pending',note=row[2] or '',revision=row[3] or 0,updated=row[4] or value.get('created',0),unread=not bool(row[5]));return value
SELECT='SELECT i.body,f.status,f.note,f.revision,f.updated,r.inquiry_id FROM inquiries i LEFT JOIN inquiry_followup f ON f.id=i.id LEFT JOIN inquiry_reads r ON r.inquiry_id=i.id AND r.user_id=? '
START="COALESCE(NULLIF(json_extract(i.body,'$.startDate'),''),NULLIF(json_extract(i.body,'$.date'),''),NULLIF(substr(json_extract(i.body,'$.startAt'),1,10),''))"
END="COALESCE(NULLIF(json_extract(i.body,'$.endDate'),''),NULLIF(substr(json_extract(i.body,'$.endAt'),1,10),''),"+START+")"
SUBMITTED="date(i.created,'unixepoch','+8 hours')"
FROM="FROM inquiries i LEFT JOIN inquiry_followup f ON f.id=i.id "
def date_value(raw):
    if not raw:return None
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw):raise ValueError('日期格式不正确。')
    try:return date.fromisoformat(raw)
    except ValueError:raise ValueError('日期不正确。')
def filters(query,*,overview=False):
    status=query.get('status','');completion=query.get('completion','');basis=query.get('dateBasis','trip')
    if status and status not in STATUSES:raise ValueError('状态不正确。')
    if completion not in ('','open','completed','cancelled'):raise ValueError('完成筛选不正确。')
    if basis not in ('trip','submitted'):raise ValueError('日期类型不正确。')
    start=date_value(query.get('from',''));end=date_value(query.get('to',''))
    if start and end and end<start:raise ValueError('结束日期不能早于开始日期。')
    where='WHERE 1=1';params=[]
    if not overview:
        if status:where+=" AND COALESCE(f.status,'pending')=?";params.append(status)
        if completion=='open':where+=" AND COALESCE(f.status,'pending') NOT IN ('completed','cancelled')"
        elif completion:where+=" AND COALESCE(f.status,'pending')=?";params.append(completion)
    q=query.get('q','').strip()[:100]
    if q:
        q=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        where+=" AND (i.body LIKE ? ESCAPE '\\' OR COALESCE(f.note,'') LIKE ? ESCAPE '\\')";params.extend(['%'+q+'%']*2)
    if basis=='submitted':
        if start:where+=' AND '+SUBMITTED+'>=?';params.append(start.isoformat())
        if end:where+=' AND '+SUBMITTED+'<=?';params.append(end.isoformat())
    else:
        if start:where+=' AND '+END+'>=?';params.append(start.isoformat())
        if end:where+=' AND '+START+'<=?';params.append(end.isoformat())
    return where,params

def counts(db,query):
    where,params=filters(query,overview=True)
    result=dict(db.execute("SELECT COALESCE(f.status,'pending'),COUNT(*) "+FROM+where+" GROUP BY COALESCE(f.status,'pending')",params))
    return {key:result.get(key,0) for key in STATUSES}

def summary(db,query):
    today=datetime.now(timezone(timedelta(hours=8))).date()
    raw=query.get('month',today.strftime('%Y-%m'))
    if not re.fullmatch(r'\d{4}-\d{2}',raw):raise ValueError('月份格式不正确。')
    first=date_value(raw+'-01');last=first.replace(day=calendar.monthrange(first.year,first.month)[1])
    where,params=filters(query)
    # Aggregate all matching records, without the list's 50-row pagination limit.
    clip='';args=[first.isoformat(),last.isoformat(),*params]
    if query.get('dateBasis','trip')=='trip':
        for key,op in [('from','>='),('to','<=')]:
            if query.get(key):clip+=' AND days.day'+op+'?';args.append(query[key])
    rows=db.execute("WITH RECURSIVE days(day) AS (SELECT ? UNION ALL SELECT date(day,'+1 day') FROM days WHERE day<?) SELECT days.day,COUNT(events.id) FROM days LEFT JOIN (SELECT i.id,"+START+" AS start,"+END+" AS finish "+FROM+where+") events ON events.start<=days.day AND events.finish>=days.day"+clip+" GROUP BY days.day ORDER BY days.day",args).fetchall()
    undated=db.execute('SELECT COUNT(*) '+FROM+where+' AND ('+START+' IS NULL OR '+END+' IS NULL)',params).fetchone()[0]
    return {'counts':counts(db,query),'calendar':[{'date':r[0],'count':r[1]} for r in rows],'month':raw,'undated':undated,'updatedAt':int(time.time()),'today':today.isoformat()}

def get(h,path,route,query):
    user=authorize(h,path)
    if not user:return
    with sqlite3.connect(path) as db:
        db.execute('BEGIN')
        if route=='/api/operator/me':return h.reply(200,{'user':user})
        if route=='/api/operator/notifications':
            count=db.execute('SELECT COUNT(*) FROM inquiries i WHERE NOT EXISTS(SELECT 1 FROM inquiry_reads r WHERE r.inquiry_id=i.id AND r.user_id=?)',(user['id'],)).fetchone()[0]
            latest=db.execute('SELECT id FROM inquiries ORDER BY created DESC,id DESC LIMIT 1').fetchone()
            return h.reply(200,{'email':inquiry_mail.status(path),'unread':count,'total':db.execute('SELECT COUNT(*) FROM inquiries').fetchone()[0],'latestId':latest[0] if latest else None})
        if route=='/api/operator/detail':
            identity=query.get('id','');row=db.execute(SELECT+'WHERE i.id=?',(user['id'],identity)).fetchone()
            if not row:return h.error(404,'没有找到这条需求。')
            history=[dict(zip(['status','note','created'],r)) for r in db.execute('SELECT status,note,created FROM inquiry_history WHERE inquiry_id=? ORDER BY seq DESC',(identity,))]
            return h.reply(200,{'inquiry':item(row),'history':history})
        if route in ('/api/operator/inquiries','/api/operator/summary'):
            try:
                if route.endswith('/summary'):return h.reply(200,summary(db,query))
                offset=max(0,int(query.get('offset','0')))
                where,params=filters(query)
                sorting=query.get('sort','newest')
                if sorting not in ('newest','tripAsc','tripDesc'):raise ValueError('排序不正确。')
                order='i.created DESC,i.id DESC' if sorting=='newest' else 'CASE WHEN '+START+' IS NULL THEN 1 ELSE 0 END,'+START+(' ASC' if sorting=='tripAsc' else ' DESC')+',i.created DESC,i.id DESC'
                total=db.execute('SELECT COUNT(*) '+FROM+where,params).fetchone()[0]
                rows=db.execute(SELECT+where+' ORDER BY '+order+' LIMIT 50 OFFSET ?',[user['id'],*params,offset]).fetchall()
                return h.reply(200,{'inquiries':[item(r) for r in rows],'total':total,'counts':counts(db,query),'offset':offset,'updatedAt':int(time.time())})
            except ValueError as e:return h.error(400,str(e))
    return h.error(404,'没有找到此操作。')
def post(h,path,route,body):
    user=authorize(h,path)
    if not user:return
    if route=='/api/operator/mail-config':
        try:inquiry_mail.configure(Path(__file__).resolve().parent,body.get('authorizationCode'),config_path=getattr(h,'config_file',None))
        except ValueError:return h.error(400,'请输入QQ邮箱生成的16位SMTP授权码。')
        except OSError:return h.error(500,'服务器未能保存邮件配置，请稍后重试。')
        with sqlite3.connect(path) as db:
            db.execute("UPDATE inquiry_mail SET next_attempt=0 WHERE status='pending'")
            if body.get('sendTest') is True:inquiry_mail.enqueue(db,'YC-MAIL-TEST-'+secrets.token_hex(6).upper())
        inquiry_mail.start(path)
        return h.reply(200,{'ok':True,'testQueued':body.get('sendTest') is True})
    identity=body.get('id')
    if not isinstance(identity,str):return h.error(400,'需求编号不正确。')
    with sqlite3.connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM inquiries WHERE id=?',(identity,)).fetchone():return h.error(404,'没有找到这条需求。')
        if route=='/api/operator/seen':
            db.execute('INSERT OR IGNORE INTO inquiry_reads VALUES(?,?)',(user['id'],identity));db.commit();return h.reply(200,{'ok':True})
        if route=='/api/operator/update':
            status=body.get('status');note=body.get('note');revision=body.get('revision')
            if not isinstance(status,str) or status not in STATUSES or not isinstance(note,str) or len(note)>2000 or type(revision) is not int:return h.error(400,'请选择状态，备注最多2000字。')
            current=db.execute('SELECT revision FROM inquiry_followup WHERE id=?',(identity,)).fetchone()
            if revision!=(current[0] if current else 0):return h.error(409,'这条需求已被更新，请重新打开后保存。')
            now=int(time.time());db.execute('INSERT INTO inquiry_followup VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,note=excluded.note,revision=excluded.revision,updated=excluded.updated',(identity,status,note.strip(),revision+1,now));db.execute('INSERT INTO inquiry_history(inquiry_id,actor,status,note,created) VALUES(?,?,?,?,?)',(identity,user['id'],status,note.strip(),now));db.commit()
            return h.reply(200,{'ok':True,'revision':revision+1})
    return h.error(404,'没有找到此操作。')
