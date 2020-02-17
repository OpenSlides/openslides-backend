from unittest import TestCase

from openslides_backend.actions import Payload
from openslides_backend.actions.topic.create import TopicCreate
from openslides_backend.actions.topic.delete import TopicDelete
from openslides_backend.actions.topic.update import TopicUpdate
from openslides_backend.shared.exceptions import ActionException, PermissionDenied

from ..fake_services.database import TESTDATA, DatabaseTestAdapter
from ..fake_services.permission import PermissionTestAdapter
from ..utils import (
    Client,
    ResponseWrapper,
    create_test_application,
    get_fqfield,
    get_fqid,
)


class BaseTopicCreateActionTester(TestCase):
    """
    Tests the topic create action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {
                "meeting_id": 2393342057,
                "title": "title_ooPhi9ZohC",
                "text": "text_eeKoosahh4",
            }
        ]
        self.attachments = [
            TESTDATA[0]["id"],
            TESTDATA[1]["id"],
        ]
        self.valid_payload_2 = [
            {
                "meeting_id": 4002059810,
                "title": "title_pha2Eirohg",
                "text": "text_CaekiiLai2",
                "mediafile_attachment_ids": self.attachments,
            }
        ]
        self.valid_payload_3 = [{"meeting_id": 3611987967, "title": "title_eivaey2Aeg"}]


class TopicCreateActionUnitTester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.action.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
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

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        result = dataset["data"]
        expected = [
            {
                "instance": self.valid_payload_1[0],
                "new_id": 42,
                "references": {
                    get_fqfield("meeting/2393342057/topic_ids"): {
                        "type": "add",
                        "value": [42],
                    },
                },
            }
        ]
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(result, expected)

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_2[0],
                    "new_id": 42,
                    "references": {
                        get_fqfield("meeting/4002059810/topic_ids"): {
                            "type": "add",
                            "value": [42],
                        },
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): {"type": "add", "value": [6259289755, 42]},
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): {"type": "add", "value": [42]},
                    },
                }
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_3)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_3[0],
                    "new_id": 42,
                    "references": {
                        get_fqfield("meeting/3611987967/topic_ids"): {
                            "type": "add",
                            "value": [6375863023, 6259289755, 42],
                        },
                    },
                }
            ],
        )

    def test_prepare_dataset_no_permission(self) -> None:
        unknown_meeting = 1730810210
        payload = [{"meeting_id": unknown_meeting, "title": "title_ieB2ohveec"}]
        with self.assertRaises(PermissionDenied) as context_manager:
            self.action.prepare_dataset(payload)
        self.assertEqual(
            context_manager.exception.message,
            f"User does not have topic.can_manage permission for meeting_id {unknown_meeting}.",
        )


class TopicCreateActionPerformTester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_perform_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: Payload = [{}]
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
        expected = [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": get_fqid("topic/42"),
                        "fields": {
                            "meeting_id": 2393342057,
                            "title": "title_ooPhi9ZohC",
                            "text": "text_eeKoosahh4",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/2393342057/"),
                        "fields": {"topic_ids": [42]},
                    },
                ],
                "information": {
                    get_fqid("topic/42"): ["Object created"],
                    get_fqid("meeting/2393342057"): ["Object attached to topic"],
                },
                "user_id": self.user_id,
                "locked_fields": {get_fqfield("meeting/2393342057/topic_ids"): 1},
            },
        ]
        self.assertEqual(result, expected)

    def test_perform_correct_2(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_2, user_id=self.user_id
        )
        result = list(write_request_elements)
        expected = [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": get_fqid("topic/42"),
                        "fields": {
                            "meeting_id": 4002059810,
                            "title": "title_pha2Eirohg",
                            "text": "text_CaekiiLai2",
                            "mediafile_attachment_ids": self.attachments,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[0]}"),
                        "fields": {"topic_ids": [6259289755, 42],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[1]}"),
                        "fields": {"topic_ids": [42],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/4002059810"),
                        "fields": {"topic_ids": [42],},
                    },
                ],
                "information": {
                    get_fqid("topic/42"): ["Object created"],
                    get_fqid("meeting/4002059810"): ["Object attached to topic"],
                    get_fqid(f"mediafile_attachment/{self.attachments[0]}"): [
                        "Object attached to topic"
                    ],
                    get_fqid(f"mediafile_attachment/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("meeting/4002059810/topic_ids"): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                    ): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                    ): 1,
                },
            }
        ]
        self.assertEqual(result, expected)

    def test_perform_correct_3(self) -> None:
        write_request_elements = self.action.perform(
            self.valid_payload_3, user_id=self.user_id
        )
        e = list(write_request_elements)
        expected = [
            {
                "events": [
                    {
                        "type": "create",
                        "fqid": get_fqid("topic/42"),
                        "fields": {
                            "meeting_id": 3611987967,
                            "title": "title_eivaey2Aeg",
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/3611987967"),
                        "fields": {"topic_ids": [6375863023, 6259289755, 42,],},
                    },
                ],
                "information": {
                    get_fqid("topic/42"): ["Object created"],
                    get_fqid("meeting/3611987967"): ["Object attached to topic"],
                },
                "user_id": self.user_id,
                "locked_fields": {get_fqfield("meeting/3611987967/topic_ids"): 1},
            }
        ]
        self.assertEqual(e, expected)

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
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionsView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/", json=[{"action": "topic.create", "data": [{}]}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[
                {
                    "action": "topic.create",
                    "data": [{"wrong_field": "text_TaenePha0e"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 200)


class TopicCreateActionWSGITesterNoPermission(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionsView"
        )

    def test_wsgi_request_no_permission_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 403)


class BaseTopicUpdateActionTester(TestCase):
    """
    Tests the topic update action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [
            {"id": 1312354708, "title": "title_ahbuQu9ooz", "text": "text_thuF7Ahxee"}
        ]
        self.attachments = [
            TESTDATA[0]["id"],
            TESTDATA[1]["id"],
        ]
        self.valid_payload_2 = [
            {
                "id": 1312354708,
                "title": "title_pai9oN2aec",
                "text": "text_oon2lai3Ie",
                "mediafile_attachment_ids": self.attachments,
            }
        ]
        self.valid_payload_3 = [
            {
                "id": 6259289755,
                "title": "title_Ashae0quei",
                "mediafile_attachment_ids": [],
            }
        ]
        self.valid_payload_4 = [
            {"id": 6259289755, "mediafile_attachment_ids": self.attachments}
        ]
        self.valid_payload_5 = [
            {"id": 6259289755, "mediafile_attachment_ids": [self.attachments[1]]}
        ]


