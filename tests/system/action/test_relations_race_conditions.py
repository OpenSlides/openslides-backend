from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.generics.delete import DeleteAction
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection

from .race_condition_mixin_test import RaceConditionMixinTest


class FakeModelRRCA(Model):
    collection = Collection("fake_model_rrc_a")
    verbose_name = "fake model for relation race condition field check a"
    id = fields.IntegerField()

    r1_a_id = fields.RelationField(to={Collection("fake_model_rrc_a"): "r1_a_id"})

    r1n_a_id = fields.RelationField(to={Collection("fake_model_rrc_a"): "rn_a_ids"})
    rn_a_ids = fields.RelationListField(to={Collection("fake_model_rrc_a"): "r1n_a_id"})

    rnm_a_ids = fields.RelationListField(to={Collection("fake_model_rrc_a"): "rnn_a_ids"})
    rnn_a_ids = fields.RelationListField(to={Collection("fake_model_rrc_a"): "rnm_a_ids"})

    r1_b_id = fields.RelationField(to={Collection("fake_model_rrc_b"): "r1_a_id"})
    rn_b_ids = fields.RelationListField(to={Collection("fake_model_rrc_b"): "r1n_a_id"})
    rnn_b_ids = fields.RelationListField(to={Collection("fake_model_rrc_b"): "rnn_a_ids"})


class FakeModelRRCB(Model):
    collection = Collection("fake_model_rrc_b")
    verbose_name = "fake model for  relation race condition field check b"
    id = fields.IntegerField()

    r1_a_id = fields.RelationField(to={Collection("fake_model_rrc_a"): "r1_b_id"})
    r1n_a_id = fields.RelationField(to={Collection("fake_model_rrc_a"): "rn_b_ids"})
    rnn_a_ids = fields.RelationListField(to={Collection("fake_model_rrc_a"): "rnn_b_ids"})


@register_action("fake_model_rrc_a.create")
class FakeModelRRCACreateAction(CreateAction):
    model = FakeModelRRCA()
    schema = {}  # type: ignore


@register_action("fake_model_rrc_a.update")
class FakeModelRRCAUpdateAction(UpdateAction):
    model = FakeModelRRCA()
    schema = {}  # type: ignore

@register_action("fake_model_rrc_a.delete")
class FakeModelRRCADeleteAction(DeleteAction):
    model = FakeModelRRCA()
    schema = {}  # type: ignore

@register_action("fake_model_rrc_b.update")
class FakeModelRRCBUpdateAction(UpdateAction):
    model = FakeModelRRCB()
    schema = {}  # type: ignore

@register_action("fake_model_rrc_b.delete")
class FakeModelRRCBDeleteAction(DeleteAction):
    model = FakeModelRRCB()
    schema = {}  # type: ignore


