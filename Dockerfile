FROM python:3.8.1

RUN apt-get -y update && apt-get -y upgrade && \
  apt-get install --no-install-recommends -y \
    postgresql-client

WORKDIR /app
#ENV FLASK_APP mediafileserver.py

COPY requirements_production.txt requirements_production.txt
RUN pip install -r requirements_production.txt

COPY src/* src/
COPY entrypoint.sh .

EXPOSE 8000
# TODO: Make the port configurable via ENV
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8000", "src.mediaserver:app"]
