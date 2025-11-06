from typing import Any


class TContext:
    def __init__(self) -> None:
        self.context: dict[str, dict[str, Any] | None] = {}

    def get_write_meeting_event(self, id_: int) -> dict[str, Any]:
        fqid = f"meeting/{id_}"
        self.context[fqid] = fields = {"id": id_, "name": f"Meeting {id_}"}
        return self.get_create_event(fqid, fields)

    def get_write_user_event(
        self, id_: int, username: str | None = None
    ) -> dict[str, Any]:
        fqid = f"user/{id_}"
        self.context[fqid] = fields = {"id": id_, "username": username or f"user{id_}"}
        return self.get_create_event(fqid, fields)

    def get_write_topic_events(self, id_: int, meeting_id: int) -> list[dict[str, Any]]:
        fqid = f"topic/{id_}"
        meeting_fqid = f"meeting/{meeting_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "title": f"Topic {id_}",
            "meeting_id": meeting_id,
        }
        if meeting_fields := self.context.get(meeting_fqid):
            meeting_fields["topic_ids"] = [*meeting_fields.get("topic_ids", []), id_]
            return [
                self.get_create_event(fqid, fields),
                self.get_update_event(
                    meeting_fqid, list_fields={"add": {"topic_ids": [id_]}}
                ),
            ]
        else:
            raise Exception(
                f"Bad setup creating topic {id_}: Meeting {meeting_id} does not exist"
            )

    def get_write_motion_events(
        self, id_: int, meeting_id: int
    ) -> list[dict[str, Any]]:
        fqid = f"motion/{id_}"
        meeting_fqid = f"meeting/{meeting_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "title": f"Motion {id_}",
            "meeting_id": meeting_id,
        }
        if meeting_fields := self.context.get(meeting_fqid):
            meeting_fields["motion_ids"] = [*meeting_fields.get("motion_ids", []), id_]
            return [
                self.get_create_event(fqid, fields),
                self.get_update_event(
                    meeting_fqid, list_fields={"add": {"motion_ids": [id_]}}
                ),
            ]
        else:
            raise Exception(
                f"Bad setup creating motion {id_}: Meeting {meeting_id} does not exist"
            )

    def get_write_assignment_events(
        self, id_: int, meeting_id: int
    ) -> list[dict[str, Any]]:
        fqid = f"assignment/{id_}"
        meeting_fqid = f"meeting/{meeting_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "title": f"Assignment {id_}",
            "meeting_id": meeting_id,
        }
        if meeting_fields := self.context.get(meeting_fqid):
            meeting_fields["assignment_ids"] = [
                *meeting_fields.get("assignment_ids", []),
                id_,
            ]
            return [
                self.get_create_event(fqid, fields),
                self.get_update_event(
                    meeting_fqid, list_fields={"add": {"assignment_ids": [id_]}}
                ),
            ]
        else:
            raise Exception(
                f"Bad setup creating assignment {id_}: Meeting {meeting_id} does not exist"
            )

    def get_write_position_events(
        self, id_: int, user_id: int, timestamp: int
    ) -> list[dict[str, Any]]:
        fqid = f"history_position/{id_}"
        user_fqid = f"user/{user_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "timestamp": timestamp,
            "original_user_id": user_id,
            "user_id": user_id,
        }
        events = [self.get_create_event(fqid, fields)]
        if user_fields := self.context[user_fqid]:
            user_fields["history_position_ids"] = [
                *user_fields.get("history_position_ids", []),
                id_,
            ]
            events.append(
                self.get_update_event(
                    user_fqid, list_fields={"add": {"history_position_ids": [id_]}}
                )
            )
        else:
            raise Exception(
                f"Bad setup creating position {id_}: User {user_id} does not exist"
            )
        return events

    def get_write_entry_events(
        self,
        id_: int,
        position_id: int,
        model_fqid: str,
        entries: list[str],
        meeting_id: int | None = None,
    ) -> list[dict[str, Any]]:
        fqid = f"history_entry/{id_}"
        model_fields = self.context[model_fqid]
        if not meeting_id:
            if model_fields and (model_meeting_id := model_fields["meeting_id"]):
                meeting_id = model_meeting_id
            else:
                raise Exception("Bad setup creating entry: No meeting_id found")
        meeting_fqid = f"meeting/{meeting_id}"
        position_fqid = f"history_position/{position_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "entries": entries,
            "original_model_id": model_fqid,
            "model_id": model_fqid,
            "position_id": position_id,
            "meeting_id": meeting_id,
        }
        events = [self.get_create_event(fqid, fields)]
        if position_fields := self.context[position_fqid]:
            position_fields["entry_ids"] = [*position_fields.get("entry_ids", []), id_]
            events.append(
                self.get_update_event(
                    position_fqid, list_fields={"add": {"entry_ids": [id_]}}
                )
            )
        else:
            raise Exception(
                f"Bad setup creating entry {id_}: Position {position_id} does not exist"
            )
        if meeting_fields := self.context[meeting_fqid]:
            meeting_fields["relevant_history_entry_ids"] = [
                *meeting_fields.get("relevant_history_entry_ids", []),
                id_,
            ]
            events.append(
                self.get_update_event(
                    meeting_fqid,
                    list_fields={"add": {"relevant_history_entry_ids": [id_]}},
                )
            )
        else:
            raise Exception(
                f"Bad setup creating entry {id_}: Meeting {meeting_id} does not exist"
            )
        if model_fields:
            model_fields["history_entry_ids"] = [
                *model_fields.get("history_entry_ids", []),
                id_,
            ]
            events.append(
                self.get_update_event(
                    model_fqid, list_fields={"add": {"history_entry_ids": [id_]}}
                )
            )
        else:
            raise Exception(
                f"Bad setup creating entry {id_}: {model_fqid} does not exist"
            )
        return events

    def get_delete_meeting_events(self, id_: int) -> list[dict[str, Any]]:
        """
        Deletes meeting and submodels,
        removes meeting reference from history entries
        """
        meeting_fqid = f"meeting/{id_}"
        if not (meeting_context := self.context[meeting_fqid]):
            return []

        events = [
            event
            for fqid in [
                *[f"motion/{id_}" for id_ in meeting_context.get("motion_ids", [])],
                *[
                    f"assignment/{id_}"
                    for id_ in meeting_context.get("assignment_ids", [])
                ],
                *[f"topic/{id_}" for id_ in meeting_context.get("topic_ids", [])],
            ]
            for event in self.get_delete_target_model_events(fqid)
        ]
        entry_fqids = [
            f"history_entry/{entry_id}"
            for entry_id in meeting_context.get("relevant_history_entry_ids", [])
        ]
        for entry_fqid in entry_fqids:
            if entry_fields := self.context[entry_fqid]:
                entry_fields["meeting_id"] = None
            events.append(
                self.get_update_event(entry_fqid, fields={"meeting_id": None})
            )
        events.append(self.get_delete_event(meeting_fqid))
        self.context[meeting_fqid] = None
        return events

    def get_delete_target_model_events(self, fqid: str) -> list[dict[str, Any]]:
        """
        Deletes the model,
        removes reference from the meeting back relation,
        removes reference from the history entries
        """
        split_fqid = fqid.split("/")
        collection = split_fqid[0]
        id_ = int(split_fqid[1])
        if not (context := self.context[fqid]):
            return []
        self.context[fqid] = None
        events = [self.get_delete_event(fqid)]
        meeting_fqid = f"meeting/{context['meeting_id']}"
        if meeting_fields := self.context[meeting_fqid]:

            def not_equals(a: int) -> bool:
                return a != id_

            back_relation = f"{collection}_ids"
            meeting_fields[back_relation] = list(
                filter(not_equals, meeting_fields[back_relation])
            )
            events.append(
                self.get_update_event(
                    meeting_fqid, list_fields={"remove": {back_relation: [id_]}}
                )
            )
        entry_fqids = [
            f"history_entry/{event_id}"
            for event_id in context.get("history_entry_ids", [])
        ]
        for entry_fqid in entry_fqids:
            if entry_fields := self.context[entry_fqid]:
                entry_fields["model_id"] = None
            events.append(self.get_update_event(entry_fqid, fields={"model_id": None}))
        return events

    def get_delete_user_events(self, id_: int) -> list[dict[str, Any]]:
        """
        Deletes user,
        removes reference from the history positions,
        removes reference from the history entries
        """
        fqid = f"user/{id_}"
        if not (context := self.context[fqid]):
            return []
        self.context[fqid] = None
        events = [self.get_delete_event(fqid)]
        entry_fqids = [
            f"history_entry/{event_id}"
            for event_id in context.get("history_entry_ids", [])
        ]
        for entry_fqid in entry_fqids:
            if entry_fields := self.context[entry_fqid]:
                entry_fields["model_id"] = None
            events.append(self.get_update_event(entry_fqid, fields={"model_id": None}))
        position_fqids = [
            f"history_position/{event_id}"
            for event_id in context.get("history_position_ids", [])
        ]
        for position_fqid in position_fqids:
            if position_fields := self.context[position_fqid]:
                position_fields["user_id"] = None
            events.append(
                self.get_update_event(position_fqid, fields={"user_id": None})
            )
        return events

    def get_delete_position_events(self, id_: int) -> list[dict[str, Any]]:
        """
        Deletes postion,
        deletes entries (via get_delete_entry_events function),
        removes reference from the user
        """
        fqid = f"history_position/{id_}"
        if not (context := self.context[fqid]):
            return []
        events: list[dict[str, Any]] = [
            event
            for entry_id in context["entry_ids"]
            for event in self.get_delete_entry_events(entry_id)
        ]
        if user_id := context.get("user_id"):
            user_fqid = f"user/{user_id}"
            if user_fields := self.context[user_fqid]:

                def not_equals(a: int) -> bool:
                    return a != id_

                user_fields["history_position_ids"] = list(
                    filter(not_equals, user_fields["history_position_ids"])
                )
                events.append(
                    self.get_update_event(
                        user_fqid,
                        list_fields={"remove": {"history_position_ids": [id_]}},
                    )
                )
        self.context[fqid] = None
        events.append(self.get_delete_event(fqid))
        return events

    def get_delete_entry_events(self, id_: int) -> list[dict[str, Any]]:
        """
        Deletes event,
        removes reference from the position,
        removes reference from the model,
        removes reference from the meeting
        """
        fqid = f"history_entry/{id_}"
        if not (context := self.context[fqid]):
            return []
        self.context[fqid] = None
        events = [self.get_delete_event(fqid)]

        def not_equals(a: int) -> bool:
            return a != id_

        if position_id := context.get("position_id"):
            position_fqid = f"history_position/{position_id}"
            if position_fields := self.context[position_fqid]:
                position_fields["entry_ids"] = list(
                    filter(not_equals, position_fields["entry_ids"])
                )
                events.append(
                    self.get_update_event(
                        position_fqid, list_fields={"remove": {"entry_ids": [id_]}}
                    )
                )
        if model_fqid := context.get("model_id"):
            if model_fields := self.context[model_fqid]:
                model_fields["history_entry_ids"] = list(
                    filter(not_equals, model_fields["history_entry_ids"])
                )
                events.append(
                    self.get_update_event(
                        model_fqid, list_fields={"remove": {"history_entry_ids": [id_]}}
                    )
                )
        if meeting_id := context.get("meeting_id"):
            meeting_fqid = f"meeting/{meeting_id}"
            if meeting_fields := self.context[meeting_fqid]:
                meeting_fields["relevant_history_entry_ids"] = list(
                    filter(not_equals, meeting_fields["relevant_history_entry_ids"])
                )
                events.append(
                    self.get_update_event(
                        meeting_fqid,
                        list_fields={"remove": {"relevant_history_entry_ids": [id_]}},
                    )
                )
        return events

    def get_create_event(self, fqid: str, fields: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "create",
            "fqid": fqid,
            "fields": fields,
        }

    def get_update_event(
        self,
        fqid: str,
        fields: dict[str, Any] = {},
        list_fields: dict[str, dict[str, list[str | int]]] = {},
    ) -> dict[str, Any]:
        return {
            "type": "update",
            "fqid": fqid,
            "fields": fields,
            "list_fields": list_fields,
        }

    def get_delete_event(self, fqid: str) -> dict[str, Any]:
        return {"type": "delete", "fqid": fqid}


