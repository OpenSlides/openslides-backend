from openslides_backend.shared.util import ONE_ORGANIZATION_FQID


def test_migration(write, finalize, assert_model):
    write({"type": "create", "fqid": ONE_ORGANIZATION_FQID, "fields": {"f": 1}})
    write({"type": "update", "fqid": ONE_ORGANIZATION_FQID, "fields": {"f": 2}})
    write({"type": "delete", "fqid": ONE_ORGANIZATION_FQID})
    write({"type": "restore", "fqid": ONE_ORGANIZATION_FQID})

    finalize("0001_limit_of_meetings")

    assert_model(
        ONE_ORGANIZATION_FQID,
        {"limit_of_meetings": 0, "f": 1, "meta_deleted": False, "meta_position": 1},
        position=1,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"limit_of_meetings": 0, "f": 2, "meta_deleted": False, "meta_position": 2},
        position=2,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"limit_of_meetings": 0, "f": 2, "meta_deleted": True, "meta_position": 3},
        position=3,
    )
    assert_model(
        ONE_ORGANIZATION_FQID,
        {"limit_of_meetings": 0, "f": 2, "meta_deleted": False, "meta_position": 4},
        position=4,
    )
