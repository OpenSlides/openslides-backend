# openslides-media-service
Media service for OpenSlides 4

Delivers media files and resources for OpenSlides. It stores the data in the
database.

## Configuration
See `config_handling.py`:
```
"MEDIA_DATABASE_HOST": Host of the database (media-postgresql),
"MEDIA_DATABASE_PORT": Port of the database (5432),
"MEDIA_DATABASE_NAME": Name of the database (openslides),
"MEDIA_DATABASE_USER_FILE": Path to the (secret) file, which contains the
username (/run/secrets/media_database_user),
"MEDIA_DATABASE_PASSWORD_FILE": Path to the (secret) file, which contains the
password (/run/secrets/media_database_password),
"BLOCK_SIZE": The size of the blocks, the file is chunked into.
              Default 4096, 4096 seems to be a good default,
"PRESENTER_HOST": Host of the presenter service,
"PRESENTER_PORT": Port of the presenter service,
```
Some configs have a default (in brackets defaults from docker-compose.yml).

## Production setup:
Use the provided Dockerfile. It creates the tables in Postgresql, if they don't
exist before startup.

## Development:
We use docker to run the code.

The command `make run-tests` runs the tests.
The command `make run-cleanup` runs the code cleanup (black, isort, flake8).

