#!/usr/bin/env python3
"""Run yourself in a terminal. Never paste the authorization code into chat."""
from pathlib import Path
from getpass import getpass
import re,os
root=Path(__file__).resolve().parent
print('QQ 邮件提醒配置；请输入 SMTP 授权码，不是邮箱登录密码。')
secret=getpass('授权码（输入隐藏）：').strip()
if not re.fullmatch(r'[A-Za-z0-9]{8,128}',secret):raise SystemExit('授权码格式不正确，未保存。')
values={'YICHEN_SMTP_HOST':'smtp.qq.com','YICHEN_SMTP_PORT':'465','YICHEN_SMTP_USER':'2712723487@qq.com','YICHEN_SMTP_PASSWORD':secret,'YICHEN_NOTIFY_EMAIL':'2712723487@qq.com'}
p=root/'.env';lines=p.read_text().splitlines() if p.exists() else []
lines=[line for line in lines if line.split('=',1)[0].strip() not in values]
lines.extend(k+'='+v for k,v in values.items())
# Private permissions are set when creating the file, before any secret is written.
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.fchmod(fd,0o600)
with os.fdopen(fd,'w') as f:f.write('\n'.join(lines)+'\n')
print('已保存到本机私有 .env。重启网站服务后开始发送新需求提醒；请勿分享 .env。')
