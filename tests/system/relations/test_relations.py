from .setup import BaseRelationsTestCase, FakeModelA, SingleRelationHandlerWithContext


class RelationHandlerTest(BaseRelationsTestCase):
    def test_O2O_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            instance={"id": 1, "fake_model_b_oo": 2},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_oo": {
                "type": "add",
                "value": 1,
                "modified_element": 1,
            }
        }
        assert result == expected

    def test_O2O_replace(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {},
                "fake_model_a/2": {"fake_model_b_oo": 3},
                "fake_model_b/3": {"fake_model_a_oo": 2},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            instance={"id": 1, "fake_model_b_oo": 3},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_oo": {
                "type": "add",
                "value": 1,
                "modified_element": 1,
            },
            "fake_model_a/2/fake_model_b_oo": {
                "type": "remove",
                "value": None,
                "modified_element": 3,
            },
        }
        assert result == expected

    def test_O2O_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_oo": 2},
                "fake_model_b/2": {"fake_model_a_oo": 1},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            instance={"id": 1, "fake_model_b_oo": None},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_oo": {
                "type": "remove",
                "value": None,
                "modified_element": 1,
            }
        }
        assert result == expected

    def test_O2M_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            instance={"id": 1, "fake_model_b_om": 2},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_mo": {
                "type": "add",
                "value": [1],
                "modified_element": 1,
            }
        }
        assert result == expected

    def test_O2M_add(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_om": 3},
                "fake_model_a/2": {},
                "fake_model_b/3": {"fake_model_a_mo": [1]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            instance={"id": 2, "fake_model_b_om": 3},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_mo": {
                "type": "add",
                "value": [1, 2],
                "modified_element": 2,
            }
        }
        assert result == expected

    def test_O2M_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_om": 2},
                "fake_model_b/2": {"fake_model_a_mo": [1]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            instance={"id": 1, "fake_model_b_om": None},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_mo": {
                "type": "remove",
                "value": [],
                "modified_element": 1,
            }
        }
        assert result == expected

    def test_M2M_empty(self) -> None:
        self.set_models({"fake_model_a/1": {}, "fake_model_b/2": {}})
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            instance={"id": 1, "fake_model_b_mm": [2]},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_mm": {
                "type": "add",
                "value": [1],
                "modified_element": 1,
            }
        }
        assert result == expected

    def test_M2M_add(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_mm": [3]},
                "fake_model_a/2": {},
                "fake_model_b/3": {"fake_model_a_mm": [1]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            instance={"id": 2, "fake_model_b_mm": [3]},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/3/fake_model_a_mm": {
                "type": "add",
                "value": [1, 2],
                "modified_element": 2,
            }
        }
        assert result == expected

    def test_M2M_delete(self) -> None:
        self.set_models(
            {
                "fake_model_a/1": {"fake_model_b_mm": [2]},
                "fake_model_b/2": {"fake_model_a_mm": [1]},
            }
        )
        handler = SingleRelationHandlerWithContext(
            datastore=self.datastore,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            instance={"id": 1, "fake_model_b_mm": []},
        )
        result = handler.perform()
        expected = {
            "fake_model_b/2/fake_model_a_mm": {
                "type": "remove",
                "value": [],
                "modified_element": 1,
            }
        }
        assert result == expected
