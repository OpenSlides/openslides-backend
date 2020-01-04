import os

bind = "0.0.0.0:8000"
worker_tmp_dir = "/dev/shm"  # See https://pythonspeed.com/articles/gunicorn-in-docker/
timeout = int(os.environ.get("OPENSLIDES_WRITE_SERVICE_WORKER_TIMEOUT", "30"))
loglevel = "debug" if os.environ.get("OPENSLIDES_WRITE_SERVICE_DEBUG") else "info"
reload = loglevel == "debug"
