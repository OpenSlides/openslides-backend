from openslides_backend.datastore.shared.postgresql_backend import \
    setup_di as postgresql_setup_di
from openslides_backend.datastore.shared.services import \
    setup_di as util_setup_di
from openslides_backend.datastore.writer import setup_di as writer_setup_di


def register_services():
    util_setup_di() # EnvironmentService, ShutdownService
    postgresql_setup_di()
    writer_setup_di()
