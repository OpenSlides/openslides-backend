from openslides_backend.action.relations import RelationsHandler
from tests.util import get_fqfield, get_fqid

from .setup import BaseRelationsTestCase, FakeModelA


class GenericRelationsTest(BaseRelationsTestCase):
    def test_generic_O2O_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            obj={"fake_model_b_generic_oo": 2},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_oo"): {
                "type": "add",
                "value": get_fqid("fake_model_a/1"),
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def xtest_generic_O2O_replace(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_a/2", {"fake_model_b_generic_oo": 3})
        self.create_model(
            "fake_model_b/3", {"fake_model_a_generic_oo": get_fqid("fake_model_a/2")}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            obj={"fake_model_b_generic_oo": 3},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_generic_oo"): {
                "type": "add",
                "value": get_fqid("fake_model_a/1"),
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def test_generic_O2O_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_generic_oo": 2})
        self.create_model(
            "fake_model_b/2", {"fake_model_a_generic_oo": get_fqid("fake_model_a/1")}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_oo,
            field_name="fake_model_b_generic_oo",
            obj={"fake_model_b_generic_oo": None},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_oo"): {
                "type": "remove",
                "value": None,
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def test_generic_O2M_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            obj={"fake_model_b_generic_om": 2},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_mo"): {
                "type": "add",
                "value": [get_fqid("fake_model_a/1")],
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def test_generic_O2M_add(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_generic_om": 3})
        self.create_model("fake_model_a/2", {})
        self.create_model(
            "fake_model_b/3", {"fake_model_a_generic_mo": [get_fqid("fake_model_a/1")]}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=2,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            obj={"fake_model_b_generic_om": 3},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_generic_mo"): {
                "type": "add",
                "value": [get_fqid("fake_model_a/1"), get_fqid("fake_model_a/2")],
                "modified_element": get_fqid("fake_model_a/2"),
            }
        }
        assert result == expected

    def test_generic_O2M_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_generic_om": 2})
        self.create_model(
            "fake_model_b/2", {"fake_model_a_generic_mo": [get_fqid("fake_model_a/1")]}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_om,
            field_name="fake_model_b_generic_om",
            obj={"fake_model_b_generic_om": None},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_mo"): {
                "type": "remove",
                "value": [],
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def test_generic_M2M_empty(self) -> None:
        self.create_model("fake_model_a/1", {})
        self.create_model("fake_model_b/2", {})
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            obj={"fake_model_b_generic_mm": [2]},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_mm"): {
                "type": "add",
                "value": [get_fqid("fake_model_a/1")],
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected

    def test_generic_M2M_add(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_generic_mm": [3]})
        self.create_model("fake_model_a/2", {})
        self.create_model(
            "fake_model_b/3", {"fake_model_a_generic_mm": [get_fqid("fake_model_a/1")]}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=2,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            obj={"fake_model_b_generic_mm": [3]},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/3/fake_model_a_generic_mm"): {
                "type": "add",
                "value": [get_fqid("fake_model_a/1"), get_fqid("fake_model_a/2")],
                "modified_element": get_fqid("fake_model_a/2"),
            }
        }
        assert result == expected

    def test_generic_M2M_delete(self) -> None:
        self.create_model("fake_model_a/1", {"fake_model_b_generic_mm": [2]})
        self.create_model(
            "fake_model_b/2", {"fake_model_a_generic_mm": [get_fqid("fake_model_a/1")]}
        )
        handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelA(),
            id=1,
            field=FakeModelA.fake_model_b_generic_mm,
            field_name="fake_model_b_generic_mm",
            obj={"fake_model_b_generic_mm": []},
        )
        result = handler.perform()
        expected = {
            get_fqfield("fake_model_b/2/fake_model_a_generic_mm"): {
                "type": "remove",
                "value": [],
                "modified_element": get_fqid("fake_model_a/1"),
            }
        }
        assert result == expected
