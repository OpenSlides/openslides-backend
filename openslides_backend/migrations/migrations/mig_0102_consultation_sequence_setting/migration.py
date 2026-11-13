from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    Introduces the new meeting setting motions_enable_consultation_sequence.
    Sets it to false on all old meetings.
    """

    ORIGIN_COLLECTIONS = ["meeting"]
