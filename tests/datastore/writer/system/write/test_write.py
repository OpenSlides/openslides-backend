import copy

import pytest

from openslides_backend.datastore.writer.flask_frontend.routes import WRITE_URL
from tests.datastore.util import assert_response_code
from tests.datastore.writer.system.util import assert_model


@pytest.fixture()
def data():
    yield copy.deepcopy(
        {
            "user_id": 1,
            "information": {},
            "locked_fields": {},
            "events": [{"type": "create", "fqid": "a/1", "fields": {"f": 1}}],
        }
    )


def create_model(json_client, data):
    fields = copy.deepcopy(data["events"][0]["fields"])
    response = json_client.post(WRITE_URL, data)
    assert_response_code(response, 201)
    assert_model("a/1", fields, 1)


def test_two_write_requests(json_client, data):
    create_model(json_client, data)

    data["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f": None}}
    data2 = copy.deepcopy(data)
    data2["events"][0] = {"type": "update", "fqid": "a/1", "fields": {"f2": 1}}
    response = json_client.post(WRITE_URL, [data, data2])
    assert_response_code(response, 201)
    assert_model("a/1", {"f2": 1}, 3)
