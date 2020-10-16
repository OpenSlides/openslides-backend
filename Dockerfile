FROM python:3.8.5-slim-buster

WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade && \
  apt-get install --no-install-recommends -y \
    postgresql-client libpq-dev python3-dev gcc

COPY requirements_production.txt requirements_production.txt
RUN pip install -r requirements_production.txt

COPY src/* src/
COPY entrypoint.sh .

EXPOSE 9006
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:9006", "src.mediaserver:app"]
