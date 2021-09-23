FROM python:3.8.5-slim-buster

RUN apt-get update && apt-get install --yes bash-completion vim postgresql-client redis-tools wait-for-it gcc libc-dev libpq-dev curl

WORKDIR /app
RUN mkdir /datastore-service

COPY requirements.txt .

RUN pip install --no-cache-dir --requirement requirements.txt

COPY .bashrc ./
COPY entrypoint.sh ./

EXPOSE 5678
ENV OPENSLIDES_DEVELOPMENT 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["sleep", "infinity"]
