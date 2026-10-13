# Run a single process with four request threads for a small initial SQLite site.
bind='127.0.0.1:8766'
workers=1
worker_class='gthread'
threads=4
preload_app=False
accesslog=None  # Do not log query strings containing customer search input.
errorlog='-'
loglevel='warning'
timeout=45
graceful_timeout=30
max_requests=2000
max_requests_jitter=200
