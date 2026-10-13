"""Authenticated operator inbox; role grants are available only through local CLI."""
import json,sqlite3,time,inquiry_mail,secrets
from pathlib import Path
STATUSES={'pending':'待联系','quoted':'已报价','reserved':'已预约'}
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
def get(h,path,route,query):
    user=authorize(h,path)
    if not user:return
    with sqlite3.connect(path) as db:
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
        if route=='/api/operator/inquiries':
            try:offset=max(0,int(query.get('offset','0')))
            except ValueError:return h.error(400,'页码不正确。')
            status=query.get('status','');q=query.get('q','').strip()[:100]
            if status and status not in STATUSES:return h.error(400,'状态不正确。')
            where='WHERE 1=1';params=[]
            if status:where+=" AND COALESCE(f.status,'pending')=?";params.append(status)
            if q:where+=' AND i.body LIKE ?';params.append('%'+q+'%')
            total=db.execute('SELECT COUNT(*) FROM inquiries i LEFT JOIN inquiry_followup f ON f.id=i.id '+where,params).fetchone()[0]
            rows=db.execute(SELECT+where+' ORDER BY i.created DESC,i.id DESC LIMIT 50 OFFSET ?',[user['id'],*params,offset]).fetchall()
            counts=dict(db.execute("SELECT COALESCE(f.status,'pending'),COUNT(*) FROM inquiries i LEFT JOIN inquiry_followup f ON f.id=i.id GROUP BY COALESCE(f.status,'pending')"))
            return h.reply(200,{'inquiries':[item(r) for r in rows],'total':total,'counts':counts,'offset':offset})
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
