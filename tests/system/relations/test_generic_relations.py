from ..action.base import BaseActionTestCase
from .setup import FakeModelA, SingleRelationHandlerWithContext


class GenericRelationsTest(BaseActionTestCase):
    def test_generic_O2O_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            instance={"id": 1, "fake_model_b_generic_oo": 2},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_oo": {
                "type": "add",
                "value": "fake_model_a/1",
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_O2O_replace(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {},
                "fake_model_a/2": {"fake_model_b_generic_oo": 3},
                "fake_model_b/3": {"fake_model_a_generic_oo": "fake_model_a/2"},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            instance={"id": 1, "fake_model_b_generic_oo": 3},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_generic_oo": {
                "type": "add",
                "value": "fake_model_a/1",
                "modified_element": "fake_model_a/1",
            },
            "fake_model_a/2/fake_model_b_generic_oo": {
                "modified_element": 3,
                "type": "remove",
                "value": None,
            },
        }
        assert result == expected

    def test_generic_O2O_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_generic_oo": 2},
                "fake_model_b/2": {"fake_model_a_generic_oo": "fake_model_a/1"},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            instance={"id": 1, "fake_model_b_generic_oo": None},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_oo": {
                "type": "remove",
                "value": None,
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_O2M_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            instance={"id": 1, "fake_model_b_generic_om": 2},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_mo": {
                "type": "add",
                "value": ["fake_model_a/1"],
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_O2M_add(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_generic_om": 3},
                "fake_model_a/2": {},
                "fake_model_b/3": {"fake_model_a_generic_mo": ["fake_model_a/1"]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            instance={"id": 2, "fake_model_b_generic_om": 3},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_generic_mo": {
                "type": "add",
                "value": ["fake_model_a/1", "fake_model_a/2"],
                "modified_element": "fake_model_a/2",
            }
        }
        assert result == expected

    def test_generic_O2M_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_generic_om": 2},
                "fake_model_b/2": {"fake_model_a_generic_mo": ["fake_model_a/1"]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            instance={"id": 1, "fake_model_b_generic_om": None},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_mo": {
                "type": "remove",
                "value": [],
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_M2M_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            instance={"id": 1, "fake_model_b_generic_mm": [2]},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_mm": {
                "type": "add",
                "value": ["fake_model_a/1"],
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_M2M_add(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_generic_mm": [3]},
                "fake_model_a/2": {},
                "fake_model_b/3": {"fake_model_a_generic_mm": ["fake_model_a/1"]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            instance={"id": 2, "fake_model_b_generic_mm": [3]},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_generic_mm": {
                "type": "add",
                "value": ["fake_model_a/1", "fake_model_a/2"],
                "modified_element": "fake_model_a/2",
            }
        }
        assert result == expected

    def test_generic_M2M_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_generic_mm": [2]},
                "fake_model_b/2": {"fake_model_a_generic_mm": ["fake_model_a/1"]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            instance={"id": 1, "fake_model_b_generic_mm": []},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_generic_mm": {
                "type": "remove",
                "value": [],
                "modified_element": "fake_model_a/1",
            }
        }
        assert result == expected

    def test_generic_multitype_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_generic_multitype": "fake_model_b/3"},
                "fake_model_a/2": {"fake_model_generic_multitype": "fake_model_b/3"},
                "fake_model_b/3": {"fake_model_a_generic_multitype_m": [1, 2]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_generic_multitype,
            field_name="fake_model_generic_multitype",
            instance={"id": 1, "fake_model_generic_multitype": None},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_generic_multitype_m": {
                "type": "remove",
                "value": [2],
                "modified_element": 1,
            },
        }
        assert result == expected