class TestRelationComplexAndRaceCondition(RaceConditionMixinTest):
    def test_create_rel_1_to_1_AA_delete(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        a2_create_data = [{
            "action": "fake_model_rrc_a.create",
            "data": [
                {"r1_a_id": 1}
            ],
        }]
        a1_delete_data = [{
            "action": "fake_model_rrc_a.delete",
            "data": [
                {"id": 1},
            ],
        }]

        thread1, thread2 = self.run_threads(a2_create_data, a1_delete_data)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "fake_model_rrc_a/1\\\' does not exist")
        self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_rel_1_to_n_AA_delete(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        a3_create_data = [{
            "action": "fake_model_rrc_a.create",
            "data": [{"rn_a_ids": [1, 2]}]
        }]
        a1_delete_data = [{
            "action": "fake_model_rrc_a.delete",
            "data": [
                {"id": 1},
            ],
        }]

        thread1, thread2 = self.run_threads(a3_create_data, a1_delete_data)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "fake_model_rrc_a/1\\\' does not exist")
        self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_rel_n_to_m_AA_okay(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        action_create_data = [
            {
                "action": "fake_model_rrc_a.create",
                "data": [
                    {"rnn_a_ids": [1, 2]}
                ],
            },
            {
                "action": "fake_model_rrc_a.update",
                "data": [
                    {"id": 1, "rnn_a_ids": [2, 3]}
                ],
            },

        ]
        response = self.client.post("/", json=action_create_data)

        self.assert_status_code(response, 200)
        model = self.get_model("fake_model_rrc_a/1")
        self.assertCountEqual(model["rnn_a_ids"], [2, 3])
        self.assertCountEqual(model["rnm_a_ids"], [3])
        model = self.get_model("fake_model_rrc_a/2")
        self.assertIsNone(model.get("rnn_a_ids"))
        self.assertCountEqual(model["rnm_a_ids"], [1, 3])
        model = self.get_model("fake_model_rrc_a/3")
        self.assertCountEqual(model["rnn_a_ids"], [1, 2])
        self.assertCountEqual(model["rnm_a_ids"], [1])

    def test_create_rel_n_to_m_AA_delete(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        action_create_data = [
            {
                "action": "fake_model_rrc_a.create",
                "data": [
                    {"rnn_a_ids": [1, 2]}
                ],
            },
            {
                "action": "fake_model_rrc_a.update",
                "data": [
                    {"id": 1, "rnn_a_ids": [2, 3]}
                ],
            },

        ]
        a1_delete_data = [{
            "action": "fake_model_rrc_a.delete",
            "data": [
                {"id": 1},
            ],
        }]

        thread1, thread2 = self.run_threads(action_create_data, a1_delete_data)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "fake_model_rrc_a/1\\\' does not exist")
        self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_rel_1_to_1_AB_delete(self) -> None:
        self.create_model("fake_model_rrc_b/1", {})
        a1_create_data = [{
            "action": "fake_model_rrc_a.create",
            "data": [
                {"r1_b_id": 1}
            ],
        }]
        b1_delete_data = [{
            "action": "fake_model_rrc_b.delete",
            "data": [
                {"id": 1},
            ],
        }]

        thread1, thread2 = self.run_threads(a1_create_data, b1_delete_data)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "fake_model_rrc_b/1\\\' does not exist")
        self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_rel_1_to_n_AB_delete(self) -> None:
        self.create_model("fake_model_rrc_b/1", {})
        self.create_model("fake_model_rrc_b/2", {})
        a1_create_data = [{
            "action": "fake_model_rrc_a.create",
            "data": [
                {"rn_b_ids": [1, 2]}
            ],
        }]
        b1_delete_data = [{
            "action": "fake_model_rrc_b.delete",
            "data": [
                {"id": 1},
            ],
        }]

        thread1, thread2 = self.run_threads(a1_create_data, b1_delete_data)
        self.assert_no_thread_exception(thread2)
        self.assert_thread_exception(thread1, "fake_model_rrc_b/1\\\' does not exist")
        self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_rel_1_to_n_AB_error(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_b/1", {})
        self.create_model("fake_model_rrc_b/2", {})
        a1_update = [
            {
                "action": "fake_model_rrc_a.update",
                "data": [{"id": 1, "rn_b_ids": [1, 2]}],
            },
            {
                "action": "fake_model_rrc_a.update",
                "data": [{"id": 1, "rn_b_ids": [2]}],
            },
        ]

        response = self.client.post("/", json=a1_update)
        self.assert_status_code(response, 200)

        model1 = self.get_model("fake_model_rrc_a/1")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")
        self.assertCountEqual(model1.get("rn_b_ids", []), [2])
        self.assertEqual(model_b1.get("r1n_a_id"), None, "Should be None, but is still 1, because not removed by 2nd action")
        self.assertEqual(model_b2.get("r1n_a_id"), 1)

    def test_create_rel_n_to_m_AB_okay1(self) -> None:
        """
        okay/fail 1 to 4 series to compare:
        okay1: Only first action => okay
        okay2: Only second action => okay
        fail3: Both actions in one post => fails
        okay4: Both actions, but each in it own post => okay
        """
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        self.create_model("fake_model_rrc_a/3", {"rnn_b_ids": [1]})
        self.create_model("fake_model_rrc_b/1", {"rnn_a_ids": [3]})
        self.create_model("fake_model_rrc_b/2", {})

        action_create_data = [
            {
                "action": "fake_model_rrc_a.update",
                "data": [
                    {"id": 1, "rnn_b_ids": [1, 2]}
                ],
            },
        ]

        response = self.client.post("/", json=action_create_data)
        self.assert_status_code(response, 200)
        model1 = self.get_model("fake_model_rrc_a/1")
        model2 = self.get_model("fake_model_rrc_a/2")
        model3 = self.get_model("fake_model_rrc_a/3")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")
        self.assertCountEqual(model1["rnn_b_ids"], [1, 2])
        self.assertCountEqual(model2.get("rnn_b_ids", []), [])
        self.assertCountEqual(model3["rnn_b_ids"], [1])
        self.assertCountEqual(model_b1["rnn_a_ids"], [3, 1])
        self.assertCountEqual(model_b2["rnn_a_ids"], [1])

    def test_create_rel_n_to_m_AB_okay2(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        self.create_model("fake_model_rrc_a/3", {"rnn_b_ids": [1]})
        self.create_model("fake_model_rrc_b/1", {"rnn_a_ids": [3]})
        self.create_model("fake_model_rrc_b/2", {})

        action_create_data = [
            {
                "action": "fake_model_rrc_b.update",
                "data": [
                    {"id": 1, "rnn_a_ids": [1, 2]}
                ],
            },

        ]

        response = self.client.post("/", json=action_create_data)
        self.assert_status_code(response, 200)
        model1 = self.get_model("fake_model_rrc_a/1")
        model2 = self.get_model("fake_model_rrc_a/2")
        model3 = self.get_model("fake_model_rrc_a/3")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")
        self.assertCountEqual(model1["rnn_b_ids"], [1])
        self.assertCountEqual(model2["rnn_b_ids"], [1])
        self.assertCountEqual(model3.get("rnn_b_ids", []), [])
        self.assertCountEqual(model_b1["rnn_a_ids"], [1, 2])
        self.assertCountEqual(model_b2.get("rnn_a_ids", []), [])

    def test_create_rel_n_to_m_AB_fail3(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        self.create_model("fake_model_rrc_a/3", {"rnn_b_ids": [1]})
        self.create_model("fake_model_rrc_b/1", {"rnn_a_ids": [3]})
        self.create_model("fake_model_rrc_b/2", {})

        action_create_data = [
            {
                "action": "fake_model_rrc_a.update",
                "data": [
                    {"id": 1, "rnn_b_ids": [1, 2]}
                ],
            },
            {
                "action": "fake_model_rrc_b.update",
                "data": [
                    {"id": 1, "rnn_a_ids": [1, 2]}
                ],
            },

        ]

        response = self.client.post("/", json=action_create_data)
        self.assert_status_code(response, 200)
        model1 = self.get_model("fake_model_rrc_a/1")
        model2 = self.get_model("fake_model_rrc_a/2")
        model3 = self.get_model("fake_model_rrc_a/3")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")
        self.assertCountEqual(model1.get("rnn_b_ids", []), [1, 2], "Fails , because 2 is removed by 2nd Action")
        self.assertCountEqual(model2.get("rnn_b_ids", []), [1])
        self.assertCountEqual(model3.get("rnn_b_ids", []), [])
        self.assertCountEqual(model_b1.get("rnn_a_ids", []), [1, 2])
        self.assertCountEqual(model_b2.get("rnn_a_ids", []), [1])

    def test_create_rel_n_to_m_AB_okay4(self) -> None:
        self.create_model("fake_model_rrc_a/1", {})
        self.create_model("fake_model_rrc_a/2", {})
        self.create_model("fake_model_rrc_a/3", {"rnn_b_ids": [1]})
        self.create_model("fake_model_rrc_b/1", {"rnn_a_ids": [3]})
        self.create_model("fake_model_rrc_b/2", {})

        action_create_data = [
            {
                "action": "fake_model_rrc_a.update",
                "data": [
                    {"id": 1, "rnn_b_ids": [1, 2]}
                ],
            },
        ]

        response = self.client.post("/", json=action_create_data)
        self.assert_status_code(response, 200)
        model1 = self.get_model("fake_model_rrc_a/1")
        model2 = self.get_model("fake_model_rrc_a/2")
        model3 = self.get_model("fake_model_rrc_a/3")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")

        action_create_data = [
            {
                "action": "fake_model_rrc_b.update",
                "data": [
                    {"id": 1, "rnn_a_ids": [1, 2]}
                ],
            },
        ]

        response = self.client.post("/", json=action_create_data)
        self.assert_status_code(response, 200)

        model1 = self.get_model("fake_model_rrc_a/1")
        model2 = self.get_model("fake_model_rrc_a/2")
        model3 = self.get_model("fake_model_rrc_a/3")
        model_b1 = self.get_model("fake_model_rrc_b/1")
        model_b2 = self.get_model("fake_model_rrc_b/2")
        self.assertCountEqual(model1.get("rnn_b_ids", []), [1, 2])
        self.assertCountEqual(model2.get("rnn_b_ids", []), [1])
        self.assertCountEqual(model3.get("rnn_b_ids", []), [])
        self.assertCountEqual(model_b1.get("rnn_a_ids", []), [1, 2])
        self.assertCountEqual(model_b2.get("rnn_a_ids", []), [1])

    # def test_create_rel_n_to_m_AB_delete(self) -> None:
    #     self.create_model("fake_model_rrc_a/1", {})
    #     self.create_model("fake_model_rrc_a/2", {})
    #     self.create_model("fake_model_rrc_a/3", {"rnn_b_ids": [1]})
    #     self.create_model("fake_model_rrc_b/1", {"rnn_a_ids": [3]})
    #     self.create_model("fake_model_rrc_b/2", {})

    #     action_create_data = [
    #         {
    #             "action": "fake_model_rrc_a.update",
    #             "data": [
    #                 {"id": 1, "rnn_b_ids": [1, 2]}
    #             ],
    #         },
    #         {
    #             "action": "fake_model_rrc_b.update",
    #             "data": [
    #                 {"id": 1, "rnn_a_ids": [1, 2]}
    #             ],
    #         },

    #     ]
    #     a1_delete_data = [{
    #         "action": "fake_model_rrc_a.delete",
    #         "data": [
    #             {"id": 1},
    #         ],
    #     }]

    #     thread1, thread2 = self.run_threads(action_create_data, a1_delete_data)
    #     self.assert_no_thread_exception(thread2)
    #     self.assert_thread_exception(thread1, "fake_model_rrc_a/1\\\' does not exist")
    #     self.assert_model_locked_thrown_in_thread(thread1)

    def test_create_A2_replace_b_id(self) -> None:
        self.create_model("fake_model_rrc_a/1", {"r1_b_id": 1})
        self.create_model("fake_model_rrc_b/1", {"r1_a_id": 1})
        a2_create_data = [{
            "action": "fake_model_rrc_a.create",
            "data": [
                {"r1_b_id": 1}
            ],
        }]
        response = self.client.post("/", json=a2_create_data)

        self.assert_status_code(response, 400)
        # TODO: Is this correct? Why not?
        self.assertIn("You can not set fake_model_rrc_b/1/r1_a_id to a new value because this field is not empty.", str(response.data))
