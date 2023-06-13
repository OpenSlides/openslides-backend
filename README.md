# openslides-media-service
Media service for OpenSlides 4

Delivers media files and resources for OpenSlides. It stores the data in the
database.

## Configuration
- `MEDIA_DATABASE_HOST`: Host of the database (default: `postgres`)
- `MEDIA_DATABASE_PORT`: Port of the database (default: `5432`)
- `MEDIA_DATABASE_NAME`: Name of the database (default: `openslides`)
- `MEDIA_DATABASE_USER`: Name of the database user (default: `openslides`)
- `MEDIA_DATABASE_PASSWORD_FILE`: Path to the (secret) file, which contains the
password (default: `/run/secrets/postgres_password`; in dev mode the password is always assumed to be `openslides`)
- `MEDIA_BLOCK_SIZE`: The size of the blocks, the file is chunked into (default: `4096`)
- `MEDIA_CLIENT_CACHE_DURATION`: The duration in seconds a file should be cached by a client (default: `86400`; disabled when: `0`)
- `PRESENTER_HOST`: Host of the presenter service (default: `backend`)
- `PRESENTER_PORT`: Port of the presenter service (default: `9003`)

## Production setup
Use the provided Dockerfile. It creates the tables in Postgresql, if they don't
exist before startup.

## Development
We use docker to run the code.

The command `make run-tests` runs the tests.
The command `make run-cleanup` runs the code cleanup (black, isort, flake8).

