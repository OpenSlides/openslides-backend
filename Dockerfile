FROM python:3.8.5-alpine3.11

RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR /srv/code
COPY openslides_backend openslides_backend
COPY requirements.txt .

RUN pip install --no-cache-dir --requirement requirements.txt

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

EXPOSE 9002
EXPOSE 9003

CMD [ "python", "-m", "openslides_backend" ]
