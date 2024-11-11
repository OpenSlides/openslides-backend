from openslides_backend.action.action_worker import ActionWorkerState


def test_migration(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "action_worker/1",
            "fields": {
                "id": 1,
                "name": "meeting.update",
                "state": ActionWorkerState.RUNNING,
                "created": 123456789,
                "timestamp": 123456790,
            },
        },
        {
            "type": "create",
            "fqid": "action_worker/2",
            "fields": {
                "id": 2,
                "name": "meeting.update",
                "state": ActionWorkerState.ABORTED,
                "created": 123456789,
                "timestamp": 123456789,
            },
        },
        {
            "type": "create",
            "fqid": "action_worker/3",
            "fields": {
                "id": 3,
                "name": "meeting.update",
                "state": ActionWorkerState.END,
                "created": 123456790,
                "timestamp": 123456790,
            },
        },
    )
    write(
        {"type": "delete", "fqid": "action_worker/2", "fields": {}},
    )

    finalize("0061_add_user_ids_to_action_workers")

    assert_model(
        "action_worker/1",
        {
            "id": 1,
            "name": "meeting.update",
            "state": ActionWorkerState.RUNNING,
            "created": 123456789,
            "timestamp": 123456790,
            "user_id": -1,
        },
    )
    assert_model(
        "action_worker/2",
        {
            "id": 2,
            "name": "meeting.update",
            "state": ActionWorkerState.ABORTED,
            "created": 123456789,
            "timestamp": 123456789,
            "meta_deleted": True,
        },
    )
    assert_model(
        "action_worker/3",
        {
            "id": 3,
            "name": "meeting.update",
            "state": ActionWorkerState.END,
            "created": 123456790,
            "timestamp": 123456790,
            "user_id": -1,
        },
    )
