FROM python:3.8.5-slim-buster

WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade && \
  apt-get install --no-install-recommends -y \
    postgresql-client libpq-dev python3-dev gcc git

COPY requirements_production.txt requirements_production.txt
RUN pip install -r requirements_production.txt

COPY src/* src/
COPY scripts/entrypoint.sh .
COPY scripts/service_env.sh scripts/

LABEL org.opencontainers.image.title="OpenSlides Media Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which delivers media files."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-media-service"

EXPOSE 9006
ENTRYPOINT ["./entrypoint.sh"]
CMD exec gunicorn -b 0.0.0.0:9006 src.mediaserver:app
