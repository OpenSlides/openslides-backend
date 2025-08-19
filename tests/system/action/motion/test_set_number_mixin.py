from typing import Any

from tests.system.action.base import BaseActionTestCase


class MotionSetNumberMixinTest(BaseActionTestCase):
    def set_test_models(self, meeting_data: dict[str, Any] = {}) -> None:
        self.create_meeting(222, meeting_data)
        self.set_user_groups(1, [222])

    def test_create_set_number_return_because_number_preset(self) -> None:
        self.set_test_models({"motions_number_type": "manually"})
        self.set_models({"motion_state/222": {"set_number": True}})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "number": "A003",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "number": "A003",
            },
        )

    def test_create_set_number_return_because_number_type_manually(self) -> None:
        self.set_test_models({"motions_number_type": "manually"})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "agenda_create": True,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "number": None,
            },
        )
        self.assert_model_exists(
            "agenda_item/1",
            {"meeting_id": 222, "content_object_id": "motion/1"},
        )

    def test_create_set_number_good(self) -> None:
        self.set_test_models({"motions_number_min_digits": None})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "1",
            },
        )

    def test_create_set_number_min_digits(self) -> None:
        self.set_test_models({"motions_number_min_digits": 3})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "001",
                "number_value": 1,
            },
        )

    def test_create_set_number_prefix_blank_lead_motion(self) -> None:
        self.set_test_models(
            {
                "motions_number_min_digits": 3,
                "motions_number_with_blank": True,
                "motions_amendments_prefix": "B",
            }
        )
        self.create_motion(222, 11, motion_data={"number": "001"})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "lead_motion_id": 11,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/12",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "001 B001",
                "number_value": 1,
            },
        )

    def test_create_set_number_prefix_blank_lead_motion_number_inc(self) -> None:
        self.set_test_models(
            {
                "motions_number_min_digits": 3,
                "motions_number_with_blank": True,
                "motions_amendments_prefix": "B",
            }
        )
        self.create_motion(
            meeting_id=222,
            base=11,
            motion_data={
                "title": "title_FcnPUXJB",
                "number": "001",
                "number_value": 3,
            },
        )
        self.create_motion(
            meeting_id=222,
            base=8,
            motion_data={
                "title": "title_FcnPUXJB",
                "number": "001",
                "number_value": 1,
                "lead_motion_id": 11,
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "lead_motion_id": 11,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/12",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "001 B002",
                "number_value": 2,
            },
        )

    def test_create_set_number_get_number_per_category(self) -> None:
        self.set_test_models(
            {"motions_number_min_digits": 3, "motions_number_type": "per_category"}
        )
        self.set_models(
            {
                "motion_category/176": {
                    "name": "name_category_176",
                    "meeting_id": 222,
                    "sequential_number": 176,
                },
            }
        )
        self.create_motion(
            meeting_id=222,
            base=8,
            motion_data={"number": "003", "number_value": 23, "category_id": 176},
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 176,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/9",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "024",
                "number_value": 24,
            },
        )

    def test_create_set_number_unique_check_jump(self) -> None:
        self.set_test_models(
            {"motions_number_min_digits": 3, "motions_number_type": "per_category"}
        )
        self.set_models(
            {
                "motion_category/176": {
                    "name": "name_category_176",
                    "meeting_id": 222,
                    "sequential_number": 176,
                },
            }
        )
        self.create_motion(
            meeting_id=222,
            base=8,
            motion_data={"number": "001", "number_value": 23, "category_id": 176},
        )
        self.create_motion(
            meeting_id=222,
            base=6,
            motion_data={"number": "024", "number_value": 24, "category_id": 176},
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 176,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/9",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": "025",
                "number_value": 25,
            },
        )

    def test_set_number_false(self) -> None:
        self.set_test_models({"motions_number_min_digits": 3})
        self.set_models({"motion_state/222": {"set_number": False}})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "state_id": 222,
                "number": None,
            },
        )


class SetNumberMixinSetStateTest(BaseActionTestCase):
    def test_set_state_correct_next_state(self) -> None:
        self.create_meeting(222)
        self.create_motion(222, 22)
        self.set_models(
            {
                "motion_state/76": {
                    "name": "test0",
                    "workflow_id": 222,
                    "weight": 76,
                    "set_number": True,
                    "meeting_id": 222,
                },
                "motion_state/222": {
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [76],
                },
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {"state_id": 76, "number": "01", "number_value": 1},
        )


class SetNumberMixinManuallyTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(222, {"motions_number_type": "manually"})
        self.set_models({"motion_state/222": {"set_number": True}})

    def test_complex_example_manually_success_no_value(self) -> None:
        self.create_motion(222)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": None, "number_value": None})

    def test_complex_example_manually_success_with_value(self) -> None:
        self.create_motion(222)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "number": "TEST",
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "TEST", "number_value": None})

    def test_complex_example_manually_not_unique(self) -> None:
        self.create_motion(222, 1, motion_data={"number": "TEST"})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "number": "TEST",
                "text": "test",
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/2")
        self.assertEqual("Number is not unique.", response.json["message"])


class SetNumberMixinSerialTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(
            222,
            {
                "motions_number_type": "serially_numbered",
                "motions_number_min_digits": 3,
                "motions_number_with_blank": True,
            },
        )
        self.set_models(
            {
                "motion_state/222": {"set_number": True},
                "motion_category/7": {
                    "name": "A",
                    "prefix": "A",
                    "meeting_id": 222,
                    "sequential_number": 7,
                },
                "motion_category/8": {
                    "name": "B",
                    "prefix": "B",
                    "meeting_id": 222,
                    "sequential_number": 8,
                },
                "motion_category/9": {
                    "name": "no prefix",
                    "meeting_id": 222,
                    "sequential_number": 9,
                },
            }
        )

    def test_complex_example_serially_numbered_1(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "B 002", "number_value": 2})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/3", {"number": "003", "number_value": 3})

    def test_complex_example_serially_numbered_2(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "B 002", "number_value": 2})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/3", {"number": "B 003", "number_value": 3})

    def test_complex_example_serially_numbered_3(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        response = self.request("motion.delete", {"id": 1})
        self.assert_status_code(response, 200)

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "A 001", "number_value": 1})


class SetNumberMixinComplexExamplesPerCategoryTest(BaseActionTestCase):
    def set_test_models(self, meeting_data: dict[str, Any] = {}) -> None:
        self.create_meeting(
            222,
            {
                "motions_number_type": "per_category",
                "motions_number_min_digits": 3,
                **meeting_data,
            },
        )
        self.set_user_groups(1, [222])
        self.set_models(
            {
                "motion_state/222": {"set_number": True},
                "motion_category/7": {
                    "name": "A",
                    "prefix": "A",
                    "meeting_id": 222,
                    "sequential_number": 7,
                },
            }
        )

    def _create_models_for_number_per_category_1(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                "motion_category/8": {
                    "name": "B",
                    "prefix": "B",
                    "meeting_id": 222,
                    "sequential_number": 8,
                },
                "motion_category/9": {
                    "name": "no prefix",
                    "meeting_id": 222,
                    "sequential_number": 9,
                },
            }
        )

    def test_complex_example_per_category_1_1(self) -> None:
        self._create_models_for_number_per_category_1()

        # create two motions of category A
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "A002", "number_value": 2})

        # create two motions of category B
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/3", {"number": "B001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/4", {"number": "B002", "number_value": 2})

        # create two motions of category "no prefix"
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/5", {"number": "001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/6", {"number": "002", "number_value": 2})

    def test_complex_example_per_category_1_2(self) -> None:
        self._create_models_for_number_per_category_1()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "001", "number_value": 1})

        self.update_model(
            "meeting/222",
            {
                "name": "name_SNLGsvIV",
                "motions_number_type": "per_category",
                "motions_number_min_digits": 1,
                "motions_number_with_blank": False,
                "is_active_in_organization_id": 1,
            },
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "2", "number_value": 2})

    def _create_models_for_number_per_category_2(self) -> None:
        self.set_test_models(
            {"motions_number_with_blank": True, "motions_amendments_prefix": "X-"}
        )

    def test_complex_example_per_category_2_1(self) -> None:
        self._create_models_for_number_per_category_2()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2", {"number": "A 001 X-001", "number_value": 1}
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"number": "A 001 X-002", "number_value": 2}
        )

    def test_complex_example_per_category_2_2(self) -> None:
        self._create_models_for_number_per_category_2()
        self.update_model(
            "meeting/222",
            {
                "motions_number_type": "per_category",
                "motions_number_min_digits": 1,
                "motions_number_with_blank": False,
                "motions_amendments_prefix": "X-",
            },
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A1", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "A1X-1", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/3", {"number": "A1X-2", "number_value": 2})

    def test_complex_example_per_category_2_3(self) -> None:
        self._create_models_for_number_per_category_2()

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        self.update_model(
            "meeting/222",
            {
                "motions_number_type": "per_category",
                "motions_number_min_digits": 1,
                "motions_number_with_blank": False,
                "motions_amendments_prefix": "X-",
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/2", {"number": "A 001X-1", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/3", {"number": "A 001X-2", "number_value": 2})

    def test_complex_example_per_category_2_4(self) -> None:
        self._create_models_for_number_per_category_2()

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"number": "A 001", "number_value": 1})

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2", {"number": "A 001 X-001", "number_value": 1}
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"number": "A 001 X-002", "number_value": 2}
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 222,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/4", {"number": "A 003", "number_value": 3})


class SetNumberMixinFollowRecommandationTest(BaseActionTestCase):
    def test_set_number(self) -> None:
        self.create_meeting(222, {"motions_number_min_digits": None})
        self.set_models(
            {
                "motion_category/7": {
                    "name": "A",
                    "prefix": "A",
                    "meeting_id": 222,
                    "sequential_number": 7,
                },
                "motion_state/76": {
                    "name": "test0",
                    "workflow_id": 222,
                    "weight": 76,
                    "next_state_ids": [77],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                    "set_number": True,
                    "meeting_id": 222,
                },
                "motion_state/77": {
                    "name": "test1",
                    "workflow_id": 222,
                    "weight": 77,
                    "first_state_of_workflow_id": 76,
                    "previous_state_ids": [76],
                    "set_number": True,
                    "meeting_id": 222,
                },
            }
        )
        self.create_motion(
            meeting_id=222,
            base=22,
            motion_data={
                "state_id": 77,
                "recommendation_id": 76,
                "recommendation_extension": "test_test_test",
                "category_id": 7,
            },
        )

        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/22",
            {"state_id": 76, "state_extension": "test_test_test", "number": "A1"},
        )
