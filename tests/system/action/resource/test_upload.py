import base64

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class ResourceUploadActionTest(BaseActionTestCase):
    def test_upload_and_create(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        filename = "test_picture.jpg"
        used_mimetype = "image/jpeg"
        token = "mytoken"
        raw_content = b"test_the_picture"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": filename,
                "file": file_content,
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organization/1",
            {
                "resource_ids": [
                    1,
                ]
            },
        )
        self.assert_model_exists(
            "resource/1",
            {
                "organization_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content),
                "token": token,
            },
        )
        self.media.upload_resource.assert_called_with(file_content, 1, used_mimetype)

    def test_upload_and_update(self) -> None:
        token = "mytoken"
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "resource_ids": [
                        1,
                    ],
                },
                "resource/1": {
                    "organization_id": 1,
                    "token": token,
                    "filesize": 2345,
                    "mimetype": "image/png",
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )

        filename = "test_picture.jpg"
        used_mimetype = "image/jpeg"
        raw_content = b"test_the_picture"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": filename,
                "file": file_content,
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted("resource/1")
        self.assert_model_exists(
            "resource/2",
            {
                "organization_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content),
                "token": token,
            },
        )
        self.assert_model_exists(
            "organization/1",
            {
                "resource_ids": [
                    2,
                ]
            },
        )

        self.media.upload_resource.assert_called_with(file_content, 2, used_mimetype)

    def test_upload_and_mixed_sep_actions(self) -> None:
        """
        Test of 2 uploads with separat actions, first on existing,
        second on not existing model instance
        """
        token1 = "t1"
        token2 = "t2"
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "resource_ids": [
                        1,
                    ],
                },
                "resource/1": {
                    "organization_id": 1,
                    "token": token1,
                    "filesize": 2345,
                    "mimetype": "image/png",
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )

        used_mimetype = "image/jpeg"
        filename1 = "test_picture1.jpg"
        raw_content1 = b"pic1"
        file_content1 = base64.b64encode(raw_content1).decode()
        filename2 = "test_picture2.jpg"
        raw_content2 = b"test_the_picture2"
        file_content2 = base64.b64encode(raw_content2).decode()

        response = self.request_json(
            [
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organization_id": 1,
                            "token": token1,
                            "filename": filename1,
                            "file": file_content1,
                        }
                    ],
                },
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organization_id": 1,
                            "token": token2,
                            "filename": filename2,
                            "file": file_content2,
                        }
                    ],
                },
            ]
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. The following locks were broken: 'organization/1/resource_ids', 'resource/1', 'resource/1/organization_id', 'resource/organization_id', 'resource/token'",
            response.json["message"],
        )
        self.assert_model_exists("organization/1", {"resource_ids": [1]})
        self.assert_model_exists("resource/1", {"meta_deleted": False, "token": token1})
        self.assert_model_not_exists("resource/2")
        self.assert_model_not_exists("resource/3")

        # TODO: When the retry-problem (issue440) is solved, the 7 has to be substituted with a 3
        self.media.upload_resource.assert_called_with(file_content2, 7, used_mimetype)

    def test_upload_and_mixed_one_action(self) -> None:
        """
        Test of 2 uploads within 1 action, first on existing,
        second on not existing model instance
        """
        token1 = "t1"
        token2 = "t2"
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "resource_ids": [
                        1,
                    ],
                },
                "resource/1": {
                    "organization_id": 1,
                    "token": token1,
                    "filesize": 2345,
                    "mimetype": "image/png",
                },
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )

        used_mimetype = "image/jpeg"
        filename1 = "test_picture1.jpg"
        raw_content1 = b"pic1"
        file_content1 = base64.b64encode(raw_content1).decode()
        filename2 = "test_picture2.jpg"
        raw_content2 = b"test_the_picture2"
        file_content2 = base64.b64encode(raw_content2).decode()

        response = self.request_multi(
            "resource.upload",
            [
                {
                    "organization_id": 1,
                    "token": token1,
                    "filename": filename1,
                    "file": file_content1,
                },
                {
                    "organization_id": 1,
                    "token": token2,
                    "filename": filename2,
                    "file": file_content2,
                },
            ],
        )

        self.assert_status_code(response, 200)
        organization = self.get_model("organization/1")
        self.assertCountEqual(organization["resource_ids"], [2, 3])
        self.assert_model_deleted("resource/1")
        self.assert_model_exists(
            "resource/2",
            {
                "organization_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content1),
                "token": token1,
            },
        )
        self.assert_model_exists(
            "resource/3",
            {
                "organization_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content2),
                "token": token2,
            },
        )

        self.media.upload_resource.assert_called_with(file_content2, 3, used_mimetype)

    def test_error_in_resource_upload(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        filename = "raises_upload_error.swf"
        used_mimetype = "application/x-shockwave-flash"
        token = "mytoken"
        raw_content = b"raising upload error in mock"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": filename,
                "file": file_content,
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn("Mocked error on media service upload", response.json["message"])
        self.assert_model_not_exists("resource/1")
        self.media.upload_resource.assert_called_with(file_content, 1, used_mimetype)

    def test_create_cannot_guess_mimetype(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        token = "mytoken"
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": "test.no_guilty_mimetype",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot guess mimetype for test.no_guilty_mimetype",
            response.json["message"],
        )
        self.assert_model_not_exists("resource/1")
        self.media.upload_resource.assert_not_called()

    def test_error_token_used_twice_in_a_request(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        token = "mytoken"
        response = self.request_multi(
            "resource.upload",
            [
                {
                    "organization_id": 1,
                    "token": token,
                    "filename": "test1.jpg",
                    "file": file_content,
                },
                {
                    "organization_id": 1,
                    "token": token,
                    "filename": "test2.jpg",
                    "file": file_content,
                },
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "It is not permitted to use the same token twice in a request.",
            response.json["message"],
        )
        self.assert_model_not_exists("resource/1")
        self.assert_model_not_exists("resource/2")
        self.media.upload_resource.assert_not_called()

    def test_error_token_used_in_a_request(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
                },
            }
        )
        token = "mytoken"
        self.set_models(
            {
                "resource/1": {
                    "organization_id": 1,
                    "token": token,
                    "filesize": 11,
                    "mimetype": "image/png",
                },
                "resource/2": {
                    "organization_id": 1,
                    "token": token,
                    "filesize": 22,
                    "mimetype": "image/png",
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": "test1.jpg",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f'Database corrupt: The resource token has to be unique, but there are 2 tokens "{token}".',
            response.json["message"],
        )
        self.assert_model_exists("resource/1")
        self.assert_model_exists("resource/2")
        self.media.upload_resource.assert_not_called()

    def test_upload_no_permissions(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
            }
        )
        filename = "test_picture.jpg"
        token = "mytoken"
        raw_content = b"test_the_picture"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "resource.upload",
            {
                "organization_id": 1,
                "token": token,
                "filename": filename,
                "file": file_content,
            },
        )

        self.assert_status_code(response, 403)
