from . import core, flask_frontend, postgresql_backend


def setup_di():
    from openslides_backend.datastore.shared.di import injector

    from .core import Database
    from .core import setup_di as core_setup_di
    from .postgresql_backend import SqlDatabaseBackendService
    from .postgresql_backend import setup_di as postgresql_backend_setup_di

    core_setup_di()
    postgresql_backend_setup_di()
    injector.register(Database, SqlDatabaseBackendService)
