import os

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ConnectionHandler


def create_schema() -> None:
    """
    Helper function to write the database schema into the database.
    """
    connection_handler = injector.get(ConnectionHandler)
    with connection_handler.get_connection_context():
        with connection_handler.get_current_connection().cursor() as cursor:
            path = os.path.realpath(
                os.path.join(os.getcwd(), os.path.dirname(__file__), "schema.sql")
            )
            cursor.execute(open(path).read(), [])
