FROM python:3.8.5-slim-buster

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y curl ncat git mime-support gcc libc-dev libpq-dev

WORKDIR /app

COPY requirements/ requirements/
RUN . requirements/export_datastore_commit.sh && pip install --no-cache-dir --requirement requirements/requirements_production.txt

RUN adduser --system --no-create-home appuser
USER appuser

EXPOSE 9002
EXPOSE 9003
ENV PYTHONPATH /app

COPY scripts scripts
COPY entrypoint.sh ./
COPY openslides_backend openslides_backend
COPY migrations/*.py migrations/
COPY migrations/migrations migrations/migrations/.
COPY global global

ENV EMAIL_HOST postfix
ENV EMAIL_PORT 25
# ENV EMAIL_HOST_USER username
# ENV EMAIL_HOST_PASSWORD secret
# EMAIL_CONNECTION_SECURITY use NONE, STARTTLS or SSL/TLS
ENV EMAIL_CONNECTION_SECURITY NONE
ENV EMAIL_TIMEOUT 5
ENV EMAIL_ACCEPT_SELF_SIGNED_CERTIFICATE false
ENV DEFAULT_FROM_EMAIL noreply@example.com

LABEL org.opencontainers.image.title="OpenSlides Backend Service"
LABEL org.opencontainers.image.description="Backend service for OpenSlides which provides actions and presenters."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-backend"

ENTRYPOINT ["./entrypoint.sh"]
CMD [ "python", "-m", "openslides_backend" ]