def test_migration_simple(write, finalize, assert_model):
    """
    Tests the following cases:
    - Topic with history entry
    - Position with exactly one entry that should be deleted
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_topic_events(1, meeting_id=1),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "topic/1", ["Topic created"]),
    )

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": []})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "topic_ids": [1],
            "relevant_history_entry_ids": [],
        },
    )
    assert_model("topic/1", {"id": 1, "title": "Topic 1", "meeting_id": 1})
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": True,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/1",
            "model_id": "topic/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )


def test_migration_with_many_different_models(write, finalize, assert_model):
    """
    Tests the following cases:
    - Motion with history entry
    - Assignment with history entry
    - User with history entry
    - Position with entries that should be deleted and entries that should not be
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        ctx.get_write_user_event(2, "bob"),
        *ctx.get_write_motion_events(1, meeting_id=1),
        *ctx.get_write_assignment_events(1, meeting_id=1),
        *ctx.get_write_topic_events(1, meeting_id=1),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "user/2", ["User created"], meeting_id=1),
        *ctx.get_write_entry_events(2, 1, "motion/1", ["Motion created"]),
        *ctx.get_write_entry_events(3, 1, "assignment/1", ["Assignment created"]),
        *ctx.get_write_entry_events(4, 1, "topic/1", ["Topic created"]),
    )

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": [1]})
    assert_model("user/2", {"id": 2, "username": "bob", "history_entry_ids": [1]})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "motion_ids": [1],
            "assignment_ids": [1],
            "topic_ids": [1],
            "relevant_history_entry_ids": [1, 2, 3],
        },
    )
    assert_model(
        "motion/1",
        {"id": 1, "title": "Motion 1", "meeting_id": 1, "history_entry_ids": [2]},
    )
    assert_model(
        "assignment/1",
        {"id": 1, "title": "Assignment 1", "meeting_id": 1, "history_entry_ids": [3]},
    )
    assert_model("topic/1", {"id": 1, "title": "Topic 1", "meeting_id": 1})
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1, 2, 3],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "entries": ["User created"],
            "original_model_id": "user/2",
            "model_id": "user/2",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "model_id": "motion/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "entries": ["Assignment created"],
            "original_model_id": "assignment/1",
            "model_id": "assignment/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/1",
            "model_id": "topic/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )


