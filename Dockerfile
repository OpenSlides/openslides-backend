FROM python:3.8.1-alpine3.11

RUN apk add build-base

WORKDIR /srv/code

EXPOSE 8000
EXPOSE 8001
EXPOSE 8002

COPY requirements_production.txt .
RUN pip install --no-cache-dir --requirement requirements_production.txt

COPY openslides_backend/ ./openslides_backend/

CMD [ "python", "-m", "openslides_backend" ]
