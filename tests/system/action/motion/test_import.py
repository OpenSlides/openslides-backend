# from typing import Any

# from openslides_backend.action.mixins.import_mixins import ImportState

# from .test_json_upload import MotionImportTestMixin


# class MotionJsonUpload(MotionImportTestMixin):
#     def set_up_models_with_import_previews_and_get_next_motion_id(
#         self,
#         additional_data: list[dict[str, Any]] = [{}],
#         base_meeting_id: int = 42,
#         base_motion_id: int = 100,
#         base_block_id: int = 1000,
#         base_tag_id: int = 10000,
#         is_reason_required: bool = False,
#         is_set_number: bool = False,
#     ) -> int:
#         (settings, users) = self.get_base_user_and_meeting_settings(
#             base_meeting_id, base_motion_id, is_reason_required, is_set_number
#         )
#         settings = {
#             base_meeting_id: self.extend_meeting_setting_with_blocks(
#                 self.extend_meeting_setting_with_tags(
#                     self.extend_meeting_setting_with_categories(
#                         settings[base_meeting_id],
#                         categories={
#                             400: {"name": "Category A", "prefix": "A"},
#                             401: {"name": "Category B", "prefix": "B"},
#                             403: {"name": "Copygory", "prefix": "COPY"},
#                             404: {"name": "Copygory", "prefix": "COPY"},
#                             405: {"name": "Copygory", "prefix": "KOPIE"},
#                             406: {"name": "Weak Copygory", "prefix": "COPY"},
#                             407: {"name": "No prefix"},
#                         },
#                         motion_to_category_ids={
#                             base_motion_id: 407,
#                             (base_motion_id + 1): 400,
#                             (base_motion_id + 2): 401,
#                             (base_motion_id + 3): 403,
#                             (base_motion_id + 4): 405,
#                         },
#                     ),
#                     base_tag_id,
#                     extra_tags=["Got tag go"],
#                     motion_to_tag_ids={
#                         (base_motion_id + i): [base_tag_id] for i in range(5)
#                     },
#                 ),
#                 base_block_id,
#                 extra_blocks=["Block and roll"],
#                 motion_to_block_ids={
#                     (base_motion_id + i): base_block_id for i in range(5)
#                 },
#             ),
#             (base_meeting_id + 1): self.extend_meeting_setting_with_blocks(
#                 self.extend_meeting_setting_with_tags(
#                     self.extend_meeting_setting_with_categories(
#                         settings[base_meeting_id + 1],
#                         categories={
#                             801: {"name": "Category B", "prefix": "B"},
#                             802: {"name": "Category C", "prefix": "C"},
#                         },
#                         motion_to_category_ids={
#                             base_motion_id * 2: 801,
#                             (base_motion_id * 2 + 1): 802,
#                         },
#                     ),
#                     base_tag_id * 2,
#                     extra_tags=["rag-tag"],
#                     motion_to_tag_ids={},
#                 ),
#                 base_block_id * 2,
#                 extra_blocks=["Blocked"],
#                 motion_to_block_ids={(base_motion_id * 2): (base_block_id * 2)},
#             ),
#         }
#         model_data = {
#             **self.set_up_models(settings, users),
#             "import_preview/2": {
#                 "state": ImportState.DONE,
#                 "name": "motion",
#                 "result": {
#                     "rows": [
#                         {
#                             "state": (
#                                 ImportState.DONE if date.get("id") else ImportState.NEW
#                             ),
#                             "messages": [],
#                             "data": {
#                                 "title": {
#                                     "value": "New",
#                                     "info": ImportState.DONE,
#                                 },
#                                 "text": {
#                                     "value": "Motion",
#                                     "info": ImportState.DONE,
#                                 },
#                                 "number": {"value": "", "info": ImportState.DONE},
#                                 "reason": {"value": "", "info": ImportState.DONE},
#                                 "submitters_username": [
#                                     {
#                                         "value": "admin",
#                                         "info": ImportState.GENERATED,
#                                         "id": 1,
#                                     }
#                                 ],
#                                 "supporters_username": [],
#                                 "category_name": {
#                                     "value": "",
#                                     "info": ImportState.DONE,
#                                 },
#                                 "tags": [],
#                                 "block": {"value": "", "info": ImportState.DONE},
#                                 **date,
#                                 "meeting_id": base_meeting_id,
#                             },
#                         }
#                         for date in additional_data
#                     ],
#                 },
#             },
#             "import_preview/3": {"result": None},
#             "import_preview/4": {
#                 "state": ImportState.DONE,
#                 "name": "topic",
#                 "result": {
#                     "rows": [
#                         {
#                             "state": ImportState.NEW,
#                             "messages": [],
#                             "data": {
#                                 "title": {"value": "test", "info": ImportState.NEW},
#                                 "meeting_id": base_meeting_id,
#                             },
#                         },
#                     ],
#                 },
#             },
#         }
#         self.set_models(model_data)
#         return base_motion_id + 105

