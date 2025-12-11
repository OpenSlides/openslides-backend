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

    def get_write_model_events(
        self, id_: int, meeting_id: int, collection: str
    ) -> list[dict[str, Any]]:
        fqid = f"{collection}/{id_}"
        meeting_fqid = f"meeting/{meeting_id}"
        self.context[fqid] = fields = {
            "id": id_,
            "title": f"{collection.capitalize()} {id_}",
            "meeting_id": meeting_id,
        }
        if meeting_fields := self.context.get(meeting_fqid):
            meeting_fields[f"{collection}_ids"] = [
                *meeting_fields.get(f"{collection}_ids", []),
                id_,
            ]
            return [
                self.get_create_event(fqid, fields),
                self.get_update_event(
                    meeting_fqid, list_fields={"add": {f"{collection}_ids": [id_]}}
                ),
            ]
        else:
            raise Exception(
                f"Bad setup creating {collection} {id_}: Meeting {meeting_id} does not exist"
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

    def get_delete_meeting_events(
        self, id_: int, make_history_changes: bool = True
    ) -> list[dict[str, Any]]:
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
        if make_history_changes:
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

    def get_delete_target_model_events(
        self, fqid: str, make_history_changes: bool = True
    ) -> list[dict[str, Any]]:
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
        if make_history_changes:
            entry_fqids = [
                f"history_entry/{event_id}"
                for event_id in context.get("history_entry_ids", [])
            ]
            for entry_fqid in entry_fqids:
                if entry_fields := self.context[entry_fqid]:
                    entry_fields["model_id"] = None
                events.append(
                    self.get_update_event(entry_fqid, fields={"model_id": None})
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
    Motion with deleted meeting will have its meeting_id removed.
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_model_events(1, meeting_id=1, collection="motion"),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "motion/1", ["Motion created"], 1),
        *ctx.get_delete_meeting_events(1, False),
    )

    finalize("0072_unset_deleted_meeting_id_in_history_entry")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": [1]})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "meta_deleted": True,
            "name": "Meeting 1",
            "motion_ids": [],
            "relevant_history_entry_ids": [1],
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "meta_deleted": True,
            "history_entry_ids": [1],
            "title": "Motion 1",
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": False,
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
            "meta_deleted": False,
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "position_id": 1,
        },
    )


