from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    Introduces the new schema changes for the idp matching feature.
    One new meeting, committeee and orga setting each
    and the three new collections idp_mapper, idp_condition and idp_mapping.
    """

    ORIGIN_COLLECTIONS = ["meeting", "committee", "organization"]