#     # -------------------------------------------------------
#     # --------------------[ Basic tests ]--------------------
#     # -------------------------------------------------------

#     def assert_simple_import(
#         self,
#         response: Any,
#         motion_id: int,
#         row_data: dict[str, Any],
#         submitter_user_id_to_weight: dict[int, int] = {1: 1},
#     ) -> None:
#         self.assert_status_code(response, 200)
#         motion = self.assert_model_exists(
#             f"motion/{motion_id}",
#             row_data,
#         )
#         assert len(motion.get("submitter_ids", [])) == len(
#             submitter_user_id_to_weight.keys()
#         )
#         submitter_ids = motion.get("submitter_ids", [])
#         submitter_user_id_to_weight_tuple_list = list(
#             submitter_user_id_to_weight.items()
#         )
#         for i in range(len(submitter_ids)):
#             submitter_id = submitter_ids[i]
#             (
#                 submitter_user_id,
#                 submitter_weight,
#             ) = submitter_user_id_to_weight_tuple_list[i]
#             submitter = self.assert_model_exists(
#                 f"motion_submitter/{submitter_id}",
#                 {"meeting_id": 42, "motion_id": motion_id, "weight": submitter_weight},
#             )
#             assert (meeting_user_id := submitter.get("meeting_user_id"))
#             self.assert_model_exists(
#                 f"meeting_user/{meeting_user_id}",
#                 {"meeting_id": 42, "user_id": submitter_user_id},
#             )
#         self.assert_model_not_exists("import_preview/2")

#     def test_import_create_simple(self) -> None:
#         next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_simple_import(response, next_id, {"title": "New", "text": "Motion"})

