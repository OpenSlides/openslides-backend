from tests.system.action.base import BaseActionTestCase


class MotionSetNumberMixinTest(BaseActionTestCase):
    def test_create_set_number_return_because_number_preset(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "manually",
                },
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                    "meeting_id": 222,
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "number": "A003",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("number") == "A003"

    def test_create_set_number_return_because_number_type_manually(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "manually",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                    "meeting_id": 222,
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "agenda_create": True,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("number") is None
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 222)
        self.assertEqual(agenda_item.get("content_object_id"), "motion/1")

    def test_create_set_number_good(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "1"

    def test_create_set_number_min_digits(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "001"
        assert model.get("number_value") == 1

    def test_create_set_number_prefix_blank_lead_motion(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                    "motions_number_with_blank": True,
                    "motions_amendments_prefix": "B",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion/11": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "001",
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 11,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/12")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "001 B001"
        assert model.get("number_value") == 1

    def test_create_set_number_prefix_blank_lead_motion_number_inc(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                    "motions_number_with_blank": True,
                    "motions_amendments_prefix": "B",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion/11": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "001",
                    "number_value": 3,
                },
                "motion/8": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "001",
                    "number_value": 1,
                    "lead_motion_id": 11,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 11,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/12")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "001 B002"
        assert model.get("number_value") == 2

    def test_create_set_number_get_number_per_category(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                    "motions_number_type": "per_category",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion_category/176": {"name": "name_category_176", "meeting_id": 222},
                "motion/8": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "003",
                    "number_value": 23,
                    "category_id": 176,
                },
            }
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 176,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/9")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "024"
        assert model.get("number_value") == 24

    def test_create_set_number_unique_check_jump(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                    "motions_number_type": "per_category",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion_category/176": {"name": "name_category_176", "meeting_id": 222},
                "motion/8": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "001",
                    "number_value": 23,
                    "category_id": 176,
                },
                "motion/6": {
                    "title": "title_FcnPUXJB",
                    "meeting_id": 222,
                    "state_id": 34,
                    "number": "024",
                    "number_value": 23,
                    "category_id": 176,
                },
            }
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 176,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/9")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") == "025"
        assert model.get("number_value") == 25

    def test_set_number_false(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_min_digits": 3,
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": False,
                },
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("state_id") == 34
        assert model.get("number") is None


class SetNumberMixinSetStateTest(BaseActionTestCase):
    def test_set_state_correct_next_state(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "user/1": {"meeting_ids": [222]},
                "motion_state/76": {
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [],
                    "previous_state_ids": [77],
                    "set_number": True,
                    "meeting_id": 222,
                },
                "motion_state/77": {
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [76],
                    "previous_state_ids": [],
                    "meeting_id": 222,
                },
                "motion/22": {"meeting_id": 222, "title": "test1", "state_id": 77},
            }
        )
        response = self.request("motion.set_state", {"id": 22, "state_id": 76})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("number") == "1"


class SetNumberMixinManuallyTest(BaseActionTestCase):
    def _create_models_for_number_manually_tests(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "manually",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
            }
        )

    def test_complex_example_manually_1(self) -> None:
        self._create_models_for_number_manually_tests()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("number") is None
        assert model.get("number_value") is None

    def test_complex_example_manually_2(self) -> None:
        self._create_models_for_number_manually_tests()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        response2 = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response2, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") is None
        assert motion1.get("number_value") is None
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") is None
        assert motion2.get("number_value") is None

    def test_complex_example_manually_3(self) -> None:
        self._create_models_for_number_manually_tests()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "number": "TEST",
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        response2 = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "number": "TEST",
                "text": "test",
            },
        )
        self.assert_status_code(response2, 400)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "TEST"
        assert motion1.get("number_value") is None
        self.assertIn("Number is not unique.", str(response2.data))


class SetNumberMixinSerialTest(BaseActionTestCase):
    def _create_models_for_number_prefix_test(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "serially_numbered",
                    "motions_number_min_digits": 3,
                    "motions_number_with_blank": True,
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion_category/7": {"name": "A", "prefix": "A", "meeting_id": 222},
                "motion_category/8": {"name": "B", "prefix": "B", "meeting_id": 222},
                "motion_category/9": {"name": "no prefix", "meeting_id": 222},
            }
        )

    def test_complex_example_serially_numbered_1(self) -> None:
        self._create_models_for_number_prefix_test()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "B 002"
        assert motion2.get("number_value") == 2

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "003"
        assert motion3.get("number_value") == 3

    def test_complex_example_serially_numbered_2(self) -> None:
        self._create_models_for_number_prefix_test()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "B 002"
        assert motion2.get("number_value") == 2

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "B 003"
        assert motion3.get("number_value") == 3

    def test_complex_example_serially_numbered_3(self) -> None:
        self._create_models_for_number_prefix_test()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        response = self.request("motion.delete", {"id": 1})
        self.assert_status_code(response, 200)

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/2")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1