def test_migration_multiple_deletable_entries(write, finalize, assert_model):
    """
    Tests the following cases:
    - Multiple positions
    - Topic with history entry
    - History entry with original_model_id from topic but topic itself was deleted
    - Deleted topic with non-deleted history entry
    - Position with multiple entries that should be deleted
    - Position with no user and exactly one entry that should be deleted
    - Position with no entries that should be deleted
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_topic_events(1, meeting_id=1),
        *ctx.get_write_topic_events(2, meeting_id=1),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "topic/1", ["Topic created"]),
        *ctx.get_write_entry_events(2, 1, "topic/2", ["Topic created"]),
    )
    write(
        ctx.get_write_user_event(2, "bob"),
        *ctx.get_write_position_events(2, user_id=1, timestamp=200),
        *ctx.get_write_entry_events(3, 2, "user/2", ["User created"], meeting_id=1),
    )
    write(
        *ctx.get_write_position_events(3, user_id=2, timestamp=300),
        *ctx.get_write_entry_events(4, 3, "topic/2", ["Topic deleted"]),
        *ctx.get_delete_target_model_events("topic/2"),
    )
    write(
        *ctx.get_write_position_events(4, user_id=2, timestamp=400),
        *ctx.get_write_entry_events(5, 4, "user/2", ["User deleted"], meeting_id=1),
        *ctx.get_delete_user_events(2),
    )

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": [2]})
    assert_model(
        "user/2",
        {
            "id": 2,
            "meta_deleted": True,
            "username": "bob",
            "history_position_ids": [3, 4],
            "history_entry_ids": [3, 5],
        },
    )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "topic_ids": [1],
            "relevant_history_entry_ids": [3, 5],
        },
    )
    assert_model("topic/1", {"id": 1, "title": "Topic 1", "meeting_id": 1})
    assert_model(
        "topic/2",
        {
            "id": 2,
            "meta_deleted": True,
            "title": "Topic 2",
            "meeting_id": 1,
            "history_entry_ids": [2, 4],
        },
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": True,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1, 2],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/1",
            "model_id": "topic/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/2",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_position/2",
        {
            "id": 2,
            "timestamp": 200,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [3],
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "entries": ["User created"],
            "original_model_id": "user/2",
            "position_id": 2,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_position/3",
        {
            "id": 3,
            "meta_deleted": True,
            "timestamp": 300,
            "original_user_id": 2,
            "entry_ids": [4],
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "meta_deleted": True,
            "entries": ["Topic deleted"],
            "original_model_id": "topic/2",
            "position_id": 3,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_position/4",
        {"id": 4, "timestamp": 400, "original_user_id": 2, "entry_ids": [5]},
    )
    assert_model(
        "history_entry/5",
        {
            "id": 5,
            "entries": ["User deleted"],
            "original_model_id": "user/2",
            "position_id": 4,
            "meeting_id": 1,
        },
    )


def test_migration_with_deleted_history_entries(write, finalize, assert_model):
    """
    Tests the following cases:
    - Ignore deleted history entries
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        ctx.get_write_user_event(2, "bob"),
        *ctx.get_write_motion_events(1, meeting_id=1),
        *ctx.get_write_assignment_events(1, meeting_id=1),
        *ctx.get_write_topic_events(1, meeting_id=1),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "user/2", ["User created"], meeting_id=1),
        *ctx.get_write_entry_events(2, 1, "motion/1", ["Motion created"]),
        *ctx.get_write_entry_events(3, 1, "assignment/1", ["Assignment created"]),
        *ctx.get_write_entry_events(4, 1, "topic/1", ["Topic created"]),
    )
    write(*ctx.get_delete_position_events(1))  # Delete entire history

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": []})
    assert_model("user/2", {"id": 2, "username": "bob", "history_entry_ids": []})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "motion_ids": [1],
            "assignment_ids": [1],
            "topic_ids": [1],
            "relevant_history_entry_ids": [],
        },
    )
    assert_model(
        "motion/1",
        {"id": 1, "title": "Motion 1", "meeting_id": 1, "history_entry_ids": []},
    )
    assert_model(
        "assignment/1",
        {"id": 1, "title": "Assignment 1", "meeting_id": 1, "history_entry_ids": []},
    )
    assert_model(
        "topic/1",
        {"id": 1, "title": "Topic 1", "meeting_id": 1, "history_entry_ids": []},
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": True,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "meta_deleted": True,
            "entries": ["User created"],
            "original_model_id": "user/2",
            "model_id": "user/2",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "meta_deleted": True,
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "model_id": "motion/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "meta_deleted": True,
            "entries": ["Assignment created"],
            "original_model_id": "assignment/1",
            "model_id": "assignment/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/1",
            "model_id": "topic/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )


def test_migration_multi_meeting(write, finalize, assert_model):
    """
    Tests the following cases:
    - With multiple meeting
    - With deleted meetings
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_topic_events(1, meeting_id=1),
        *ctx.get_write_topic_events(2, meeting_id=1),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "topic/1", ["Topic created"]),
        *ctx.get_write_entry_events(2, 1, "topic/2", ["Topic created"]),
    )
    write(
        ctx.get_write_meeting_event(2),
        *ctx.get_write_topic_events(3, meeting_id=2),
        *ctx.get_write_topic_events(4, meeting_id=2),
        *ctx.get_write_position_events(2, user_id=1, timestamp=200),
        *ctx.get_write_entry_events(3, 2, "topic/3", ["Topic created"]),
        *ctx.get_write_entry_events(4, 2, "topic/4", ["Topic created"]),
    )
    write(*ctx.get_delete_meeting_events(2))  # Delete meeting 2

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": []})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "topic_ids": [1, 2],
            "relevant_history_entry_ids": [],
        },
    )
    assert_model(
        "meeting/2",
        {
            "id": 2,
            "meta_deleted": True,
            "name": "Meeting 2",
            "topic_ids": [],
            "relevant_history_entry_ids": [3, 4],
        },
    )
    assert_model("topic/1", {"id": 1, "title": "Topic 1", "meeting_id": 1})
    assert_model("topic/2", {"id": 2, "title": "Topic 2", "meeting_id": 1})
    assert_model(
        "topic/3",
        {
            "id": 3,
            "meta_deleted": True,
            "title": "Topic 3",
            "meeting_id": 2,
            "history_entry_ids": [3],
        },
    )
    assert_model(
        "topic/4",
        {
            "id": 4,
            "meta_deleted": True,
            "title": "Topic 4",
            "meeting_id": 2,
            "history_entry_ids": [4],
        },
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": True,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1, 2],
        },
    )
    assert_model(
        "history_position/2",
        {
            "id": 2,
            "meta_deleted": True,
            "timestamp": 200,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [3, 4],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/1",
            "model_id": "topic/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/2",
            "model_id": "topic/2",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/3",
            "position_id": 2,
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "meta_deleted": True,
            "entries": ["Topic created"],
            "original_model_id": "topic/4",
            "position_id": 2,
        },
    )


# TODO: Write tests at least checking these cases:
# - Test for other not-allowed models
def test_migration_other_models(write, finalize, assert_model):
    """
    Tests the other models
    """
    ctx = TContext()
    write(
        ctx.get_write_user_event(1, "admin"),
        ctx.get_write_meeting_event(1),
    )
    data: dict[str, dict[str, Any]] = {
        "organization": {"name": "An organization"},
        "meeting_user": {"meeting_id": 1},
        "gender": {"name": "A gender"},
        "organization_tag": {"name": "Tagliatelle"},
        "theme": {"name": "Very colourful and pretty"},
        "committee": {"name": "Cute committee"},
        "structure_level": {"name": "green", "meeting_id": 1},
        "group": {"name": "Admin", "meeting_id": 1},
        "personal_note": {"note": "This is a note", "meeting_id": 1},
        "tag": {"name": "A tag", "meeting_id": 1},
        "agenda_item": {"meeting_id": 1},
        "list_of_speakers": {"meeting_id": 1},
        "structure_level_list_of_speakers": {"meeting_id": 1},
        "point_of_order_category": {"meeting_id": 1},
        "speaker": {"meeting_id": 1},
        "motion_submitter": {"meeting_id": 1},
        "motion_editor": {"meeting_id": 1},
        "motion_working_group_speaker": {"meeting_id": 1},
        "motion_comment": {"meeting_id": 1},
        "motion_comment_section": {"meeting_id": 1},
        "motion_category": {"meeting_id": 1},
        "motion_block": {"meeting_id": 1},
        "motion_change_recommendation": {"meeting_id": 1},
        "motion_state": {"meeting_id": 1},
        "motion_workflow": {"meeting_id": 1},
        "mediafile": {
            "title": "A mediafile",
            "owner_id": "meeting/1",
            "meeting_mediafile_ids": [1],
        },
        "meeting_mediafile": {
            "meeting_id": 1,
            "mediafile_id": 1,
            "is_public": True,
            "inherited_access_group_ids": [],
        },
        "projector": {"name": "Project OR", "meeting_id": 1},
        "projection": {"meeting_id": 1},
        "projector_message": {"meeting_id": 1},
        "projector_countdown": {"meeting_id": 1},
        "poll": {"meeting_id": 1},
        "option": {"meeting_id": 1},
        "vote": {"meeting_id": 1},
        "assignment_candidate": {"meeting_id": 1},
        "poll_candidate_list": {"meeting_id": 1},
        "poll_candidate": {"meeting_id": 1},
        "chat_group": {"meeting_id": 1},
        "chat_message": {"meeting_id": 1},
        "action_worker": {"name": "meeting.import"},
        "import_preview": {"name": "motion"},
    }
    meeting_back_realtions = [
        "meeting_user_ids",
        "structure_level_ids",
        "group_ids",
        "personal_note_ids",
        "tag_ids",
        "agenda_item_ids",
        "list_of_speakers_ids",
        "structure_level_list_of_speakers_ids",
        "point_of_order_category_ids",
        "speaker_ids",
        "motion_submitter_ids",
        "motion_editor_ids",
        "motion_working_group_speaker_ids",
        "motion_comment_ids",
        "motion_comment_section_ids",
        "motion_category_ids",
        "motion_block_ids",
        "motion_change_recommendation_ids",
        "motion_state_ids",
        "motion_workflow_ids",
        "mediafile_ids",
        "meeting_mediafile_ids",
        "projector_ids",
        "all_projection_ids",
        "projector_message_ids",
        "projector_countdown_ids",
        "poll_ids",
        "option_ids",
        "vote_ids",
        "assignment_candidate_ids",
        "poll_candidate_list_ids",
        "poll_candidate_ids",
        "chat_group_ids",
        "chat_message_ids",
    ]
    ctx.context.update(
        {f"{collection}/1": {"id": 1, **fields} for collection, fields in data.items()}
    )
    if meeting_context := ctx.context["meeting/1"]:
        meeting_context.update({field: [1] for field in meeting_back_realtions})
    write(
        ctx.get_update_event(
            "meeting/1", {field: [1] for field in meeting_back_realtions}
        ),
        *[
            ctx.get_create_event(f"{collection}/1", {"id": 1, **fields})
            for collection, fields in data.items()
        ],
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *[
            event
            for entry_id, collection in enumerate(data, 1)
            for event in ctx.get_write_entry_events(
                entry_id, 1, f"{collection}/1", [f"{collection} created"], meeting_id=1
            )
        ],
        *ctx.get_write_entry_events(
            len(data) + 1,
            1,
            "history_position/1",
            ["History position created"],
            meeting_id=1,
        ),
        *ctx.get_write_entry_events(
            len(data) + 2, 1, "history_entry/1", ["History entry created"], meeting_id=1
        ),
        *ctx.get_write_entry_events(
            len(data) + 3, 1, "meeting/1", ["Meeting updated"], meeting_id=1
        ),
    )

    finalize("0070_remove_mistakenly_created_history_entries")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": []})
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": True,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": list(range(1, len(data) + 4)),
        },
    )
    for entry_id, (collection, fields) in enumerate(data.items(), 1):
        fqid = f"{collection}/1"
        assert_model(fqid, {"id": 1, **fields})
        assert_model(
            f"history_entry/{entry_id}",
            {
                "id": entry_id,
                "meta_deleted": True,
                "position_id": 1,
                "model_id": fqid,
                "original_model_id": fqid,
                "entries": [f"{collection} created"],
                "meeting_id": 1,
            },
        )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "relevant_history_entry_ids": [],
            **{field: [1] for field in meeting_back_realtions},
        },
    )
    assert_model(
        f"history_entry/{len(data)+1}",
        {
            "id": len(data) + 1,
            "meta_deleted": True,
            "position_id": 1,
            "model_id": "history_position/1",
            "original_model_id": "history_position/1",
            "entries": ["History position created"],
            "meeting_id": 1,
        },
    )
    assert_model(
        f"history_entry/{len(data)+2}",
        {
            "id": len(data) + 2,
            "meta_deleted": True,
            "position_id": 1,
            "model_id": "history_entry/1",
            "original_model_id": "history_entry/1",
            "entries": ["History entry created"],
            "meeting_id": 1,
        },
    )
    assert_model(
        f"history_entry/{len(data)+3}",
        {
            "id": len(data) + 3,
            "meta_deleted": True,
            "position_id": 1,
            "model_id": "meeting/1",
            "original_model_id": "meeting/1",
            "entries": ["Meeting updated"],
            "meeting_id": 1,
        },
    )
