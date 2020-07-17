FROM python:3.8.1-alpine3.11

ARG REPOSITORY_URL="https://github.com/OpenSlides/openslides-backend"
ARG GIT_CHECKOUT=master
ARG OPENSLIDES_BACKEND_ACTION_PORT=9002
ARG OPENSLIDES_BACKEND_PRESENTER_PORT=9003

ENV OPENSLIDES_BACKEND_COMPONENT=all

WORKDIR /srv/code

RUN apk add --no-cache gcc musl-dev linux-headers git \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup

RUN git clone --no-checkout -- $REPOSITORY_URL . \
    && git checkout $COMMIT \
    && pip install --no-cache-dir --requirement requirements_production.txt \
    && chown -R appuser:appgroup /srv/code

EXPOSE ${OPENSLIDES_BACKEND_ACTION_PORT}
EXPOSE ${OPENSLIDES_BACKEND_PRESENTER_PORT}

CMD [ "python", "-m", "openslides_backend" ]
