from urllib.parse import urlsplit
from webapp import create_app,service
origin=urlsplit(service.PUBLIC_ORIGIN)
if origin.scheme!='https' or not origin.hostname or origin.username or origin.password or origin.path or origin.query or origin.fragment or 'YOUR_DOMAIN' in service.PUBLIC_ORIGIN:
    raise RuntimeError('Set YICHEN_PUBLIC_ORIGIN to the final HTTPS origin before production startup.')
app=create_app()
