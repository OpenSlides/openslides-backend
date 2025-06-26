ARG CONTEXT=prod

FROM python:3.10.17-slim-bookworm as base

## Setup
ARG CONTEXT
ARG REQUIREMENTS_FILE_OVERWRITE=""
WORKDIR /app
ENV APP_CONTEXT=${CONTEXT}

### Query based on context value
ENV IGNORE_INSTALL_RECOMMENDS=${prod:+"--no-install-recommends"}
ENV CONTEXT_INSTALLS=${tests:+""}${prod:+"libc-dev"}${dev:+"make vim bash-completion"}

RUN CONTEXT_INSTALLS=$(case "$APP_CONTEXT" in \
    tests)  echo "";; \
    dev)    echo "make vim bash-completion";; \
    *)      echo "libc-dev" ;; esac) && \
    IGNORE_INSTALL_RECOMMENDS=${prod:+"--no-install-recommends"} && \
    apt-get -y update && apt-get -y upgrade && apt-get install ${IGNORE_INSTALL_RECOMMENDS} -y \
    curl \
    git \
    gcc \
    libpq-dev \
    libmagic1 \
    mime-support \
    ncat \
    ${CONTEXT_INSTALLS} && \
    rm -rf /var/lib/apt/lists/*

### Requirements file will be autoselected, unless an overwrite is given via ARG REQUIEREMENTS_FILE_OVERWRITE
COPY requirements/ requirements/
RUN REQUIREMENTS_FILE=$(case "$APP_CONTEXT" in \
    tests) echo "requirements_development.txt";; \
    dev)   echo "requirements_development.txt";; \
    *)     echo "requirements_production.txt" ;; esac) && \
    REQUIREMENTS_FILE=${REQUIEREMENTS_FILE_OVERWRITE:-$REQUIREMENTS_FILE} && \
    . requirements/export_service_commits.sh && pip install --no-cache-dir --requirement requirements/${REQUIREMENTS_FILE}

ENV PYTHONPATH /app

ENV EMAIL_HOST postfix
ENV EMAIL_PORT 25
ENV EMAIL_CONNECTION_SECURITY NONE
ENV EMAIL_TIMEOUT 5
ENV EMAIL_ACCEPT_SELF_SIGNED_CERTIFICATE false
ENV DEFAULT_FROM_EMAIL noreply@example.com

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

HEALTHCHECK CMD curl --fail http://localhost:9002/system/action/health/ && curl --fail http://localhost:9003/system/presenter/health/ || exit 1

#HEALTHCHECK --interval=5m --timeout=2m --start-period=45s \
#   CMD (curl -f --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 "http://localhost:9002/system/action/health/xxx" && curl -f --retry 6 --max-time 5 --retry-delay 10 --retry-max-time 60 "http://localhost:9003/system/presenter/health/") || bash -c 'kill -s 15 -1 && (sleep 10; kill -s 9 -1)'

ENTRYPOINT ["./entrypoint.sh"]

# Development Image
FROM base as dev

COPY dev/.bashrc .
COPY dev/cleanup.sh .

# Copy files which are mounted to make the full stack work
COPY scripts scripts
COPY cli cli
COPY data data
COPY meta meta

COPY Makefile .
COPY setup.cfg .
COPY dev/entrypoint.sh ./

RUN chmod 777 -R .

ENV OPENSLIDES_DEVELOPMENT 1

EXPOSE 5678

STOPSIGNAL SIGKILL

# Test Image (same as dev)
FROM dev as tests

# Production Image
FROM base as prod

# Große Sicherheitslücke hier umgehen:
# Das sorgt dafür dass alle Commands innerhalb des Containers als unprivilegierter User durchgeführt werden und nicht als root
RUN adduser --system --no-create-home appuser
USER appuser

COPY --chown=appuser:appuser scripts scripts
COPY --chown=appuser:appuser entrypoint.sh ./
COPY --chown=appuser:appuser openslides_backend openslides_backend
COPY --chown=appuser:appuser meta meta
COPY --chown=appuser:appuser data data

ARG VERSION=dev
RUN echo "$VERSION" > openslides_backend/version.txt