def test_migration_not_deleted(write, finalize, assert_model):
    """
    Tests the following cases:
    Motion with deleted meeting will have its meeting_id removed.
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_model_events(1, meeting_id=1, collection="motion"),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "motion/1", ["Motion created"], 1),
    )

    finalize("0072_unset_deleted_meeting_id_in_history_entry")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": [1]})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "meta_deleted": False,
            "name": "Meeting 1",
            "motion_ids": [1],
            "relevant_history_entry_ids": [1],
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "meta_deleted": False,
            "history_entry_ids": [1],
            "title": "Motion 1",
            "meeting_id": 1,
        },
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "meta_deleted": False,
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
            "meta_deleted": False,
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "model_id": "motion/1",
            "meeting_id": 1,
            "position_id": 1,
        },
    )


def test_migration_multiple_deletable_entries(write, finalize, assert_model):
    """
    Tests the following cases:
    - Multiple meetings, motions and positions
    """
    ctx = TContext()
    write(ctx.get_write_user_event(1, "admin"))
    write(
        ctx.get_write_meeting_event(1),
        *ctx.get_write_model_events(1, meeting_id=1, collection="motion"),
        *ctx.get_write_model_events(2, meeting_id=1, collection="motion"),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_position_events(2, user_id=1, timestamp=200),
        *ctx.get_write_entry_events(1, 1, "motion/1", ["Motion created"], 1),
        *ctx.get_write_entry_events(2, 2, "motion/2", ["Motion created"], 1),
    )
    write(
        ctx.get_write_meeting_event(2),
        *ctx.get_write_model_events(3, meeting_id=2, collection="motion"),
        *ctx.get_write_model_events(4, meeting_id=2, collection="motion"),
        *ctx.get_write_position_events(3, user_id=1, timestamp=300),
        *ctx.get_write_position_events(4, user_id=1, timestamp=400),
        *ctx.get_write_entry_events(3, 3, "motion/3", ["Motion created"], 2),
        *ctx.get_write_entry_events(4, 3, "motion/4", ["Motion created"], 2),
        *ctx.get_write_entry_events(5, 4, "motion/3", ["Motion deleted"], 2),
        *ctx.get_write_entry_events(6, 4, "motion/4", ["Motion deleted"], 2),
    )
    write(
        *ctx.get_delete_meeting_events(1, False),
        *ctx.get_delete_meeting_events(2, False),
    )

    finalize("0072_unset_deleted_meeting_id_in_history_entry")

    assert_model(
        "user/1", {"id": 1, "username": "admin", "history_position_ids": [1, 2, 3, 4]}
    )
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "meta_deleted": True,
            "motion_ids": [],
            "relevant_history_entry_ids": [1, 2],
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "meta_deleted": True,
            "history_entry_ids": [1],
            "title": "Motion 1",
            "meeting_id": 1,
        },
    )
    assert_model(
        "motion/2",
        {
            "id": 2,
            "meta_deleted": True,
            "title": "Motion 2",
            "meeting_id": 1,
            "history_entry_ids": [2],
        },
    )
    assert_model(
        "history_position/1",
        {
            "id": 1,
            "timestamp": 100,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [1],
        },
    )
    assert_model(
        "history_position/2",
        {
            "id": 2,
            "timestamp": 200,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [2],
        },
    )
    assert_model(
        "history_entry/1",
        {
            "id": 1,
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "position_id": 1,
        },
    )
    assert_model(
        "history_entry/2",
        {
            "id": 2,
            "entries": ["Motion created"],
            "original_model_id": "motion/2",
            "position_id": 2,
        },
    )
    assert_model(
        "history_position/3",
        {
            "id": 3,
            "timestamp": 300,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [3, 4],
        },
    )
    assert_model(
        "history_position/4",
        {
            "id": 4,
            "timestamp": 400,
            "original_user_id": 1,
            "user_id": 1,
            "entry_ids": [5, 6],
        },
    )
    assert_model(
        "history_entry/3",
        {
            "id": 3,
            "entries": ["Motion created"],
            "original_model_id": "motion/3",
            "position_id": 3,
        },
    )
    assert_model(
        "history_entry/4",
        {
            "id": 4,
            "entries": ["Motion created"],
            "original_model_id": "motion/4",
            "position_id": 3,
        },
    )
    assert_model(
        "history_entry/5",
        {
            "id": 5,
            "entries": ["Motion deleted"],
            "original_model_id": "motion/3",
            "position_id": 4,
        },
    )
    assert_model(
        "history_entry/6",
        {
            "id": 6,
            "entries": ["Motion deleted"],
            "original_model_id": "motion/4",
            "position_id": 4,
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
        *ctx.get_write_model_events(1, meeting_id=1, collection="motion"),
        *ctx.get_write_position_events(1, user_id=1, timestamp=100),
        *ctx.get_write_entry_events(1, 1, "motion/1", ["Motion created"]),
    )
    write(*ctx.get_delete_position_events(1))  # Delete entire history

    finalize("0072_unset_deleted_meeting_id_in_history_entry")

    assert_model("user/1", {"id": 1, "username": "admin", "history_position_ids": []})
    assert_model(
        "meeting/1",
        {
            "id": 1,
            "name": "Meeting 1",
            "motion_ids": [1],
            "relevant_history_entry_ids": [],
        },
    )
    assert_model(
        "motion/1",
        {"id": 1, "title": "Motion 1", "meeting_id": 1, "history_entry_ids": []},
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
            "entries": ["Motion created"],
            "original_model_id": "motion/1",
            "model_id": "motion/1",
            "position_id": 1,
            "meeting_id": 1,
        },
    )
