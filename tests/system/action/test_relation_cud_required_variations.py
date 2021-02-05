import pytest

from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from .base import BaseActionTestCase


class FakeModelA(Model):
    collection = Collection("test_model_a")
    verbose_name = "fake model for a"
    id = fields.IntegerField()

    fake_b_casc_to_all_id = fields.RelationField(
        to={Collection("test_model_b"): "fake_a_casc_to_all_ids"},
        on_delete=fields.OnDelete.CASCADE,
        required=True,
    )
    fake_b_prot_to_all_id = fields.RelationField(
        to={Collection("test_model_b"): "fake_a_prot_to_all_ids"},
        on_delete=fields.OnDelete.PROTECT,
    )
    fake_b_setnul_to_req_id = fields.RelationField(
        to={Collection("test_model_b"): "fake_a_setnul_to_req_ids"},
    )
    fake_b_setnul_to_not_req_id = fields.RelationField(
        to={Collection("test_model_b"): "fake_a_setnul_to_not_req_ids"},
    )


class FakeModelB(Model):
    collection = Collection("test_model_b")
    verbose_name = "fake model for b"
    id = fields.IntegerField()

    fake_a_casc_to_all_ids = fields.RelationListField(
        to={Collection("test_model_a"): "fake_b_casc_to_all_id"}, required=True
    )
    fake_a_prot_to_all_ids = fields.RelationListField(
        to={Collection("test_model_a"): "fake_b_prot_to_all_id"}, required=True
    )
    fake_a_setnul_to_req_ids = fields.RelationListField(
        to={Collection("test_model_a"): "fake_b_setnul_to_req_id"}, required=True
    )

    fake_a_setnul_to_not_req_ids = fields.RelationListField(
        to={Collection("test_model_a"): "fake_b_setnul_to_not_req_id"}
    )


class FakeModelC(Model):
    collection = Collection("test_model_c")
    verbose_name = "fake model for c"
    id = fields.IntegerField()

    req_field = fields.IntegerField(required=True)
    not_req_field = fields.IntegerField(required=True)


