import base64

from tests.system.action.base import BaseActionTestCase


class ResourceUploadActionTest(BaseActionTestCase):
    def test_upload_and_create(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        filename = "test_picture.jpg"
        used_mimetype = "image/jpeg"
        token = "mytoken"
        raw_content = b"test_the_picture"
        file_content = base64.b64encode(raw_content).decode()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": filename,
                            "file": file_content,
                        }
                    ],
                }
            ],
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organisation/1",
            {
                "resource_ids": [
                    1,
                ]
            },
        )
        self.assert_model_exists(
            "resource/1",
            {
                "organisation_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content),
                "token": token,
            },
        )
        self.media.upload_resource.assert_called_with(file_content, 1, used_mimetype)

    def test_upload_and_update(self) -> None:
        token = "mytoken"
        self.create_model(
            "organisation/1",
            {
                "name": "test_organisation1",
                "resource_ids": [
                    1,
                ],
            },
        )
        self.create_model(
            "resource/1",
            {
                "organisation_id": 1,
                "token": token,
                "filesize": 2345,
                "mimetype": "image/png",
            },
        )

        filename = "test_picture.jpg"
        used_mimetype = "image/jpeg"
        raw_content = b"test_the_picture"
        file_content = base64.b64encode(raw_content).decode()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": filename,
                            "file": file_content,
                        }
                    ],
                }
            ],
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted("resource/1")
        self.assert_model_exists(
            "resource/2",
            {
                "organisation_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content),
                "token": token,
            },
        )
        self.assert_model_exists(
            "organisation/1",
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
        self.create_model(
            "organisation/1",
            {
                "name": "test_organisation1",
                "resource_ids": [
                    1,
                ],
            },
        )
        self.create_model(
            "resource/1",
            {
                "organisation_id": 1,
                "token": token1,
                "filesize": 2345,
                "mimetype": "image/png",
            },
        )

        used_mimetype = "image/jpeg"
        filename1 = "test_picture1.jpg"
        raw_content1 = b"pic1"
        file_content1 = base64.b64encode(raw_content1).decode()
        filename2 = "test_picture2.jpg"
        raw_content2 = b"test_the_picture2"
        file_content2 = base64.b64encode(raw_content2).decode()

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
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
                            "organisation_id": 1,
                            "token": token2,
                            "filename": filename2,
                            "file": file_content2,
                        }
                    ],
                },
            ],
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model \\'organisation/1\\' raises MODEL_LOCKED error.",
            str(response.data),
        )
        self.assert_model_exists("organisation/1", {"resource_ids": [1]})
        self.assert_model_exists("resource/1", {"meta_deleted": False, "token": token1})
        self.assert_model_not_exists("resource/2")
        self.assert_model_not_exists("resource/3")

        # TODO: When the retry-problem (issue440) is solved, the 9 has to be substituted with a 3
        self.media.upload_resource.assert_called_with(file_content2, 9, used_mimetype)

    def test_upload_and_mixed_one_action(self) -> None:
        """
        Test of 2 uploads within 1 action, first on existing,
        second on not existing model instance
        """
        token1 = "t1"
        token2 = "t2"
        self.create_model(
            "organisation/1",
            {
                "name": "test_organisation1",
                "resource_ids": [
                    1,
                ],
            },
        )
        self.create_model(
            "resource/1",
            {
                "organisation_id": 1,
                "token": token1,
                "filesize": 2345,
                "mimetype": "image/png",
            },
        )

        used_mimetype = "image/jpeg"
        filename1 = "test_picture1.jpg"
        raw_content1 = b"pic1"
        file_content1 = base64.b64encode(raw_content1).decode()
        filename2 = "test_picture2.jpg"
        raw_content2 = b"test_the_picture2"
        file_content2 = base64.b64encode(raw_content2).decode()

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token1,
                            "filename": filename1,
                            "file": file_content1,
                        },
                        {
                            "organisation_id": 1,
                            "token": token2,
                            "filename": filename2,
                            "file": file_content2,
                        },
                    ],
                },
            ],
        )

        self.assert_status_code(response, 200)
        organisation = self.get_model("organisation/1")
        self.assertCountEqual(organisation["resource_ids"], [2, 3])
        self.assert_model_deleted("resource/1")
        self.assert_model_exists(
            "resource/2",
            {
                "organisation_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content1),
                "token": token1,
            },
        )
        self.assert_model_exists(
            "resource/3",
            {
                "organisation_id": 1,
                "mimetype": used_mimetype,
                "filesize": len(raw_content2),
                "token": token2,
            },
        )

        self.media.upload_resource.assert_called_with(file_content2, 3, used_mimetype)

    def test_error_in_resource_upload(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        filename = "raises_upload_error.swf"
        used_mimetype = "application/x-shockwave-flash"
        token = "mytoken"
        raw_content = b"raising upload error in mock"
        file_content = base64.b64encode(raw_content).decode()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": filename,
                            "file": file_content,
                        }
                    ],
                }
            ],
        )

        self.assert_status_code(response, 400)
        self.assertIn("Mocked error on media service upload", str(response.data))
        self.assert_model_not_exists("resource/1")
        self.media.upload_resource.assert_called_with(file_content, 1, used_mimetype)

    def test_create_cannot_guess_mimetype(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        file_content = base64.b64encode(b"testtesttest").decode()
        token = "mytoken"
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": "test.no_guilty_mimetype",
                            "file": file_content,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot guess mimetype for test.no_guilty_mimetype", str(response.data)
        )
        self.assert_model_not_exists("resource/1")
        self.media.upload_resource.assert_not_called()

    def test_error_token_used_twice_in_a_request(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        file_content = base64.b64encode(b"testtesttest").decode()
        token = "mytoken"
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": "test1.jpg",
                            "file": file_content,
                        },
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": "test2.jpg",
                            "file": file_content,
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "It is not permitted to use the same token twice in a request.",
            str(response.data),
        )
        self.assert_model_not_exists("resource/1")
        self.assert_model_not_exists("resource/2")
        self.media.upload_resource.assert_not_called()

    def test_error_token_used_in_a_request(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        token = "mytoken"
        self.create_model(
            "resource/1",
            {
                "organisation_id": 1,
                "token": token,
                "filesize": 11,
                "mimetype": "image/png",
            },
        )
        self.create_model(
            "resource/2",
            {
                "organisation_id": 1,
                "token": token,
                "filesize": 22,
                "mimetype": "image/png",
            },
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "resource.upload",
                    "data": [
                        {
                            "organisation_id": 1,
                            "token": token,
                            "filename": "test1.jpg",
                            "file": file_content,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f'Database corrupt: The resource token has to be unique, but there are 2 tokens \\\\"{token}\\\\".',
            str(response.data),
        )
        self.assert_model_exists("resource/1")
        self.assert_model_exists("resource/2")
        self.media.upload_resource.assert_not_called()
