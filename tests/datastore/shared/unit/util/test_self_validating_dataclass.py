from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from openslides_backend.datastore.shared.util import (
    BadCodingError,
    InvalidFormat,
    SelfValidatingDataclass,
)
from openslides_backend.shared.patterns import (
    Collection,
    Field,
    FullQualifiedField,
    FullQualifiedId,
    Id,
    Position,
)


@dataclass
class A(SelfValidatingDataclass):
    fqid: FullQualifiedId
    collection: Collection
    field: Field
    fqfield: FullQualifiedField
    id: Id
    position: Position


def test_simple():
    fqid = MagicMock(name="fqid")
    collection = MagicMock(name="collection")
    field = MagicMock(name="field")
    fqfield = MagicMock(name="fqfield")
    id = MagicMock(name="id")
    position = MagicMock(name="position")
    position.__le__.return_value = False

    with (
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_collection"
        ) as assert_is_collection,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
        ) as assert_is_fqid,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqfield"
        ) as assert_is_fqfield,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_field"
        ) as assert_is_field,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_id"
        ) as assert_is_id,
    ):
        A(fqid, collection, field, fqfield, id, position)

        assert_is_collection.assert_called_with(collection)
        assert_is_field.assert_called_with(field)
        assert_is_fqfield.assert_called_with(fqfield)
        assert_is_fqid.assert_called_with(fqid)
        assert_is_id.assert_called_with(str(id))
        position.__le__.assert_called_with(0)


@dataclass
class B(SelfValidatingDataclass):
    list: list[FullQualifiedId]
    position: Position | None = None


def test_extended():
    fqid = MagicMock(name="fqid")
    position = MagicMock(name="position")
    position.__le__.return_value = True

    with patch(
        "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid:
        with pytest.raises(InvalidFormat):
            B([fqid], position)

        assert_is_fqid.assert_called_with(fqid)
        position.__le__.assert_called_with(0)


def test_optional():
    fqid = MagicMock(name="fqid")

    with patch(
        "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
    ):
        # test that no position is okay because it's optional
        B([fqid])


class SomeClass:
    pass


@dataclass
class C(SelfValidatingDataclass):
    field: list[SomeClass] | list[FullQualifiedId]


def test_union_of_lists_with_fqid_success():
    fqid: Any = MagicMock(name="fqid")

    with patch(
        "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid:
        C([fqid])
        assert_is_fqid.assert_called_with(fqid)


def test_union_of_lists_with_fqid_fail():
    fqid: Any = MagicMock(name="fqid")

    with patch(
        "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid:
        assert_is_fqid.side_effect = InvalidFormat("msg")
        with pytest.raises(InvalidFormat):
            C([fqid])
        assert_is_fqid.assert_called_with(fqid)


def test_union_of_lists_with_some_class():
    some_class = SomeClass()

    with patch(
        "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
    ) as assert_is_fqid:
        C([some_class])
        assert_is_fqid.assert_not_called()


@dataclass
class D(SelfValidatingDataclass):
    field: list[FullQualifiedId] | list[FullQualifiedField]


def test_union_of_lists_with_fqid_and_fqfield_success_1():
    fqid = MagicMock()

    with (
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
        ) as assert_is_fqid,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqfield"
        ) as assert_is_fqfield,
    ):
        D([fqid])
        assert_is_fqid.assert_called_with(fqid)
        assert_is_fqfield.assert_not_called()


def test_union_of_lists_with_fqid_and_fqfield_success_2():
    fqfield = MagicMock()

    with (
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
        ) as assert_is_fqid,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqfield"
        ) as assert_is_fqfield,
    ):
        assert_is_fqid.side_effect = InvalidFormat("msg")
        D([fqfield])

        assert_is_fqid.assert_called_with(fqfield)
        assert_is_fqfield.assert_called_with(fqfield)


def test_union_of_lists_with_fqid_and_fqfield_fail():
    data = MagicMock()

    with (
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqid"
        ) as assert_is_fqid,
        patch(
            "openslides_backend.datastore.shared.util.self_validating_dataclass.assert_is_fqfield"
        ) as assert_is_fqfield,
    ):
        assert_is_fqid.side_effect = InvalidFormat("msg")
        assert_is_fqfield.side_effect = InvalidFormat("msg")

        with pytest.raises(InvalidFormat):
            D([data])

        assert_is_fqid.assert_called_with(data)
        assert_is_fqfield.assert_called_with(data)


class AnotherClass:
    pass


@dataclass
class E(SelfValidatingDataclass):
    field: list[SomeClass] | list[AnotherClass]


def test_union_of_lists_invalid_data():
    data: Any = MagicMock()

    with pytest.raises(BadCodingError):
        E([data])
