from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.services import ReadDatabase


def test_get_current_migration_index(
    migration_handler,
    write,
    set_migration_index_to_1,
    connection_handler,
):
    read_db = injector.get(ReadDatabase)
    with connection_handler.get_connection_context():
        assert read_db.get_current_migration_index() == -1

    write({"type": "create", "fqid": "a/1", "fields": {"f": [1]}})
    set_migration_index_to_1()

    with connection_handler.get_connection_context():
        assert read_db.get_current_migration_index() == 1
