from unittest import TestCase
from unittest.mock import patch

from openslides_backend.actions.actions.base import ActionException, PermissionDenied
from openslides_backend.actions.actions.topic.create import TopicCreate
from openslides_backend.actions.actions.topic.update import TopicUpdate
from openslides_backend.actions.actions.types import Payload
from openslides_backend.actions.http.application import create_application

from ..fake_adapters.authentication import AuthenticationTestAdapter
from ..fake_adapters.database import TESTDATA, DatabaseTestAdapter
from ..fake_adapters.event_store import EventStoreTestAdapter
from ..fake_adapters.permission import PermissionTestAdapter
from ..utils import Client, ResponseWrapper, get_fqfield


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
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_1[0],
                    "new_id": 42,
                    "references": {get_fqfield("meeting/2393342057/topic_ids"): [42]},
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
                    "topic": self.valid_payload_2[0],
                    "new_id": 42,
                    "references": {
                        get_fqfield("meeting/4002059810/topic_ids"): [42],
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [6259289755, 42],
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [42],
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
                    "topic": self.valid_payload_3[0],
                    "new_id": 42,
                    "references": {
                        get_fqfield("meeting/3611987967/topic_ids"): [
                            6375863023,
                            6259289755,
                            42,
                        ]
                    },
                }
            ],
        )


class TopicCreateActionPerformTester(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.action = TopicCreate(PermissionTestAdapter(), DatabaseTestAdapter())
        self.user_id = 5968705978  # This user has perm TOPIC_CAN_MANAGE

    def test_perform_empty(self) -> None:
        payload: Payload = []
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_empty_2(self) -> None:
        payload: Payload = [{}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_fuzzy(self) -> None:
        payload = [{"wrong_field": "text_Kiofee1ieV"}]
        with self.assertRaises(ActionException):
            self.action.perform(payload, user_id=self.user_id)

    def test_perform_correct_1(self) -> None:
        events = self.action.perform(self.valid_payload_1, user_id=self.user_id)
        self.assertEqual(
            list(events),
            [
                {
                    "type": "create",
                    "position": 1,
                    "information": {"user_id": self.user_id, "text": "Topic created"},
                    "fields": {
                        get_fqfield("topic/42/title"): "title_ooPhi9ZohC",
                        get_fqfield("topic/42/text"): "text_eeKoosahh4",
                    },
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Object attached to new topic",
                    },
                    "fields": {get_fqfield("meeting/2393342057/topic_ids"): [42]},
                },
            ],
        )

    def test_perform_correct_2(self) -> None:
        events = self.action.perform(self.valid_payload_2, user_id=self.user_id)
        self.assertEqual(
            list(events),
            [
                {
                    "type": "create",
                    "position": 1,
                    "information": {"user_id": self.user_id, "text": "Topic created"},
                    "fields": {
                        get_fqfield("topic/42/title"): "title_pha2Eirohg",
                        get_fqfield("topic/42/text"): "text_CaekiiLai2",
                        get_fqfield(
                            "topic/42/mediafile_attachment_ids"
                        ): self.attachments,
                    },
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Object attached to new topic",
                    },
                    "fields": {get_fqfield("meeting/4002059810/topic_ids"): [42]},
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Object attached to new topic",
                    },
                    "fields": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [6259289755, 42]
                    },
                },
                {
                    "type": "update",
                    "position": 1,
                    "information": {
                        "user_id": self.user_id,
                        "text": "Object attached to new topic",
                    },
                    "fields": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [42]
                    },
                },
            ],
        )

    def test_perform_correct_3(self) -> None:
        events = self.action.perform(self.valid_payload_3, user_id=self.user_id)
        e = list(events)
        expected = [
            {
                "type": "create",
                "position": 1,
                "information": {"user_id": self.user_id, "text": "Topic created"},
                "fields": {get_fqfield("topic/42/title"): "title_eivaey2Aeg"},
            },
            {
                "type": "update",
                "position": 1,
                "information": {
                    "user_id": self.user_id,
                    "text": "Object attached to new topic",
                },
                "fields": {
                    get_fqfield("meeting/3611987967/topic_ids"): [
                        6375863023,
                        6259289755,
                        42,
                    ]
                },
            },
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
            5968705978  # This user has perm TOPIC_CAN_MANAGE see patch call below.
        )
        self.authentication_patcher = patch(
            "openslides_backend.actions.views.base.AuthenticationHTTPAdapter",
            AuthenticationTestAdapter(self.user_id),
        )
        self.authentication_patcher.start()
        self.permission_patcher = patch(
            "openslides_backend.actions.views.base.PermissionHTTPAdapter",
            PermissionTestAdapter,
        )
        self.permission_patcher.start()
        self.database_patcher = patch(
            "openslides_backend.actions.views.base.DatabaseHTTPAdapter",
            DatabaseTestAdapter,
        )
        self.database_patcher.start()
        self.event_store_patcher = patch(
            "openslides_backend.actions.views.base.EventStoreHTTPAdapter",
            EventStoreTestAdapter,
        )
        self.event_store_patcher.start()
        self.application = create_application()

    def tearDown(self) -> None:
        self.authentication_patcher.stop()
        self.permission_patcher.stop()
        self.database_patcher.stop()
        self.event_store_patcher.stop()

    def test_wsgi_request_empty(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions", json=[{"action": "topic.create", "data": [{}]}]
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_fuzzy(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[
                {
                    "action": "topic.create",
                    "data": [{"wrong_field": "text_Hoh3quoos9"}],
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
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 200)

    def test_wsgi_request_correct_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_3}],
        )
        self.assertEqual(response.status_code, 200)


class TopicCreateActionWSGITesterNoPermission(BaseTopicCreateActionTester):
    def setUp(self) -> None:
        super().setUp()
        self.user_id_no_permission = 9707919439
        self.authentication_patcher = patch(
            "openslides_backend.actions.views.base.AuthenticationHTTPAdapter",
            AuthenticationTestAdapter(self.user_id_no_permission),
        )
        self.authentication_patcher.start()
        self.permission_patcher = patch(
            "openslides_backend.actions.views.base.PermissionHTTPAdapter",
            PermissionTestAdapter,
        )
        self.permission_patcher.start()
        self.database_patcher = patch(
            "openslides_backend.actions.views.base.DatabaseHTTPAdapter",
            DatabaseTestAdapter,
        )
        self.database_patcher.start()
        self.application = create_application()

    def tearDown(self) -> None:
        self.authentication_patcher.stop()
        self.permission_patcher.stop()
        self.database_patcher.stop()

    def test_wsgi_request_no_permission_1(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_1}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_2}],
        )
        self.assertEqual(response.status_code, 403)

    def test_wsgi_request_no_permission_3(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "topic.create", "data": self.valid_payload_3}],
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
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"], [{"topic": self.valid_payload_1[0], "references": {}}],
        )

    def test_prepare_dataset_2(self) -> None:
        dataset = self.action.prepare_dataset(self.valid_payload_2)
        self.assertEqual(dataset["position"], 1)
        self.assertEqual(
            dataset["data"],
            [
                {
                    "topic": self.valid_payload_2[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [6259289755, 1312354708],
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [1312354708],
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
                    "topic": self.valid_payload_3[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [],
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
                    "topic": self.valid_payload_4[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [6259289755],
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
                    "topic": self.valid_payload_5[0],
                    "references": {
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[0]}/topic_ids"
                        ): [],
                        get_fqfield(
                            f"mediafile_attachment/{self.attachments[1]}/topic_ids"
                        ): [6259289755],
                    },
                }
            ],
        )
