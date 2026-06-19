import multiprocessing

bind = "127.0.0.1:3001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"
