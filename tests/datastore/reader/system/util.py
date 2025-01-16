import json

from openslides_backend.services.database.event_types import EVENT_TYPE
from openslides_backend.shared.patterns import META_POSITION, strip_reserved_fields


def setup_data(connection, cursor, models, deleted=False):
    max_pos = max(m[META_POSITION] for _, m in models.items())
    cursor.execute(
        "insert into positions (user_id, migration_index) values "
        + ",".join(["(0, 1)"] * max_pos)
    )
    for weight, (fqid, model) in enumerate(models.items()):
        data = json.loads(json.dumps(model))
        strip_reserved_fields(data)
        cursor.execute(
            "insert into events (position, fqid, type, data, weight) values (%s, %s, %s, %s, %s)",
            [
                model[META_POSITION],
                fqid,
                EVENT_TYPE.CREATE,
                json.dumps(data),
                weight,
            ],
        )
        cursor.execute(
            "insert into models (fqid, data, deleted) values (%s, %s, %s)",
            [fqid, json.dumps(model), deleted],
        )
    connection.commit()
