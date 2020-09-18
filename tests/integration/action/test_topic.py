import simplejson as json

from openslides_backend.action import ActionPayload
from openslides_backend.action.topic.create import TopicCreate
from openslides_backend.action.topic.delete import TopicDelete
from openslides_backend.action.topic.update import TopicUpdate
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from tests.system.action.base import BaseActionTestCase
from tests.util import Client, get_fqfield, get_fqid

from ..fake_services.database import DatabaseTestAdapter
from ..fake_services.permission import PermissionTestAdapter
from ..util import create_test_application_old as create_test_application

# TODO: These tests use all old style datastore testing.
# Fix this (do not use create_test_applicaton_old and do not use old_style_testing=True any more).


class BaseTopicCreateActionTester(BaseActionTestCase):
    """
    Tests the topic create action.
    """

    def setUp(self) -> None:
        super().setUp()
        self.valid_payload_1 = [
            {
                "meeting_id": 2393342057,
                "title": "title_ooPhi9ZohC",
                "text": "text_eeKoosahh4",
            }
        ]
        self.attachments = [3549387598, 7583920032]
        self.valid_payload_2 = [
            {
                "meeting_id": 4002059810,
                "title": "title_pha2Eirohg",
                "text": "text_CaekiiLai2",
                "attachment_ids": self.attachments,
            }
        ]
        self.valid_payload_3 = [{"meeting_id": 3611987967, "title": "title_eivaey2Aeg"}]


class TopicCreateActionUnitTester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 5968705978
        self.action = TopicCreate(
            "topic.create",
            PermissionTestAdapter(superuser=user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Kiofee1ieV"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_validation_correct_3(self) -> None:
        self.action.validate(self.valid_payload_3)

    def test_validation_invalid_1(self) -> None:
        invalid_payload = [
            {
                "meeting_id": 3611987967,
                "title": "title_yae0Ohph4e",
                "unknown_property_aiseCah6ah": "unknown_property_iagh4paoWi",
            }
        ]
        with self.assertRaises(ActionException):
            self.action.validate(invalid_payload)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        result = dataset["data"]
        expected = [
            {
                "instance": self.valid_payload_1[0],
                "new_id": 42,
                "relations": {
                    get_fqfield("meeting/2393342057/topic_ids"): {
                        "type": "add",
                        "value": [42],
                    },
                },
            }
        ]
        self.assertEqual(result, expected)

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_2[0],
                    "new_id": 42,
                    "relations": {
                        get_fqfield("meeting/4002059810/topic_ids"): {
                            "type": "add",
                            "value": [42],
                        },
                        get_fqfield(
                            f"mediafile/{self.attachments[0]}/attachment_ids"
                        ): {
                            "type": "add",
                            "value": [
                                get_fqid("topic/6259289755"),
                                get_fqid("topic/42"),
                            ],
                        },
                        get_fqfield(
                            f"mediafile/{self.attachments[1]}/attachment_ids"
                        ): {"type": "add", "value": [get_fqid("topic/42")]},
                    },
                }
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_3)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_3[0],
                    "new_id": 42,
                    "relations": {
                        get_fqfield("meeting/3611987967/topic_ids"): {
                            "type": "add",
                            "value": [6375863023, 6259289755, 42],
                        },
                    },
                }
            ],
        )


