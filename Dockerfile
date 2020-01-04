FROM python:3.8-alpine

WORKDIR /srv/code

EXPOSE 8000

COPY requirements_production.txt .
RUN pip install --no-cache-dir --requirement requirements_production.txt

COPY gunicorn_conf.py .

CMD [ "gunicorn", "--config=python:gunicorn_conf", "openslides_backend.wsgi:application" ]

COPY openslides_backend/ ./openslides_backend/
