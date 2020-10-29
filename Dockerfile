FROM python:3.8.5-slim-buster

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y curl git

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

RUN adduser --system --no-create-home appuser
USER appuser

EXPOSE 9002
EXPOSE 9003

COPY openslides_backend openslides_backend

CMD [ "python", "-m", "openslides_backend" ]
