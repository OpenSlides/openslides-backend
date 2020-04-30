from unittest.mock import Mock

from openslides_backend.services.database import DatabaseAdapter
from openslides_backend.shared.patterns import Collection, FullQualifiedId

engine = Mock()
log = Mock()

db = DatabaseAdapter(engine, log)


def test_get() -> None:
    fqid = FullQualifiedId(Collection("fakeModel"), 1)
    fields = ["a", "b", "c"]
    data = {
        "command": "get",
        "parameters": {"fqid": str(fqid), "mapped_fields": fields},
    }
    partial_model, num = db.get(fqid, fields)
    assert num is not None
    assert partial_model is not None
    assert partial_model["foo"] == "bar"
    engine.get.assert_called_with(data)
