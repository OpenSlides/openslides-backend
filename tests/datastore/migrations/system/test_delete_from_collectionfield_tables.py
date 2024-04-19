def test_delete_from_tables(migration_handler, write, query_single_value, assert_count):
    write({"type": "create", "fqid": "a/1", "fields": {"f": 1}})
    write({"type": "update", "fqid": "a/1", "fields": {"f": 2}})

    assert query_single_value("select count(*) from collectionfields", []) > 0
    assert query_single_value("select count(*) from events_to_collectionfields", []) > 0

    migration_handler.delete_collectionfield_aux_tables()

    assert_count("collectionfields", 0)
    assert_count("events_to_collectionfields", 0)
