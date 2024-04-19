import sys
from unittest.mock import MagicMock, patch

from openslides_backend.datastore.shared.postgresql_backend import filter_models
from openslides_backend.shared.filters import And, FilterOperator, Not, Or

# Hack to patch the eval function in the module - since the function has the same name as the
# module, the former shadows the latter.
filter_models_module = sys.modules[
    "openslides_backend.datastore.shared.postgresql_backend.filter_models"
]


@patch.object(filter_models_module, "eval")
class TestFilterModels:
    models = {"a/1": MagicMock()}

    def test_sql_to_filter_code_simple(self, mock) -> None:
        filter_models(self.models, "a", FilterOperator("test", "=", 1))
        assert mock.call_args[0][0] == 'model.get("test") == 1'

    def test_sql_to_filter_code_complex(self, mock) -> None:
        operator = FilterOperator("test", "=", 1)
        _filter = Or([operator, And([operator, Not(operator)])])
        filter_models(self.models, "a", _filter)
        assert (
            mock.call_args[0][0]
            == '(model.get("test") == 1) or ((model.get("test") == 1) and (not (model.get("test") == 1)))'
        )