class TopicCreateActionPerformTester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 5968705978
        self.action = TopicCreate(
            "topic.create",
            PermissionTestAdapter(superuser=self.user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )

    def test_perform_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Ieh5aiwora"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        result = list(write_request_elements)
        self.assertTrue(len(result) == 2)

    def test_perform_correct_2(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        result = list(write_request_elements)
        self.assertTrue(len(result) == 2)

    def test_perform_correct_3(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_3, user_id=self.user_id
        )
        result = list(write_request_elements)
        self.assertTrue(len(result) == 2)

    def test_perform_no_permission_1(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_1, user_id=4796568680)

    def test_perform_no_permission_2(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_2, user_id=4796568680)

    def test_perform_no_permission_3(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_3, user_id=4796568680)


class TopicCreateActionWSGITester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.datastore_content = {
            get_fqfield("meeting/2393342057/topic_ids"): [],
            get_fqfield("meeting/4002059810/user_ids"): [5968705978],
            get_fqfield("mediafile/3549387598/meeting_ids"): [4002059810],
            get_fqfield("mediafile/3549387598/attachment_ids"): ["topic/6259289755"],
            get_fqfield("mediafile/7583920032/meeting_ids"): [4002059810],
            get_fqfield("meeting/3611987967/topic_ids"): [6375863023, 6259289755],
        }
        self.user_id = 5968705978
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )
        self.client = Client(self.application)

    def test_wsgi_request_empty(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": [{}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [{"wrong_field": "text_TaenePha0e"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "topic/42",
                        "fields": {
                            "meeting_id": 2393342057,
                            "title": "title_ooPhi9ZohC",
                            "text": "text_eeKoosahh4",
                            "agenda_item_id": 42,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/2393342057",
                        "fields": {"topic_ids": [42]},
                    },
                    {
                        "type": "create",
                        "fqid": "agenda_item/42",
                        "fields": {
                            "meeting_id": 2393342057,
                            "content_object_id": "topic/42",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/2393342057",
                        "fields": {"agenda_item_ids": [42]},
                    },
                ],
                "information": {
                    "topic/42": ["Object created"],
                    "meeting/2393342057": [
                        "Object attached to topic",
                        "Object attached to agenda item",
                    ],
                    "agenda_item/42": ["Object created"],
                },
                "user_id": self.user_id,
                "locked_fields": {"meeting/2393342057": 1},
            }
        )
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)
        self.assertIn("Action handled successfully", str(response.data))

    def test_wsgi_request_correct_2(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "topic/42",
                        "fields": {
                            "meeting_id": 4002059810,
                            "title": "title_pha2Eirohg",
                            "text": "text_CaekiiLai2",
                            "attachment_ids": self.attachments,
                            "agenda_item_id": 42,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": f"mediafile/{self.attachments[0]}",
                        "fields": {"attachment_ids": ["topic/6259289755", "topic/42"]},
                    },
                    {
                        "type": "update",
                        "fqid": f"mediafile/{self.attachments[1]}",
                        "fields": {"attachment_ids": ["topic/42"]},
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/4002059810",
                        "fields": {"topic_ids": [42]},
                    },
                    {
                        "type": "create",
                        "fqid": "agenda_item/42",
                        "fields": {
                            "meeting_id": 4002059810,
                            "content_object_id": "topic/42",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/4002059810",
                        "fields": {"agenda_item_ids": [42]},
                    },
                ],
                "information": {
                    "topic/42": ["Object created"],
                    f"mediafile/{self.attachments[0]}": ["Object attached to topic"],
                    f"mediafile/{self.attachments[1]}": ["Object attached to topic"],
                    "meeting/4002059810": [
                        "Object attached to topic",
                        "Object attached to agenda item",
                    ],
                    "agenda_item/42": ["Object created"],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    f"mediafile/{self.attachments[0]}": 1,
                    f"mediafile/{self.attachments[1]}": 1,
                    "meeting/4002059810": 1,
                },
            }
        )
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_3(self) -> None:
        expected_write_data = json.dumps(  # noqa: F841
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": "topic/42",
                        "fields": {
                            "meeting_id": 3611987967,
                            "title": "title_eivaey2Aeg",
                            "agenda_item_id": 42,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/3611987967",
                        "fields": {"topic_ids": [6375863023, 6259289755, 42]},
                    },
                    {
                        "type": "create",
                        "fqid": "agenda_item/42",
                        "fields": {
                            "meeting_id": 3611987967,
                            "content_object_id": "topic/42",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": "meeting/3611987967",
                        "fields": {"agenda_item_ids": [42]},
                    },
                ],
                "information": {
                    "topic/42": ["Object created"],
                    "meeting/3611987967": [
                        "Object attached to topic",
                        "Object attached to agenda item",
                    ],
                    "agenda_item/42": ["Object created"],
                },
                "user_id": self.user_id,
                "locked_fields": {"meeting/3611987967": 1},
            }
        )
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assert_status_code(response, 200)


