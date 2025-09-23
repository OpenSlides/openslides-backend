# TODO This README is not up to date and needs to be updated before merging back into main branch.
# Migrations for the Datastore

The `migrate.py` script is the main entrypoint to execute migrations. The migrations itself are in the `migrations` folder. Each file can be arbitrarily named but must include a class called `Migration` that can be found by the loader. Note that all docker related files in this folder are only for **developing** migrations, not execute them. For execution in the dev mode, see the actual backend target for the dockerfile (`target dev`) and `dev/entrypoint.sh`.

There are three ways to execute migrations:

## 1) Developing migrations
This is done within the dockersetup in this folder. Note that the datastore needs to be checked out with the name `openslides-datastore-service` next to the backend repository.

- checkout the current datastore (in ../../openslides-datastore-service) and the current backend.
- `make run-dev`: Starts the compose setup -> A shell opens with the ability to run `migrate.py` and auxillary scripts.
- You can exit from it with `exit` and shut down the docker setup with `make stop-dev`
- You can write migrations in the backend and also adjust the Datastore at the same time since both are mounted into the container.

The following scripts can be used to make snapshots and trying out new migrations

#### Scripts for setting initial data
Only the current dataset is exported, so after a (re-)import, only one position exists in the datastore. Also note that importing clears the old content

- `export-data-only.sh` [to:export.json]
- `import-data-only.sh` [from:export.json]

#### Scripts for the full backup (Does a DB dump)
- `export-events.sh` [to:export.sql]
- `import-events.sh` [from:export.sql]

#### Downloading example data
- `fetch-example-data.sh` [to:example-data.json]


## 2) Migrations in dev mode

They are run before the backend starts. It is ensured that is is not scaled, so this is fine regarding race conditions. See `dev/entrypoint.sh` for the usage

## 3) Migrations in production:

See [migration route docs](/docs/migration_route.md).