class TopicUpdateActionUnitTester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicUpdate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.action.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
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
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"], [{"instance": self.valid_payload_1[0], "references": {}}],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_2[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): {"type": "add", "value": [6259289755, 1312354708]},
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): {"type": "add", "value": [1312354708]},
                    },
                }
            ],
        )

    def test_prepare_dataset_3(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_3)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_3[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): {"type": "remove", "value": []},
                    },
                }
            ],
        )

    def test_prepare_dataset_4(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_4)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_4[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): {"type": "add", "value": [6259289755]},
                    },
                }
            ],
        )

    def test_prepare_dataset_5(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_5)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": self.valid_payload_5[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): {"type": "remove", "value": []},
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): {"type": "add", "value": [6259289755]},
                    },
                }
            ],
        )


class TopicUpdateActionPerformTester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicUpdate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_perform_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: Payload = [{}]
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
                "locked_fields": {get_fqfield("topic/1312354708/deleted"): 1},
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
                            "mediafile_attachment_ids": self.attachments,
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[0]}"),
                        "fields": {"topic_ids": [6259289755, 1312354708],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[1]}"),
                        "fields": {"topic_ids": [1312354708],},
                    },
                ],
                "information": {
                    get_fqid("topic/1312354708"): ["Object updated"],
                    get_fqid(f"mediafile_attachment/{self.attachments[0]}"): [
                        "Object attached to topic"
                    ],
                    get_fqid(f"mediafile_attachment/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("topic/1312354708/deleted"): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                    ): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                    ): 1,
                },
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
                        "fields": {
                            "title": "title_Ashae0quei",
                            "mediafile_attachment_ids": [],
                        },
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("mediafile_attachment/3549387598"),
                        "fields": {"topic_ids": [],},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid("mediafile_attachment/3549387598"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("topic/6259289755/deleted"): 1,
                    get_fqfield("mediafile_attachment/3549387598/topic_ids"): 1,
                },
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
                        "fields": {"mediafile_attachment_ids": self.attachments,},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[1]}"),
                        "fields": {"topic_ids": [6259289755],},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid(f"mediafile_attachment/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("topic/6259289755/deleted"): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                    ): 1,
                },
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
                        "fields": {"mediafile_attachment_ids": [self.attachments[1]],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[0]}"),
                        "fields": {"topic_ids": [],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid(f"mediafile_attachment/{self.attachments[1]}"),
                        "fields": {"topic_ids": [6259289755],},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object updated"],
                    get_fqid(f"mediafile_attachment/{self.attachments[0]}"): [
                        "Object attachment to topic reset"
                    ],
                    get_fqid(f"mediafile_attachment/{self.attachments[1]}"): [
                        "Object attached to topic"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("topic/6259289755/deleted"): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                    ): 1,
                    get_fqfield(
                        f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                    ): 1,
                },
            },
        ]
        result = list(write_request_elements)
        self.assertEqual(result, expected)


