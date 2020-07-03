from collections import defaultdict
from typing import Any, Dict, Iterable, Tuple

import simplejson as json

from openslides_backend.shared.patterns import KEYSEPARATOR, FullQualifiedField


class HTTPTestEngine:

    TEST_POSITION = 1
    NEW_ID = 42

    def __init__(
        self, datastore_content: Dict[FullQualifiedField, Any], expected_write_data: str
    ) -> None:
        self.datastore_content = datastore_content
        self.expected_write_data = expected_write_data

    def retrieve(self, endpoint: str, data: str) -> Tuple[bytes, int]:
        return getattr(self, endpoint)(data)

    def get(self, data: str) -> Tuple[bytes, int]:
        payload = json.loads(data)
        collection, instance_id = payload["fqid"].split(KEYSEPARATOR)
        result: Dict[str, Any] = {}
        for fqfield, value in self.search(
            collection, int(instance_id), payload.get("mapped_fields")
        ):
            result[fqfield.field] = value
        return json.dumps(result).encode(), 200

    def get_many(self, data: str) -> Tuple[bytes, int]:
        payload = json.loads(data)
        result: Dict[str, Dict[int, Dict[str, Any]]] = {}
        for request in payload["requests"]:
            if not isinstance(request, dict):
                raise ValueError(
                    "Sending a list of GetManyRequests is required for this test engine."
                )
            result[request["collection"]] = defaultdict(dict)
            for instance_id in request["ids"]:
                for fqfield, value in self.search(
                    request["collection"],
                    instance_id,
                    mapped_fields=request.get("mapped_fields"),
                ):
                    result[request["collection"]][instance_id][fqfield.field] = value
        return json.dumps(result).encode(), 200

    def reserve_ids(self, data: str) -> Tuple[bytes, int]:
        return json.dumps({"ids": [self.NEW_ID]}).encode(), 200

    def write(self, data: str) -> Tuple[bytes, int]:
        expected = json.loads(self.expected_write_data)
        got = json.loads(data)
        # print(expected, got, sep="\n")
        assert expected == got, f"Expected {expected}, \n\n got {got}"
        return b"", 200

    def search(
        self, collection: str, instance_id: int, mapped_fields: Iterable[str] = None
    ) -> Iterable[Tuple[FullQualifiedField, Any]]:
        found = False
        for fqfield, value in self.datastore_content.items():
            if str(fqfield.collection) == collection and fqfield.id == instance_id:
                found = True
                if mapped_fields is None or fqfield.field in mapped_fields:
                    yield fqfield, value
        if found:
            if mapped_fields is None or "meta_position" in mapped_fields:
                yield FullQualifiedField(
                    fqfield.collection, fqfield.id, "meta_position"
                ), self.TEST_POSITION
