"""WSGI application sharing the tested API handlers with the local preview service.

HTTP transport is provided by Gunicorn; static assets are served by nginx.
No socket server or SMTP thread starts simply by importing this module.
"""
import io,os,sqlite3
from types import SimpleNamespace
from urllib.parse import urlsplit
from flask import Flask,request,Response
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
import server as service

class RequestHandler(service.Handler):
    def __init__(self):
        self.headers=request.headers
        self.path=request.path+('?' + request.query_string.decode('latin1') if request.query_string else '')
        self.command=request.method
        self.client_address=(request.remote_addr or 'unknown',0)
        self.server=SimpleNamespace(server_port=urlsplit(request.url).port or (443 if request.is_secure else 80))
        self.rfile=io.BytesIO(request.get_data(cache=False))
        self.wfile=io.BytesIO();self.status=200;self.response_headers=[]
    def send_response(self,code,message=None):self.status=code
    def send_header(self,name,value):self.response_headers.append((name,str(value)))
    def end_headers(self):
        for name,value in [('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY'),('Referrer-Policy','strict-origin-when-cross-origin')]:self.send_header(name,value)
    def response(self):return Response(self.wfile.getvalue(),status=self.status,headers=self.response_headers)

def create_app(*,start_mail=True):
    app=Flask(__name__,static_folder=str(service.ROOT/'dist'),static_url_path='')
    app.config.update(MAX_CONTENT_LENGTH=16384,DEBUG=False,TESTING=False)
    if os.environ.get('YICHEN_TRUST_PROXY')=='1':
        # Valid only with one trusted nginx proxy and a loopback-only Gunicorn bind.
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=1)
    @app.route('/api/<path:subpath>',methods=['GET','POST'])
    @app.route('/_AMapService/<path:subpath>',methods=['GET'])
    def api(subpath):
        handler=RequestHandler()
        if request.method=='POST':handler.do_POST()
        else:handler.do_GET()
        return handler.response()
    @app.get('/')
    def index():return app.send_static_file('index.html')
    @app.after_request
    def cache_policy(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy']="base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'"
        if request.path=='/operator.html' or request.path.startswith('/api/'):
            response.headers['Cache-Control']='no-store'
        return response
    @app.get('/healthz')
    def health():
        try:
            with sqlite3.connect(service.DB.as_uri()+'?mode=ro',uri=True) as db:db.execute('SELECT 1').fetchone()
        except sqlite3.Error:return {'status':'unavailable'},503
        return {'status':'ok'}
    @app.errorhandler(HTTPException)
    def http_error(error):
        if error.code==404 and not request.path.startswith('/api/'):
            return app.send_static_file('404.html'),404
        return {'error':'请求无法处理，请检查提交信息。'},error.code
    if start_mail:service.inquiry_mail.start(service.DB)
    return app