class SetNumberMixinComplexExamplesPerCategoryTest(BaseActionTestCase):
    def _create_models_for_number_per_category_1(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "per_category",
                    "motions_number_min_digits": 3,
                    "motions_number_with_blank": False,
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion_category/7": {"name": "A", "prefix": "A", "meeting_id": 222},
                "motion_category/8": {"name": "B", "prefix": "B", "meeting_id": 222},
                "motion_category/9": {"name": "no prefix", "meeting_id": 222},
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
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A001"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 7,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "A002"
        assert motion2.get("number_value") == 2

        # create two motions of category B
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "B001"
        assert motion3.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 8,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion4 = self.get_model("motion/4")
        assert motion4.get("number") == "B002"
        assert motion4.get("number_value") == 2

        # create two motions of category "no prefix"
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion5 = self.get_model("motion/5")
        assert motion5.get("number") == "001"
        assert motion5.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "category_id": 9,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion6 = self.get_model("motion/6")
        assert motion6.get("number") == "002"
        assert motion6.get("number_value") == 2

    def test_complex_example_per_category_1_2(self) -> None:
        self._create_models_for_number_per_category_1()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "001"
        assert motion1.get("number_value") == 1

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
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "2"
        assert motion2.get("number_value") == 2

    def _create_models_for_number_per_category_2(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "meeting/222": {
                    "motions_number_type": "per_category",
                    "motions_number_min_digits": 3,
                    "motions_number_with_blank": True,
                    "motions_amendments_prefix": "X-",
                },
                "user/1": {"meeting_ids": [222]},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "name": "name_state34",
                    "meeting_id": 222,
                    "set_number": True,
                },
                "motion_category/7": {"name": "A", "prefix": "A", "meeting_id": 222},
            }
        )

    def test_complex_example_per_category_2_1(self) -> None:
        self._create_models_for_number_per_category_2()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "A 001 X-001"
        assert motion2.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "A 001 X-002"
        assert motion3.get("number_value") == 2

    def test_complex_example_per_category_2_2(self) -> None:
        self._create_models_for_number_per_category_2()
        self.update_model(
            "meeting/222",
            {
                "name": "name_SNLGsvIV",
                "motions_number_type": "per_category",
                "motions_number_min_digits": 1,
                "motions_number_with_blank": False,
                "motions_amendments_prefix": "X-",
                "is_active_in_organization_id": 1,
            },
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A1"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "A1X-1"
        assert motion2.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "A1X-2"
        assert motion3.get("number_value") == 2

    def test_complex_example_per_category_2_3(self) -> None:
        self._create_models_for_number_per_category_2()

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        self.update_model(
            "meeting/222",
            {
                "name": "name_SNLGsvIV",
                "motions_number_type": "per_category",
                "motions_number_min_digits": 1,
                "motions_number_with_blank": False,
                "motions_amendments_prefix": "X-",
                "is_active_in_organization_id": 1,
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "A 001X-1"
        assert motion2.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "A 001X-2"
        assert motion3.get("number_value") == 2

    def test_complex_example_per_category_2_4(self) -> None:
        self._create_models_for_number_per_category_2()

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        motion1 = self.get_model("motion/1")
        assert motion1.get("number") == "A 001"
        assert motion1.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion2 = self.get_model("motion/2")
        assert motion2.get("number") == "A 001 X-001"
        assert motion2.get("number_value") == 1

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        motion3 = self.get_model("motion/3")
        assert motion3.get("number") == "A 001 X-002"
        assert motion3.get("number_value") == 2

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
                "category_id": 7,
            },
        )
        self.assert_status_code(response, 200)
        motion4 = self.get_model("motion/4")
        assert motion4.get("number") == "A 003"
        assert motion4.get("number_value") == 3


class SetNumberMixinFollowRecommandationTest(BaseActionTestCase):
    def test_set_number(self) -> None:
        self.create_meeting(222)
        self.set_models(
            {
                "user/1": {"meeting_ids": [222]},
                "motion_category/7": {"name": "A", "prefix": "A", "meeting_id": 222},
                "motion_state/76": {
                    "name": "test0",
                    "motion_ids": [],
                    "next_state_ids": [77],
                    "previous_state_ids": [],
                    "show_state_extension_field": True,
                    "show_recommendation_extension_field": True,
                    "set_number": True,
                    "meeting_id": 222,
                },
                "motion_state/77": {
                    "name": "test1",
                    "motion_ids": [22],
                    "first_state_of_workflow_id": 76,
                    "next_state_ids": [],
                    "previous_state_ids": [76],
                    "set_number": True,
                    "meeting_id": 222,
                },
                "motion/22": {
                    "meeting_id": 222,
                    "title": "test1",
                    "state_id": 77,
                    "recommendation_id": 76,
                    "recommendation_extension": "test_test_test",
                    "category_id": 7,
                },
            }
        )
        response = self.request("motion.follow_recommendation", {"id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/22")
        assert model.get("state_id") == 76
        assert model.get("state_extension") == "test_test_test"
        assert model.get("number") == "A1"
