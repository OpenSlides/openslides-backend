from openslides_backend.migrations.base import BaseMigration

from ..mig_0100_init_reldb.migration import ORIGIN_COLL


class Migration(BaseMigration):
    ORIGIN_COLLECTIONS = ORIGIN_COLL
