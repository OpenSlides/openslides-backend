ARG CONTEXT=prod

FROM python:3.10.18-slim-bookworm AS base

## Setup
ARG CONTEXT
ARG REQUIREMENTS_FILE_OVERWRITE=""
WORKDIR /app
ENV APP_CONTEXT=${CONTEXT}

### Apt-get and pip requirements installs handled by dev/dockerfile-installs.sh
COPY requirements/ requirements/
COPY ./dev/dockerfile-installs.sh ./dockerfile-installs.sh
RUN chmod +x ./dockerfile-installs.sh && \
    bash ./dockerfile-installs.sh "${APP_CONTEXT}" "${REQUIREMENTS_FILE_OVERWRITE}" && \
    rm ./dockerfile-installs.sh

# Environment
ENV PYTHONPATH=/app
ENV EMAIL_HOST=postfix
ENV EMAIL_PORT=25
ENV EMAIL_CONNECTION_SECURITY=NONE
ENV EMAIL_TIMEOUT=5
ENV EMAIL_ACCEPT_SELF_SIGNED_CERTIFICATE=false
ENV DEFAULT_FROM_EMAIL=noreply@example.com

## External Information
LABEL org.opencontainers.image.title="OpenSlides Backend Service"
LABEL org.opencontainers.image.description="Backend service for OpenSlides which provides actions and presenters."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-backend"

EXPOSE 9002
EXPOSE 9003

## Command
COPY ./dev/command.sh ./
RUN chmod +x command.sh
CMD ["./command.sh"]

HEALTHCHECK CMD curl --fail http://localhost:9002/system/action/health/ || curl --fail http://localhost:9003/system/presenter/health/ || exit 1

#HEALTHCHECK --interval=5m --timeout=2m --start-period=45s \
#   CMD (curl -f --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 "http://localhost:9002/system/action/health/xxx" && curl -f --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 "http://localhost:9003/system/presenter/health/") || bash -c 'kill -s 15 -1 && (sleep 10; kill -s 9 -1)'

ENTRYPOINT ["./entrypoint.sh"]

# Development Image
FROM base AS dev

COPY dev/.bashrc .
COPY dev/cleanup.sh .
COPY dev/run-lint.sh ./dev/

# Copy files which are mounted to make the full stack work
COPY scripts scripts
COPY cli cli
COPY data data
COPY meta meta

COPY Makefile .
COPY setup.cfg .
COPY dev/entrypoint.sh ./

RUN chmod 777 -R .
ENV OPENSLIDES_DEVELOPMENT=1

EXPOSE 5678

STOPSIGNAL SIGKILL

# Test Image (same as dev)
FROM dev AS tests

# Production Image
FROM base AS prod

# This disables root access for the enduser, which could pose a security risk
RUN adduser --system --no-create-home appuser

COPY scripts scripts
COPY entrypoint.sh ./
COPY openslides_backend openslides_backend
COPY meta meta
COPY data data

RUN chown appuser ./scripts/ && \
 chown appuser ./entrypoint.sh && \
 chown appuser ./openslides_backend && \
 chown appuser ./meta && \
 chown appuser ./command.sh && \
 chown appuser ./data

ARG VERSION=dev
RUN echo "$VERSION" > openslides_backend/version.txt

USER appuser
