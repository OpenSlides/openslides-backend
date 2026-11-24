from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    """
    Introduces the new schema changes for the idp matching feature.
    One new meeting, committeee and orga setting each
    and the three new collections idm_mapper, idm_condition and idm_mapping.
    """

    ORIGIN_COLLECTIONS = ["meeting", "committee", "organization"]