class TopicCreateActionWSGITesterNoPermission(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionView", superuser=0
        )
        self.client = Client(self.application)

    def test_wsgi_request_no_permission_1(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_3(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assert_status_code(response, 403)


class BaseTopicUpdateActionTester(BaseActionTestCase):
    """
    Tests the topic update action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {"id": 1312354708, "title": "title_ahbuQu9ooz", "text": "text_thuF7Ahxee"}
        ]
        self.attachments = [3549387598, 7583920032]
        self.valid_payload_2 = [
            {
                "id": 1312354708,
                "title": "title_pai9oN2aec",
                "text": "text_oon2lai3Ie",
                "attachment_ids": self.attachments,
            }
        ]
        self.valid_payload_3 = [
            {"id": 6259289755, "title": "title_Ashae0quei", "attachment_ids": []}
        ]
        self.valid_payload_4 = [{"id": 6259289755, "attachment_ids": self.attachments}]
        self.valid_payload_5 = [
            {"id": 6259289755, "attachment_ids": [self.attachments[1]]}
        ]


class TopicUpdateActionUnitTester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 5968705978

        self.action = TopicUpdate(
            "topic.update",
            PermissionTestAdapter(superuser=user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_guaPee0goh"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_validation_correct_3(self) -> None:
        self.action.validate(self.valid_payload_3)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(
            dataset["data"], [{"instance": self.valid_payload_1[0], "relations": {}}],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_2[0],
                    "relations": {
                        get_fqfield(
                            f"mediafile/{self.attachments[0]}/attachment_ids"
                        ): {
                            "type": "add",
                            "value": [
                                get_fqid("topic/6259289755"),
                                get_fqid("topic/1312354708"),
                            ],
                        },
                        get_fqfield(
                            f"mediafile/{self.attachments[1]}/attachment_ids"
                        ): {"type": "add", "value": [get_fqid("topic/1312354708")]},
                    },
                }
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_3)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_3[0],
                    "relations": {
                        get_fqfield(
                            f"mediafile/{self.attachments[0]}/attachment_ids"
                        ): {"type": "remove", "value": []},
                    },
                }
            ],
        )

    def test_prepare_dataset_4(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_4)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_4[0],
                    "relations": {
                        get_fqfield(
                            f"mediafile/{self.attachments[1]}/attachment_ids"
                        ): {"type": "add", "value": [get_fqid("topic/6259289755")]},
                    },
                }
            ],
        )

    def test_prepare_dataset_5(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_5)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_5[0],
                    "relations": {
                        get_fqfield(
                            f"mediafile/{self.attachments[0]}/attachment_ids"
                        ): {"type": "remove", "value": []},
                        get_fqfield(
                            f"mediafile/{self.attachments[1]}/attachment_ids"
                        ): {"type": "add", "value": [get_fqid("topic/6259289755")]},
                    },
                }
            ],
        )


class TopicUpdateActionPerformTester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 5968705978
        self.action = TopicUpdate(
            "topic.update",
            PermissionTestAdapter(superuser=self.user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )

    def test_perform_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_gaiThupu6a"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/1312354708"),
                        "fields": {
                            "title": "title_ahbuQu9ooz",
                            "text": "text_thuF7Ahxee",
                        },
                    },
                ],
                "information": {get_fqid("topic/1312354708"): ["Object updated"]},
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_correct_2(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/1312354708"),
                        "fields": {
                            "title": "title_pai9oN2aec",
                            "text": "text_oon2lai3Ie",
                            "attachment_ids": self.attachments,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile/{self.attachments[0]}"),
                        "fields": {
                            "attachment_ids": [
                                get_fqid("topic/6259289755"),
                                get_fqid("topic/1312354708"),
                            ]
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile/{self.attachments[1]}"),
                        "fields": {"attachment_ids": [get_fqid("topic/1312354708")]},
                    },
                ],
                "information": {
                    get_fqid("topic/1312354708"): ["Object updated"],
                    get_fqid(f"mediafile/{self.attachments[0]}"): [
                        "Object attached to topic"
                    ],
                    get_fqid(f"mediafile/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_correct_3(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_3, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/6259289755"),
                        "fields": {"title": "title_Ashae0quei", "attachment_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("mediafile/3549387598"),
                        "fields": {"attachment_ids": []},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid("mediafile/3549387598"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_correct_4(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_4, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/6259289755"),
                        "fields": {"attachment_ids": self.attachments},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile/{self.attachments[1]}"),
                        "fields": {"attachment_ids": [get_fqid("topic/6259289755")]},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid(f"mediafile/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_correct_5(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_5, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {
                        "type": "update",
                        "fqid": get_fqid("topic/6259289755"),
                        "fields": {"attachment_ids": [self.attachments[1]]},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile/{self.attachments[0]}"),
                        "fields": {"attachment_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile/{self.attachments[1]}"),
                        "fields": {"attachment_ids": [get_fqid("topic/6259289755")]},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid(f"mediafile/{self.attachments[0]}"): [
                        "Object attachment to topic reset"
                    ],
                    get_fqid(f"mediafile/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)


class TopicUpdateActionWSGITester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 5968705978
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )
        self.client = Client(self.application)

    def test_wsgi_request_empty(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": [{}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.update",
                    "data": [{"wrong_field": "text_Hoh3quoos9"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_2(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_3(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_3}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_4(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_4}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_5(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_5}],
        )
        self.assert_status_code(response, 200)


class TopicUpdateActionWSGITesterNoPermission(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionView", superuser=0
        )
        self.client = Client(self.application)

    def test_wsgi_request_no_permission_1(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_3(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_3}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_4(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_4}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_5(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_5}],
        )
        self.assert_status_code(response, 403)


class BaseTopicDeleteActionTester(BaseActionTestCase):
    """
    Tests the topic delete action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [{"id": 1312354708}]
        self.valid_payload_2 = [
            {"id": 1312354708},
            {"id": 6259289755},
        ]
        self.pseudo_valid_payload_3 = [{"id": 5756367535}]


class TopicDeleteActionUnitTester(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        user_id = 5968705978
        self.action = TopicDelete(
            "topic.delete",
            PermissionTestAdapter(superuser=user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )
        self.action.user_id = user_id

    def test_validation_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Eichielao7"}]
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_correct_1(self) -> None:
        self.action.validate(self.valid_payload_1)

    def test_validation_correct_2(self) -> None:
        self.action.validate(self.valid_payload_2)

    def test_validation_correct_3(self) -> None:
        self.action.validate(self.pseudo_valid_payload_3)

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": {
                        "id": self.valid_payload_1[0]["id"],
                        "meeting_id": None,
                        "agenda_item_id": None,
                        "attachment_ids": None,
                        "list_of_speakers_id": None,
                        "tag_ids": None,
                    },
                    "relations": {
                        get_fqfield("meeting/7816466305/topic_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                }
            ],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": {
                        "id": self.valid_payload_2[0]["id"],
                        "meeting_id": None,
                        "agenda_item_id": None,
                        "attachment_ids": None,
                        "list_of_speakers_id": None,
                        "tag_ids": None,
                    },
                    "relations": {
                        get_fqfield("meeting/7816466305/topic_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                },
                {
                    "instance": {
                        "id": self.valid_payload_2[1]["id"],
                        "meeting_id": None,
                        "agenda_item_id": None,
                        "attachment_ids": None,
                        "list_of_speakers_id": None,
                        "tag_ids": None,
                    },
                    "relations": {
                        get_fqfield("meeting/3611987967/topic_ids"): {
                            "type": "remove",
                            "value": [6375863023],
                        },
                        get_fqfield("mediafile/3549387598/attachment_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                },
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        with self.assertRaises(ActionException):
            self.action.prepare_dataset(self.pseudo_valid_payload_3)


class TopicDeleteActionPerformTester(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 5968705978
        self.action = TopicDelete(
            "topic.delete",
            PermissionTestAdapter(superuser=self.user_id),
            DatabaseTestAdapter(old_style_testing=True),
        )

    def test_perform_empty(self) -> None:
        payload: ActionPayload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: ActionPayload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_aizaeMai7E"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_1, user_id=self.user_id
        )
        expected = [
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("topic/1312354708")},
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/7816466305"),
                        "fields": {"topic_ids": []},
                    },
                ],
                "information": {
                    get_fqid("topic/1312354708"): ["Object deleted"],
                    get_fqid("meeting/7816466305"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)

    def test_perform_correct_2(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        result = list(write_request_elements)
        expected = [
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("topic/1312354708")},
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/7816466305"),
                        "fields": {"topic_ids": []},
                    },
                ],
                "information": {
                    get_fqid("topic/1312354708"): ["Object deleted"],
                    get_fqid("meeting/7816466305"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
            },
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("topic/6259289755")},
                    {
                        "type": "update",
                        "fqid": get_fqid("mediafile/3549387598"),
                        "fields": {"attachment_ids": []},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/3611987967"),
                        "fields": {"topic_ids": [6375863023]},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object deleted"],
                    get_fqid("meeting/3611987967"): [
                        "Object attachment to topic reset"
                    ],
                    get_fqid("mediafile/3549387598"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
            },
        ]
        self.assertEqual(result, expected)

    def test_perform_no_permission_1(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_1, user_id=4796568680)

    def test_perform_no_permission_2(self) -> None:
        with self.assertRaises(PermissionDenied):
            self.action.perform(self.valid_payload_2, user_id=4796568680)


class TopicDeleteActionWSGITester(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = 5968705978
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionView", superuser=self.user_id
        )
        self.client = Client(self.application)

    def test_wsgi_request_empty(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": [{}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "topic.delete",
                    "data": [{"wrong_field": "text_path4phahN"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 200)

    def test_wsgi_request_correct_2(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 200)


class TopicDeleteActionWSGITesterNoPermission(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionView", superuser=0
        )
        self.client = Client(self.application)

    def test_wsgi_request_no_permission_1(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_1}],
        )
        self.assert_status_code(response, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_2}],
        )
        self.assert_status_code(response, 403)
