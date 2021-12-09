from datastore.shared.postgresql_backend import setup_di as setup_di_postgres
from datastore.shared.postgresql_backend.create_schema import create_schema
from datastore.shared.services import setup_di as setup_di_services

setup_di_services()
setup_di_postgres()
create_schema()
