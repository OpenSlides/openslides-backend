from unittest import TestCase

from openslides_backend.shared.patterns import (
    collection_from_collectionfield,
    collectionfield_from_fqid_and_field,
    field_from_collectionfield,
)


class PatternsTest(TestCase):
    """
    Tests for some patterns helper functions.
    """

    def test_collection_from_collectionfield_ok(self) -> None:
        assert collection_from_collectionfield("model/field") == "model"

    def test_field_from_collectionfield_ok(self) -> None:
        assert field_from_collectionfield("model/field") == "field"

    def test_collectionfield_from_fqid_and_field_ok(self) -> None:
        assert collectionfield_from_fqid_and_field("model/1", "field") == "model/field"
