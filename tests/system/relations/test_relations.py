from openslides_backend.action.relations import RelationsHandler
from tests.util import get_fqfield

from .setup import BaseRelationsTestCase, FakeModelA


class RelationHandlerTest(BaseRelationsTestCase):
    def test_O2O_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            obj={"fake_model_b_oo": 2},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_oo"): {"type": "add", "value": 1}
        }
        assert result == expected

    def xtest_O2O_replace(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_a/2", {"fake_model_b_oo": 3})
        self.create_model("fake_model_b/3", {"fake_model_a_oo": 2})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            obj={"fake_model_b_oo": 3},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_oo"): {"type": "add", "value": 1}
        }
        assert result == expected

    def test_O2O_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_oo": 2})
        self.create_model("fake_model_b/2", {"fake_model_a_oo": 1})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_oo,
            field_name="fake_model_b_oo",
            obj={"fake_model_b_oo": None},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_oo"): {
                "type": "remove",
                "value": None,
            }
        }
        assert result == expected

    def test_O2M_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            obj={"fake_model_b_om": 2},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_mo"): {"type": "add", "value": [1]}
        }
        assert result == expected

    def test_O2M_add(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_om": 3})
        self.create_model("fake_model_a/2", {})
        self.create_model("fake_model_b/3", {"fake_model_a_mo": [1]})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=2,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            obj={"fake_model_b_om": 3},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_mo"): {
                "type": "add",
                "value": [1, 2],
            }
        }
        assert result == expected

    def test_O2M_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_om": 2})
        self.create_model("fake_model_b/2", {"fake_model_a_mo": [1]})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_om,
            field_name="fake_model_b_om",
            obj={"fake_model_b_om": None},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_mo"): {
                "type": "remove",
                "value": [],
            }
        }
        assert result == expected

    def test_M2M_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            obj={"fake_model_b_mm": [2]},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_mm"): {"type": "add", "value": [1]}
        }
        assert result == expected

    def test_M2M_add(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_mm": [3]})
        self.create_model("fake_model_a/2", {})
        self.create_model("fake_model_b/3", {"fake_model_a_mm": [1]})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=2,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            obj={"fake_model_b_mm": [3]},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_mm"): {
                "type": "add",
                "value": [1, 2],
            }
        }
        assert result == expected

    def test_M2M_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_mm": [2]})
        self.create_model("fake_model_b/2", {"fake_model_a_mm": [1]})
        handler = RelationsHandler(
            database=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_mm,
            field_name="fake_model_b_mm",
            obj={"fake_model_b_mm": []},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_mm"): {
                "type": "remove",
                "value": [],
            }
        }
        assert result == expected
