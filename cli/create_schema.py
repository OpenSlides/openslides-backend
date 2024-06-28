from openslides_backend.datastore.shared.postgresql_backend.create_schema import (
    create_schema,
)


def main() -> None:
    create_schema()


if __name__ == "__main__":
    main()
