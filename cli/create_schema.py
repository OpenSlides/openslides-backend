from datastore.writer.app import register_services
from datastore.shared.postgresql_backend.create_schema import create_schema

def main() -> None:
    register_services()
    create_schema()

if __name__ == "__main__":
    main()