#     def test_import_update_simple(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             [
#                 {
#                     "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
#                     "id": 101,
#                 }
#             ]
#         )
#         self.assert_model_exists(
#             "motion/101",
#             {
#                 "number": "NUM01",
#                 "category_id": 400,
#                 "block_id": 1000,
#                 "tag_ids": [10000],
#                 "submitter_ids": [70000],
#             },
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_simple_import(
#             response,
#             101,
#             {
#                 "title": "New",
#                 "text": "Motion",
#                 "number": "NUM01",
#                 "category_id": None,
#                 "block_id": None,
#                 "tag_ids": [],
#                 "submitter_ids": [150101],
#             },
#         )

#     def test_import_update_simple_2(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             [
#                 {
#                     "number": {
#                         "info": ImportState.DONE,
#                         "id": 102,
#                         "value": "AMNDMNT1",
#                     },
#                     "text": {"info": ImportState.DONE, "value": ""},
#                     "id": 102,
#                 }
#             ]
#         )
#         self.assert_model_exists(
#             "motion/102", {"number": "AMNDMNT1", "supporter_meeting_user_ids": [700]}
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_simple_import(
#             response,
#             102,
#             {
#                 "title": "New",
#                 "text": "",
#                 "number": "AMNDMNT1",
#                 "supporter_meeting_user_ids": [],
#             },
#         )

#     def test_import_create_simple_with_reason_required(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             is_reason_required=True
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         assert (
#             "Error: Reason is required"
#             in response.json["results"][0][0]["rows"][0]["messages"]
#         )
#         assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
#         assert (
#             response.json["results"][0][0]["rows"][0]["data"]["reason"]["info"]
#             == ImportState.ERROR
#         )

#     def test_import_update_simple_with_reason_required(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             [
#                 {
#                     "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
#                     "id": 101,
#                 }
#             ],
#             is_reason_required=True,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         assert (
#             "Error: Reason is required to update."
#             in response.json["results"][0][0]["rows"][0]["messages"]
#         )
#         assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
#         assert (
#             response.json["results"][0][0]["rows"][0]["data"]["reason"]["info"]
#             == ImportState.ERROR
#         )

#     def test_import_database_corrupt(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             [
#                 {
#                     "number": {"info": ImportState.DONE, "id": 101, "value": "NUM01"},
#                     "submitters_username": [
#                         {"info": ImportState.DONE, "id": 12345678, "value": "bob"}
#                     ],
#                     "id": 101,
#                 }
#             ]
#         )
#         self.set_models(
#             {
#                 "user/12345678": {
#                     "username": "bob",
#                     "meeting_ids": [42],
#                     "meeting_user_ids": [12345678],
#                 },
#                 "meeting_user/12345678": {},
#                 "user/123456789": {
#                     "username": "bob",
#                     "meeting_ids": [42],
#                     "meeting_user_ids": [123456789],
#                 },
#                 "meeting_user/123456789": {},
#             }
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_status_code(response, 400)
#         assert (
#             "Database corrupt: Found multiple users with the username bob."
#             in response.json["message"]
#         )

#     def test_import_abort(self) -> None:
#         next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
#         response = self.request("motion.import", {"id": 2, "import": False})
#         self.assert_status_code(response, 200)
#         self.assert_model_not_exists("import_preview/2")
#         self.assert_model_not_exists(f"motion/{next_id}")

#     def test_import_wrong_import_preview(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id()
#         response = self.request("motion.import", {"id": 3, "import": True})
#         self.assert_status_code(response, 400)
#         assert (
#             "Wrong id doesn't point on motion import data." in response.json["message"]
#         )

#     def test_import_wrong_meeting_model_import_preview(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id()
#         response = self.request("motion.import", {"id": 4, "import": True})
#         self.assert_status_code(response, 400)
#         assert (
#             "Wrong id doesn't point on motion import data." in response.json["message"]
#         )

#     def prepare_complex_test(
#         self,
#         changed_entries: dict[str, Any] = {},
#         is_update: bool = False,
#         multiple: bool = False,
#     ) -> int:
#         payload: list[dict[str, Any]] = []
#         for i in range(2 if multiple else 1):
#             data: dict[str, Any] = {
#                 "number": {"info": ImportState.DONE, "value": f"DUM0{i + 1}"},
#                 "title": {"info": ImportState.DONE, "value": "Always look on..."},
#                 "text": {
#                     "info": ImportState.DONE,
#                     "value": "...the bright side...",
#                 },
#                 "reason": {"info": ImportState.DONE, "value": "...of life!"},
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 405,
#                     "value": "Copygory",
#                 },
#                 "category_prefix": "KOPIE",
#                 "block": {
#                     "info": ImportState.DONE,
#                     "id": 1001,
#                     "value": "Blockodile",
#                 },
#                 "submitters_username": [
#                     {"info": ImportState.DONE, "id": 3, "value": "firstMeeting"},
#                     {"info": ImportState.DONE, "id": 12, "value": "multiMeeting"},
#                     {
#                         "info": ImportState.DONE,
#                         "id": 7,
#                         "value": "firstMeetingBoth",
#                     },
#                     {
#                         "info": ImportState.DONE,
#                         "id": 4,
#                         "value": "firstMeetingSubmitter",
#                     },
#                 ],
#                 "supporters_username": [
#                     {
#                         "info": ImportState.DONE,
#                         "id": 13,
#                         "value": "multiMeetingSubmitter",
#                     },
#                     {
#                         "info": ImportState.DONE,
#                         "id": 6,
#                         "value": "firstMeetingSupporter",
#                     },
#                 ],
#                 "tags": [
#                     {"info": ImportState.DONE, "id": 10005, "value": "Got tag go"},
#                     {"info": ImportState.DONE, "id": 10002, "value": "Price tag"},
#                 ],
#             }
#             if is_update:
#                 id_ = 104 if i else 101
#                 data.update(
#                     {
#                         "id": id_,
#                         "number": {
#                             "info": ImportState.DONE,
#                             "id": id_,
#                             "value": f"NUM0{i + 1}",
#                         },
#                     }
#                 )
#             for key in changed_entries:
#                 data[key] = changed_entries[key]
#             payload.append(data)
#         return self.set_up_models_with_import_previews_and_get_next_motion_id(payload)

#     def test_import_update_complex(self) -> None:
#         self.prepare_complex_test(is_update=True)
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_simple_import(
#             response,
#             101,
#             {
#                 "title": "Always look on...",
#                 "text": "...the bright side...",
#                 "reason": "...of life!",
#                 "number": "NUM01",
#                 "category_id": 405,
#                 "block_id": 1001,
#                 "submitter_ids": [70000, 150101, 150102, 150103],
#                 "supporter_meeting_user_ids": [1300, 600],
#                 "tag_ids": [10005, 10002],
#             },
#             {7: 3, 3: 1, 12: 2, 4: 4},
#         )

#     def test_import_create_complex(self) -> None:
#         next_id = self.prepare_complex_test()
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_simple_import(
#             response,
#             next_id,
#             {
#                 "title": "Always look on...",
#                 "text": "...the bright side...",
#                 "reason": "...of life!",
#                 "number": "DUM01",
#                 "category_id": 405,
#                 "block_id": 1001,
#                 "submitter_ids": [150101, 150102, 150103, 150104],
#                 "supporter_meeting_user_ids": [1300, 600],
#                 "tag_ids": [10005, 10002],
#             },
#             {3: 1, 12: 2, 7: 3, 4: 4},
#         )

#     def assert_error_for_changed_property(
#         self, response: Any, changed_keys: list[str], error_messages: list[str]
#     ) -> None:
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         errors = response.json["results"][0][0]["rows"][0]["messages"]
#         for message in error_messages:
#             assert message in errors
#         assert len(errors) == len(error_messages)
#         data = response.json["results"][0][0]["rows"][0]["data"]
#         for key in data:
#             if key in changed_keys:
#                 if isinstance(data[key], dict):
#                     assert data[key]["info"] == ImportState.ERROR
#                 elif isinstance(data[key], list):
#                     assert ImportState.ERROR in [date["info"] for date in data[key]]
#             elif isinstance(data[key], dict):
#                 assert data[key]["info"] != ImportState.ERROR
#             elif isinstance(data[key], list):
#                 assert ImportState.ERROR not in [date["info"] for date in data[key]]

#     def test_import_update_changed_number_name(self) -> None:
#         self.prepare_complex_test(
#             {
#                 "number": {
#                     "id": 101,
#                     "info": ImportState.DONE,
#                     "value": "This shouldn't be found",
#                 }
#             },
#             is_update=True,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["number"],
#             [
#                 "Error: Motion 101 not found anymore for updating motion 'This shouldn't be found'."
#             ],
#         )

#     def assert_changed_submitter_name(self, is_update: bool = False) -> None:
#         self.prepare_complex_test(
#             {
#                 "submitters_username": [
#                     {
#                         "id": 7,
#                         "info": ImportState.DONE,
#                         "value": "updatedUser",
#                     }
#                 ]
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["submitters_username"],
#             ["Error: Couldn't find submitter anymore: updatedUser"],
#         )

#     def test_import_create_changed_submitter_name(self) -> None:
#         self.assert_changed_submitter_name()

#     def test_import_update_changed_submitter_name(self) -> None:
#         self.assert_changed_submitter_name(True)

#     def assert_changed_supporter_name(self, is_update: bool = False) -> None:
#         self.prepare_complex_test(
#             {
#                 "supporters_username": [
#                     {
#                         "id": 13,
#                         "info": ImportState.DONE,
#                         "value": "updatedUser",
#                     }
#                 ]
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["supporters_username"],
#             ["Error: Couldn't find supporter anymore: updatedUser"],
#         )

#     def test_import_create_changed_supporter_name(self) -> None:
#         self.assert_changed_supporter_name()

#     def test_import_update_changed_supporter_name(self) -> None:
#         self.assert_changed_supporter_name(True)

#     def assert_changed_tag_name(self, is_update: bool = False) -> None:
#         self.prepare_complex_test(
#             {
#                 "tags": [
#                     {"info": ImportState.DONE, "id": 10005, "value": "Got tag go"},
#                     {"info": ImportState.DONE, "id": 10002, "value": "Tag auch"},
#                 ]
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["tags"],
#             ["Error: Couldn't find tag anymore: Tag auch"],
#         )

#     def test_import_create_changed_tag_name(self) -> None:
#         self.assert_changed_tag_name()

#     def test_import_update_changed_tag_name(self) -> None:
#         self.assert_changed_tag_name(True)

#     def assert_changed_block_name(self, is_update: bool = False) -> None:
#         self.prepare_complex_test(
#             {
#                 "block": {
#                     "info": ImportState.DONE,
#                     "id": 1001,
#                     "value": "Blockschokolade",
#                 }
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["block"],
#             ["Error: Couldn't find motion block anymore"],
#         )

#     def test_import_create_changed_block_name(self) -> None:
#         self.assert_changed_block_name()

#     def test_import_update_changed_block_name(self) -> None:
#         self.assert_changed_block_name(True)

#     def assert_changed_category(
#         self,
#         is_update: bool = False,
#         other_name: bool = False,
#         other_prefix: bool = False,
#     ) -> None:
#         self.prepare_complex_test(
#             {
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 405,
#                     "value": ("Cat, egg or I" if other_name else "Copygory"),
#                 },
#                 "category_prefix": ("L" if other_prefix else "KOPIE"),
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_error_for_changed_property(
#             response,
#             ["category_name"],
#             ["Error: Category could not be found anymore"],
#         )

#     def test_import_create_changed_category_name(self) -> None:
#         self.assert_changed_category(other_name=True)

#     def test_import_update_changed_category_name(self) -> None:
#         self.assert_changed_category(True, other_name=True)

#     def test_import_create_changed_category_prefix(self) -> None:
#         self.assert_changed_category(other_prefix=True)

#     def test_import_update_changed_category_prefix(self) -> None:
#         self.assert_changed_category(True, other_prefix=True)

#     def test_import_create_changed_category_both(self) -> None:
#         self.assert_changed_category(other_name=True, other_prefix=True)

#     def test_import_update_changed_category_both(self) -> None:
#         self.assert_changed_category(True, other_name=True, other_prefix=True)

#     def assert_with_multiple(self, is_update: bool = False) -> None:
#         next_id = self.prepare_complex_test(is_update=is_update, multiple=True)
#         response = self.request("motion.import", {"id": 2, "import": True})
#         assert response.json["results"][0][0]["state"] != ImportState.ERROR
#         for i in range(2):
#             assert (
#                 response.json["results"][0][0]["rows"][i]["state"] != ImportState.ERROR
#             )
#             if is_update:
#                 if i == 0:
#                     submitter_ids = [70000, 150101, 150102, 150103]
#                     submitter_user_id_to_weight = {7: 3, 3: 1, 12: 2, 4: 4}
#                 else:
#                     submitter_ids = [150104 + j for j in range(4)]
#                     submitter_user_id_to_weight = {3: 1, 12: 2, 7: 3, 4: 4}
#             else:
#                 submitter_ids = [150101 + j + i * 4 for j in range(4)]
#                 submitter_user_id_to_weight = {3: 1, 12: 2, 7: 3, 4: 4}
#             self.assert_simple_import(
#                 response,
#                 ((101 + (i * 3)) if is_update else (next_id + i)),
#                 {
#                     "title": "Always look on...",
#                     "text": "...the bright side...",
#                     "reason": "...of life!",
#                     "number": f"NUM0{i + 1}" if is_update else f"DUM0{i + 1}",
#                     "category_id": 405,
#                     "block_id": 1001,
#                     "submitter_ids": submitter_ids,
#                     "supporter_meeting_user_ids": [1300, 600],
#                     "tag_ids": [10005, 10002],
#                 },
#                 submitter_user_id_to_weight,
#             )

#     def test_import_create_with_multiple(self) -> None:
#         self.assert_with_multiple()

#     def test_import_update_with_multiple(self) -> None:
#         self.assert_with_multiple(True)

#     def prepare_complex_different_found_test(
#         self,
#         changed_entries: dict[str, Any] = {},
#         is_update: bool = False,
#     ) -> int:
#         payload: list[dict[str, Any]] = []
#         data: dict[str, Any] = {
#             "number": {"info": ImportState.DONE, "value": "DUM01"},
#             "title": {"info": ImportState.DONE, "value": "Always look on..."},
#             "text": {
#                 "info": ImportState.DONE,
#                 "value": "...the bright side...",
#             },
#             "reason": {"info": ImportState.DONE, "value": "...of life!"},
#             "category_name": {
#                 "info": ImportState.DONE,
#                 "id": 409,
#                 "value": "Copygory",
#             },
#             "category_prefix": "KOPIE",
#             "block": {
#                 "info": ImportState.DONE,
#                 "id": 1009,
#                 "value": "Blockodile",
#             },
#             "submitters_username": [
#                 {"info": ImportState.DONE, "id": 23, "value": "firstMeeting"},
#                 {"info": ImportState.DONE, "id": 22, "value": "multiMeeting"},
#                 {
#                     "info": ImportState.DONE,
#                     "id": 2,
#                     "value": "firstMeetingBoth",
#                 },
#                 {
#                     "info": ImportState.DONE,
#                     "id": 2,
#                     "value": "firstMeetingSubmitter",
#                 },
#             ],
#             "supporters_username": [
#                 {
#                     "info": ImportState.DONE,
#                     "id": 23,
#                     "value": "multiMeetingSubmitter",
#                 },
#                 {
#                     "info": ImportState.DONE,
#                     "id": 26,
#                     "value": "firstMeetingSupporter",
#                 },
#             ],
#             "tags": [
#                 {"info": ImportState.DONE, "id": 10008, "value": "Got tag go"},
#                 {"info": ImportState.DONE, "id": 10009, "value": "Price tag"},
#             ],
#         }
#         if is_update:
#             id_ = 108
#             data.update(
#                 {
#                     "id": id_,
#                     "number": {
#                         "info": ImportState.DONE,
#                         "id": id_,
#                         "value": "NUM01",
#                     },
#                 }
#             )
#         for key in changed_entries:
#             data[key] = changed_entries[key]
#         payload.append(data)
#         return self.set_up_models_with_import_previews_and_get_next_motion_id(payload)

#     def assert_different_found(self, response: Any, is_update: bool = False) -> None:
#         list_fields = ["tags", "supporters_username", "submitters_username"]
#         single_fields = ["category_name", "block"]
#         messages = [
#             "Error: Category search didn't deliver the same result as in the preview",
#             "Error: Motion block search didn't deliver the same result as in the preview",
#             "Error: Tag search didn't deliver the same result as in the preview: Got tag go, Price tag",
#             "Error: Submitter search didn't deliver the same result as in the preview: firstMeeting, multiMeeting, firstMeetingBoth, firstMeetingSubmitter",
#             "Error: Supporter search didn't deliver the same result as in the preview: multiMeetingSubmitter, firstMeetingSupporter",
#         ]
#         if is_update:
#             single_fields.append("number")
#             messages.append(
#                 "Error: Number 'NUM01' found in different id (101 instead of 108)"
#             )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         for message in messages:
#             assert message in response.json["results"][0][0]["rows"][0]["messages"]
#         assert len(response.json["results"][0][0]["rows"][0]["messages"]) == len(
#             messages
#         )
#         assert response.json["results"][0][0]["rows"][0]["state"] == ImportState.ERROR
#         for field in single_fields:
#             assert (
#                 response.json["results"][0][0]["rows"][0]["data"][field]["info"]
#                 == ImportState.ERROR
#             )
#         for field in list_fields:
#             for date in response.json["results"][0][0]["rows"][0]["data"][field]:
#                 assert date["info"] == ImportState.ERROR

#     def test_import_update_different_found(self) -> None:
#         self.prepare_complex_different_found_test(is_update=True)
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_different_found(response, True)

#     def test_import_create_different_found(self) -> None:
#         self.prepare_complex_different_found_test()
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_different_found(response)

#     def assert_different_category(
#         self,
#         is_update: bool = False,
#         changed_entries: dict[str, Any] = {
#             "category_name": {
#                 "info": ImportState.DONE,
#                 "id": 407,
#                 "value": "No prefix",
#             },
#             "category_prefix": "",
#         },
#     ) -> Any:
#         self.prepare_complex_test(
#             changed_entries,
#             is_update,
#         )
#         return self.request("motion.import", {"id": 2, "import": True})

#     def test_import_create_category_no_prefix(self) -> None:
#         response = self.assert_different_category()
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_update_category_no_prefix(self) -> None:
#         response = self.assert_different_category(is_update=True)
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_category_single_meeting(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 400,
#                     "value": "Category A",
#                 },
#                 "category_prefix": "A",
#             }
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_update_category_single_meeting(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 400,
#                     "value": "Category A",
#                 },
#                 "category_prefix": "A",
#             },
#             is_update=True,
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_category_multi_meeting(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 401,
#                     "value": "Category B",
#                 },
#                 "category_prefix": "B",
#             }
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_update_category_multi_meeting(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 401,
#                     "value": "Category B",
#                 },
#                 "category_prefix": "B",
#             },
#             is_update=True,
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_category_duplicate(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 404,
#                     "value": "Copygory",
#                 },
#                 "category_prefix": "COPY",
#             }
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         assert (
#             "Error: Category could not be found anymore"
#             in response.json["results"][0][0]["rows"][0]["messages"]
#         )

#     def test_import_update_category_duplicate(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 403,
#                     "value": "Copygory",
#                 },
#                 "category_prefix": "COPY",
#             },
#             is_update=True,
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.ERROR
#         assert (
#             "Error: Category could not be found anymore"
#             in response.json["results"][0][0]["rows"][0]["messages"]
#         )

#     def test_import_create_category_fake_duplicate_1(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 405,
#                     "value": "Copygory",
#                 },
#                 "category_prefix": "KOPIE",
#             }
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_update_category_fake_duplicate_1(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 405,
#                     "value": "Copygory",
#                 },
#                 "category_prefix": "KOPIE",
#             },
#             is_update=True,
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_category_fake_duplicate_2(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 406,
#                     "value": "Weak Copygory",
#                 },
#                 "category_prefix": "COPY",
#             }
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_update_category_fake_duplicate_2(self) -> None:
#         response = self.assert_different_category(
#             changed_entries={
#                 "category_name": {
#                     "info": ImportState.DONE,
#                     "id": 406,
#                     "value": "Weak Copygory",
#                 },
#                 "category_prefix": "COPY",
#             },
#             is_update=True,
#         )
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     knights = [
#         "Sir Galahad the Pure",
#         "Sir Bedivere the Wise",
#         "Sir Lancelot the Brave",
#         "Sir Robin the-not-quite-so-brave-as-Sir-Lancelot",
#         "Arthur, King of the Britons",
#     ]

#     def assert_with_verbose_fields(
#         self, separate_at: int, is_update: bool = False, multiple: bool = False
#     ) -> None:
#         separate_at = separate_at % 5
#         self.prepare_complex_test(
#             {
#                 "submitters_verbose": self.knights[:separate_at],
#                 "supporters_verbose": self.knights[separate_at:],
#             },
#             is_update,
#             multiple,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_with_verbose_fields_0(self) -> None:
#         self.assert_with_verbose_fields(0)

#     def test_import_create_with_verbose_fields_1(self) -> None:
#         self.assert_with_verbose_fields(1, multiple=True)

#     def test_import_update_with_verbose_fields_2(self) -> None:
#         self.assert_with_verbose_fields(2, True)

#     def test_import_update_with_verbose_fields_3(self) -> None:
#         self.assert_with_verbose_fields(3, True, multiple=True)

#     def test_import_update_with_verbose_fields_4(self) -> None:
#         self.assert_with_verbose_fields(4, True)

#     def assert_with_amendment(
#         self, is_amendment: bool = False, is_update: bool = False
#     ) -> None:
#         self.prepare_complex_test(
#             {
#                 "motion_amendment": (
#                     {"value": "1", "info": ImportState.WARNING}
#                     if is_amendment
#                     else {"value": "0", "info": ImportState.DONE}
#                 ),
#             },
#             is_update,
#         )
#         response = self.request("motion.import", {"id": 2, "import": True})
#         self.assert_status_code(response, 200)
#         assert response.json["results"][0][0]["state"] == ImportState.DONE

#     def test_import_create_with_amendment_false(self) -> None:
#         self.assert_with_amendment()

#     def test_import_create_with_amendment_true(self) -> None:
#         self.assert_with_amendment(True)

#     def test_import_update_with_amendment_false(self) -> None:
#         self.assert_with_amendment(False, True)

#     def test_import_update_with_amendment_true(self) -> None:
#         self.assert_with_amendment(True, True)

#     def assert_after_json_upload(
#         self,
#         response: Any,
#         meeting_id: int,
#         motion_id: int,
#         motion_data: dict[str, Any],
#         submitter_user_ids: list[int] = [1],
#         supporter_user_ids: list[int] = [],
#     ) -> None:
#         self.assert_status_code(response, 200)
#         motion = self.assert_model_exists(
#             f"motion/{motion_id}",
#             motion_data,
#         )
#         assert len(motion.get("submitter_ids", [])) == len(submitter_user_ids)
#         submitter_ids = motion.get("submitter_ids", [])
#         for i in range(len(submitter_ids)):
#             submitter_id = submitter_ids[i]
#             submitter = self.assert_model_exists(
#                 f"motion_submitter/{submitter_id}",
#                 {"meeting_id": meeting_id, "motion_id": motion_id},
#             )
#             assert (meeting_user_id := submitter.get("meeting_user_id"))
#             self.assert_model_exists(
#                 f"meeting_user/{meeting_user_id}",
#                 {"meeting_id": meeting_id, "user_id": submitter_user_ids[i]},
#             )
#         assert len(motion.get("supporter_meeting_user_ids", [])) == len(
#             supporter_user_ids
#         )
#         supporter_ids = motion.get("supporter_meeting_user_ids", [])
#         for i in range(len(supporter_ids)):
#             supporter_id = supporter_ids[i]
#             self.assert_model_exists(
#                 f"meeting_user/{supporter_id}",
#                 {"meeting_id": meeting_id, "user_id": supporter_user_ids[i]},
#             )

#     def test_import_create_with_json_upload_format_1(self) -> None:
#         next_id = self.set_up_models_with_import_previews_and_get_next_motion_id()
#         json_upload_response = self.request(
#             "motion.json_upload",
#             {
#                 "data": [{"title": "test", "text": "my", "motion_amendment": "1"}],
#                 "meeting_id": 42,
#             },
#         )
#         response = self.request(
#             "motion.import",
#             {"id": json_upload_response.json["results"][0][0]["id"], "import": True},
#         )
#         self.assert_after_json_upload(
#             response, 42, next_id, {"title": "test", "text": "<p>my</p>"}
#         )

#     def test_import_update_with_json_upload_format_1(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id(
#             is_reason_required=True
#         )
#         json_upload_response = self.request(
#             "motion.json_upload",
#             {
#                 "data": [
#                     {
#                         "number": "NUM01",
#                         "title": "test",
#                         "text": "my",
#                         "reason": "stuff",
#                         "motion_amendment": "1",
#                     }
#                 ],
#                 "meeting_id": 42,
#             },
#         )
#         response = self.request(
#             "motion.import",
#             {"id": json_upload_response.json["results"][0][0]["id"], "import": True},
#         )
#         self.assert_after_json_upload(
#             response,
#             42,
#             101,
#             {
#                 "number": "NUM01",
#                 "title": "test",
#                 "text": "<p>my</p>",
#                 "reason": "stuff",
#             },
#         )

#     def test_import_create_with_json_upload_format_2(self) -> None:
#         next_id = self.set_up_models_with_import_previews_and_get_next_motion_id(
#             is_set_number=True
#         )
#         json_upload_response = self.request(
#             "motion.json_upload",
#             {
#                 "data": [
#                     {
#                         "title": "test",
#                         "text": "my",
#                         "number": "",
#                         "reason": "",
#                         "submitters_verbose": self.knights[:3],
#                         "submitters_username": [
#                             "firstMeeting",
#                             "firstMeetingSupporter",
#                             "firstMeetingBoth",
#                             "multiMeeting",
#                         ],
#                         "supporters_verbose": self.knights[3],
#                         "supporters_username": "firstMeetingSubmitter",
#                         "category_name": "Copygory",
#                         "category_prefix": "KOPIE",
#                         "tags": "Tag-liatelle",
#                         "block": "Blockolade",
#                     }
#                 ],
#                 "meeting_id": 42,
#             },
#         )
#         response = self.request(
#             "motion.import",
#             {"id": json_upload_response.json["results"][0][0]["id"], "import": True},
#         )
#         self.assert_after_json_upload(
#             response,
#             42,
#             next_id,
#             {
#                 "title": "test",
#                 "text": "<p>my</p>",
#                 "category_id": 405,
#                 "tag_ids": [10000],
#                 "block_id": 1000,
#             },
#             [3, 6, 7, 12],
#             [4],
#         )

#     def test_import_update_with_json_upload_format_2(self) -> None:
#         self.set_up_models_with_import_previews_and_get_next_motion_id()
#         json_upload_response = self.request(
#             "motion.json_upload",
#             {
#                 "data": [
#                     {
#                         "number": "NUM01",
#                         "title": "test",
#                         "text": "my",
#                         "reason": "stuff",
#                         "submitters_verbose": "",
#                         "submitters_username": "",
#                         "supporters_verbose": "",
#                         "supporters_username": "",
#                         "category_name": "",
#                         "category_prefix": "",
#                         "tags": "",
#                         "block": "",
#                     }
#                 ],
#                 "meeting_id": 42,
#             },
#         )
#         response = self.request(
#             "motion.import",
#             {"id": json_upload_response.json["results"][0][0]["id"], "import": True},
#         )
#         self.assert_after_json_upload(
#             response,
#             42,
#             101,
#             {
#                 "number": "NUM01",
#                 "title": "test",
#                 "text": "<p>my</p>",
#                 "reason": "stuff",
#             },
#         )