@register_action("test_model_a.create")
class FakeModelACreateAction(CreateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


@register_action("test_model_c.create")
class FakeModelCCreateAction(CreateAction):
    model = FakeModelC()
    schema = {}  # type: ignore


@register_action("test_model_a.delete")
class FakeModelADeleteAction(DeleteAction):
    model = FakeModelA()
    schema = {}  # type: ignore


@register_action("test_model_a.update")
class FakeModelAUpdateAction(UpdateAction):
    model = FakeModelA()
    schema = {}  # type: ignore


@register_action("test_model_b.delete")
class FakeModelBDeleteAction(DeleteAction):
    model = FakeModelB()
    schema = {}  # type: ignore


@register_action("test_model_b.update")
class FakeModelBUpdateAction(UpdateAction):
    model = FakeModelB()
    schema = {}  # type: ignore


@register_action("test_model_c.update")
class FakeModelCUpdateAction(UpdateAction):
    model = FakeModelC()
    schema = {}  # type: ignore


class TestDeleteVariations(BaseActionTestCase):
    #@pytest.mark.skip
    def test_del_a_casc_to_all(self) -> None:
        self.create_model("test_model_a/1", {"fake_b_casc_to_all_id": 1})
        self.create_model("test_model_b/1", {"fake_a_casc_to_all_ids": [1]})
        response = self.client.post(
            "/",
            json=[{"action": "test_model_a.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("test_model_a/1")
        self.assert_model_deleted("test_model_b/1")

    #@pytest.mark.skip
    def test_del_a_prot_to_all_filled(self) -> None:
        """
        test_model_a/1 can't be deleted, because it is PROTECTED and there
        is a value in "fake_b_prot_to_all_id", internally with ProtectedModelsException
        """
        self.create_model("test_model_a/1", {"fake_b_prot_to_all_id": 1})
        self.create_model("test_model_b/1", {"fake_a_prot_to_all_ids": [1]})
        response = self.client.post(
            "/",
            json=[{"action": "test_model_a.delete", "data": [{"id": 1}]}],
        )
        self.assertIn(
            "You can not delete test_model_a/1 because you have to delete the following related models first: [FullQualifiedId(\\'test_model_b/1\\')]",
            str(response.data),
        )
        self.assert_model_exists("test_model_a/1", {"fake_b_prot_to_all_id": 1})
        self.assert_model_exists("test_model_b/1")

    #@pytest.mark.skip
    def test_del_a_prot_to_all_not_filled(self) -> None:
        self.create_model("test_model_a/1", {"fake_b_prot_to_all_id": None})
        response = self.client.post(
            "/",
            json=[{"action": "test_model_a.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("test_model_a/1")

    def test_del_a_setnul_to_req(self) -> None:
        """
        a/1 will be deleted and b/1 will be set to null, because of SET_NULL.
        This should not be allowed, because b/1:fake_b_prot_to_setnul_id is required.
        """
        self.create_model("test_model_a/1", {"fake_b_setnul_to_req_id": 1})
        self.create_model("test_model_b/1", {"fake_a_setnul_to_req_ids": [1]})
        response = self.client.post(
            "/",
            json=[{"action": "test_model_a.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Backward relation test_model_b/1: You try to set following required fields to an empty value: [\\'fake_a_setnul_to_req_ids\\']",
            str(response.data),
        )
        self.assert_model_exists("test_model_a/1", {"fake_b_setnul_to_req_id": 1})
        self.assert_model_exists("test_model_b/1", {"fake_a_setnul_to_req_ids": [1]})

    def test_del_a_setnul_to_not_req(self) -> None:
        self.create_model("test_model_a/1", {"fake_b_setnul_to_not_req_id": 1})
        self.create_model("test_model_b/1", {"fake_a_setnul_to_not_req_ids": [1]})
        response = self.client.post(
            "/",
            json=[{"action": "test_model_a.delete", "data": [{"id": 1}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("test_model_a/1")
        self.assert_model_exists("test_model_b/1", {"fake_a_setnul_to_not_req_ids": []})


class TestUpdateVariations(BaseActionTestCase):
    def test_upd_a_all_to_req(self) -> None:
        """
        This should raise an error,
        because the value is required in b1/fake_a_setnul_to_req_ids
        """
        self.create_model("test_model_a/1", {"fake_b_setnul_to_req_id": 1})
        self.create_model("test_model_b/1", {"fake_a_setnul_to_req_ids": [1]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_a.update",
                    "data": [{"id": 1, "fake_b_setnul_to_req_id": None}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Backward relation test_model_b/1: You try to set following required fields to an empty value: [\\'fake_a_setnul_to_req_ids\\']",
            str(response.data),
        )
        self.assert_model_exists("test_model_a/1", {"fake_b_setnul_to_req_id": 1})
        self.assert_model_exists("test_model_b/1", {"fake_a_setnul_to_req_ids": [1]})

    #@pytest.mark.skip
    def test_upd_a_all_to_not_req(self) -> None:
        self.create_model("test_model_a/1", {"fake_b_setnul_to_not_req_id": 1})
        self.create_model("test_model_b/1", {"fake_a_setnul_to_not_req_ids": [1]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_a.update",
                    "data": [{"id": 1, "fake_b_setnul_to_not_req_id": None}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "test_model_a/1", {"fake_b_setnul_to_not_req_id": None}
        )
        self.assert_model_exists("test_model_b/1", {"fake_a_setnul_to_not_req_ids": []})

    #@pytest.mark.skip
    def test_upd_a_all_to_req_multi(self) -> None:
        self.create_model("test_model_a/1", {"fake_b_setnul_to_req_id": 1})
        self.create_model("test_model_a/2", {"fake_b_setnul_to_req_id": 1})
        self.create_model("test_model_b/1", {"fake_a_setnul_to_req_ids": [1, 2]})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_a.update",
                    "data": [{"id": 1, "fake_b_setnul_to_req_id": None}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("test_model_a/1", {"fake_b_setnul_to_req_id": None})
        self.assert_model_exists("test_model_a/2", {"fake_b_setnul_to_req_id": 1})
        self.assert_model_exists("test_model_b/1", {"fake_a_setnul_to_req_ids": [2]})

    #@pytest.mark.skip
    def test_upd_c_set_req_field_empty(self) -> None:
        """
        Should fail, because req_field may not be set empty
        """
        self.create_model("test_model_c/1", {"req_field": 1})
        response = self.client.post(
            "/",
            json=[
                {"action": "test_model_c.update", "data": [{"id": 1, "req_field": 0}]}
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Update of test_model_c/1: You try to set following required fields to an empty value: [\\'req_field\\']",
            str(response.data),
        )
        self.assert_model_exists("test_model_c/1", {"req_field": 1})


class TestCreateVariations(BaseActionTestCase):
    #@pytest.mark.skip
    def test_create_a_impossible_v1(self) -> None:
        """
        Should be impossible, because fake_b_casc_to_all_id can't be set, because there is no test_model_b instance stored.
        """
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_a.create",
                    "data": [{"fake_b_casc_to_all_id": None}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Creation of test_model_a/1: You try to set following required fields to an empty value: [\\'fake_b_casc_to_all_id\\']",
            str(response.data),
        )
        self.assert_model_not_exists("test_model_a/1")

    #@pytest.mark.skip
    def test_create_a_impossible_v2(self) -> None:
        """
        Should be impossible, because fake_b_casc_to_all_id can't be set, because there is no test_model_b instance stored.
        """
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_a.create",
                    "data": [{"fake_b_casc_to_all_id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model \\'test_model_b/1\\' does not exist.",
            str(response.data),
        )
        self.assert_model_not_exists("test_model_a/1")

    #@pytest.mark.skip
    def test_create_c(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "test_model_c.create",
                    "data": [{"req_field": 1, "not_req_field": 2}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("test_model_c/1", {"req_field": 1, "not_req_field": 2})

    #@pytest.mark.skip
    def test_create_c_without_req_field(self) -> None:
        """
        Should fail, because req_field is not set
        """
        response = self.client.post(
            "/",
            json=[{"action": "test_model_c.create", "data": [{"not_req_field": 2}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn("required", str(response.data))
        self.assert_model_not_exists("test_model_c/1")
