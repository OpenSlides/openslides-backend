from unittest.mock import MagicMock, patch

from openslides_backend.services.datastore.extended_adapter import (
    ExtendedDatastoreAdapter,
)
from openslides_backend.shared.filters import And, FilterOperator, Not, Or


def test_sql_to_filter_code_simple() -> None:
    ds = ExtendedDatastoreAdapter(MagicMock(), MagicMock(), MagicMock())
    with patch("openslides_backend.services.datastore.extended_adapter.eval") as mock:
        ds._filter_changed_models(MagicMock(), FilterOperator("test", "=", 1), [])
    assert (
        mock.call_args[0][0]
        == "{model['id']: {field: model[field] for field in mapped_fields if field in model} for fqid, model in self.changed_models.items() if fqid_collection(fqid) == collection and (model.get(\"test\") == 1)}"
    )


def test_sql_to_filter_code_complex() -> None:
    ds = ExtendedDatastoreAdapter(MagicMock(), MagicMock(), MagicMock())
    operator = FilterOperator("test", "=", 1)
    _filter = Or(operator, And(operator, Not(operator)))
    with patch("openslides_backend.services.datastore.extended_adapter.eval") as mock:
        ds._filter_changed_models(MagicMock(), _filter, [])
    assert (
        mock.call_args[0][0]
        == '{model[\'id\']: {field: model[field] for field in mapped_fields if field in model} for fqid, model in self.changed_models.items() if fqid_collection(fqid) == collection and ((model.get("test") == 1) or ((model.get("test") == 1) and (not (model.get("test") == 1))))}'
    )
