"""WorkBuddy 应用托管部署入口（临时在线预览用）。

与 wsgi.py 的分工：
- wsgi.py        → 正式服务器入口，强制校验真实 HTTPS 域名，未配置会拒绝启动。
- deploy_cloud.py → 本文件，用于 WorkBuddy 一键发布；监听 $PORT 并绑定 0.0.0.0。

两个特殊处理：
1. 发布工具会把 dist/ 当作构建输出目录排除，所以前端静态文件改用 webroot/ 副本提供。
2. YICHEN_PUBLIC_ORIGIN 必须等于真实托管域名，否则浏览器提交会被 CSRF 校验拒绝。

环境变量必须在导入 server 之前设置，因为 server 在导入时就会创建数据目录与数据库连接。
"""

import os

# 托管沙箱里项目目录可能只读，数据目录放到临时目录（临时预览，数据不保留）
if not os.environ.get('YICHEN_DATA_DIR'):
    os.environ['YICHEN_DATA_DIR'] = '/tmp/yichen-drive-data'

# 真实托管域名：首次发布拿到链接后回填，必须与访问地址完全一致
os.environ.setdefault('YICHEN_PUBLIC_ORIGIN', 'https://yichen-drive.app.workbuddy.host')

import server as service
from pathlib import Path
from webapp import create_app

app = create_app(start_mail=False)

# webapp 已注册 "/" 与静态文件路由，这里只把静态目录换成发布副本，
# 不新增路由，避免 endpoint 冲突；首页由 webapp 的 index 视图继续提供。
app.static_folder = str(Path(service.ROOT) / 'webroot')


if __name__ == '__main__':
    # 托管平台通过 PORT 注入端口；未注入时回落到 8000，避免 $PORT 展开为空导致启动失败
    port = int(os.environ.get('PORT') or 8000)
    app.run(host='0.0.0.0', port=port, threaded=True)