class TopicUpdateActionWSGITester(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionsView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/", json=[{"action": "topic.update", "data": [{}]}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[
                {
                    "action": "topic.update",
                    "data": [{"wrong_field": "text_Hoh3quoos9"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_4(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_4}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_5(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_5}],
        )
        self.assertEqual(response.status_code, 200)


class TopicUpdateActionWSGITesterNoPermission(BaseTopicUpdateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionsView"
        )

    def test_wsgi_request_no_permission_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_4(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_4}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_5(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.update", "data": self.valid_payload_5}],
        )
        self.assertEqual(response.status_code, 403)


class BaseTopicDeleteActionTester(TestCase):
    """
    Tests the topic delete action.
    """

    def setUp(self) -> None:
        self.valid_payload_1 = [{"id": 1312354708}]
        self.valid_payload_2 = [
            {"id": 1312354708},
            {"id": 6259289755},
        ]


class TopicDeleteActionUnitTester(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicDelete(PermissionTestAdapter(), DatabaseTestAdapter())
        self.action.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_validation_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.validate(payload)

    def test_validation_empty_2(self) -> None:
        payload: Payload = [{}]
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

    def test_prepare_dataset_1(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_1)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": {
                        "id": self.valid_payload_1[0]["id"],
                        "meeting_id": None,
                        "mediafile_attachment_ids": None,
                    },
                    "references": {
                        get_fqfield("meeting/7816466305/topic_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                    "cascade_delete": {},
                }
            ],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "instance": {
                        "id": self.valid_payload_2[0]["id"],
                        "meeting_id": None,
                        "mediafile_attachment_ids": None,
                    },
                    "references": {
                        get_fqfield("meeting/7816466305/topic_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                    "cascade_delete": {},
                },
                {
                    "instance": {
                        "id": self.valid_payload_2[1]["id"],
                        "meeting_id": None,
                        "mediafile_attachment_ids": None,
                    },
                    "references": {
                        get_fqfield("meeting/3611987967/topic_ids"): {
                            "type": "remove",
                            "value": [6375863023],
                        },
                        get_fqfield("mediafile_attachment/3549387598/topic_ids"): {
                            "type": "remove",
                            "value": [],
                        },
                    },
                    "cascade_delete": {},
                },
            ],
        )


class TopicDeleteActionPerformTester(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicDelete(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )

    def test_perform_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: Payload = [{}]
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
                "locked_fields": {
                    get_fqfield("topic/1312354708/deleted"): 1,
                    get_fqfield("meeting/7816466305/topic_ids"): 1,
                },
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
                "locked_fields": {
                    get_fqfield("topic/1312354708/deleted"): 1,
                    get_fqfield("meeting/7816466305/topic_ids"): 1,
                },
            },
            {
                "events": [
                    {"type": "delete", "fqid": get_fqid("topic/6259289755")},
                    {
                        "type": "update",
                        "fqid": get_fqid("mediafile_attachment/3549387598"),
                        "fields": {"topic_ids": [],},
                    },
                    {
                        "type": "update",
                        "fqid": get_fqid("meeting/3611987967"),
                        "fields": {"topic_ids": [6375863023],},
                    },
                ],
                "information": {
                    get_fqid("topic/6259289755"): ["Object deleted"],
                    get_fqid("meeting/3611987967"): [
                        "Object attachment to topic reset"
                    ],
                    get_fqid("mediafile_attachment/3549387598"): [
                        "Object attachment to topic reset"
                    ],
                },
                "user_id": self.user_id,
                "locked_fields": {
                    get_fqfield("topic/6259289755/deleted"): 1,
                    get_fqfield("meeting/3611987967/topic_ids"): 1,
                    get_fqfield("mediafile_attachment/3549387598/topic_ids"): 1,
                },
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
        self.user_id = (
            5968705978  # This user has perm TOPIC_CAN_MANAGE for some meetings.
        )
        self.application = create_test_application(
            user_id=self.user_id, view_name="ActionsView"
        )

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/", json=[{"action": "topic.delete", "data": [{}]}])
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/",
            json=[
                {
                    "action": "topic.delete",
                    "data": [{"wrong_field": "text_path4phahN"}],
                }
            ],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'id\\'] properties", str(response.data),
        )

    def test_wsgi_request_correct_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 200)


class TopicDeleteActionWSGITesterNoPermission(BaseTopicDeleteActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.application = create_test_application(
            user_id=self.user_id_no_permission, view_name="ActionsView"
        )

    def test_wsgi_request_no_permission_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/", json=[{"action": "topic.delete", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 403)
