FROM python:3.8.5-slim-buster

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y curl git mime-support gcc libc-dev libpq-dev ncat wait-for-it

WORKDIR /app
RUN mkdir migrations

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

RUN adduser --system --no-create-home appuser
USER appuser

EXPOSE 9002
EXPOSE 9003

COPY wait.sh ./
COPY entrypoint.sh ./
COPY entrypoint-setup.sh ./
COPY openslides_backend openslides_backend

COPY migrations/migrate.py migrations/.
COPY migrations/migrations migrations/migrations/.

ENTRYPOINT ["./entrypoint.sh"]
CMD [ "python", "-m", "openslides_backend" ]
