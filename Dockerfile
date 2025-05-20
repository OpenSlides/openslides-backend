FROM python:3.10.17-slim-bookworm

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y curl ncat git mime-support gcc libc-dev libpq-dev libmagic1

WORKDIR /app

COPY requirements/ requirements/
RUN . requirements/export_service_commits.sh && pip install --no-cache-dir --requirement requirements/requirements_production.txt

RUN adduser --system --no-create-home appuser
USER appuser

EXPOSE 9002
EXPOSE 9003
ENV PYTHONPATH /app

COPY --chown=appuser:appuser scripts scripts
COPY --chown=appuser:appuser entrypoint.sh ./
COPY --chown=appuser:appuser openslides_backend openslides_backend
COPY --chown=appuser:appuser meta meta
COPY --chown=appuser:appuser data data

ARG VERSION=dev
RUN echo "$VERSION" > openslides_backend/version.txt

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

HEALTHCHECK CMD curl --fail http://localhost:9002/system/action/health/ || curl --fail http://localhost:9003/system/presenter/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD exec python -m openslides_backend
