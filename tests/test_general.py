import os
from unittest import TestCase
from unittest.mock import patch

from openslides_backend.actions.general.patterns import (
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)
from openslides_backend.actions.http.application import Application, create_application

from .fake_adapters.authentication import AuthenticationTestAdapter
from .utils import Client, ResponseWrapper


class WSGIApplicationTester(TestCase):
    """
    Tests the WSGI application in general.
    """

    def setUp(self) -> None:
        self.authentication_patcher = patch(
            "openslides_backend.actions.views.base.AuthenticationHTTPAdapter",
            AuthenticationTestAdapter(0),  # User is anonymous
        )
        self.authentication_patcher.start()
        self.application = create_application()

    def tearDown(self) -> None:
        self.authentication_patcher.stop()

    def test_wsgi_file(self) -> None:
        from openslides_backend.wsgi import application

        self.assertTrue(isinstance(application, Application))

    def test_create_application(self) -> None:
        self.assertTrue(isinstance(self.application, Application))

    def test_create_application_2(self) -> None:
        os.environ["OPENSLIDES_BACKEND_DEBUG"] = "1"
        app = create_application()
        self.assertTrue(isinstance(app, Application))

    def test_wsgi_request_root(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_root_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_fuzzy_path(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/unknown_path")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_fuzzy_path_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/unknown_path")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_correct_path_with_slash(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/system/api/actions/")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_correct_path_with_slash_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/system/api/actions/")
        self.assertEqual(response.status_code, 404)

    def test_wsgi_request_wrong_method(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.get("/system/api/actions")
        self.assertEqual(response.status_code, 405)

    def test_wsgi_request_wrong_media_type(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/system/api/actions")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Wrong media type.", str(response.data))

    def test_wsgi_request_missing_body(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post("/system/api/actions", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to decode JSON object", str(response.data))

    def test_wsgi_request_fuzzy_body(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json={"fuzzy_key_Eeng7pha3a": "fuzzy_value_eez3Ko6quu"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("data must be array", str(response.data))

    def test_wsgi_request_fuzzy_body_2(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"fuzzy_key_Voh8in7aec": "fuzzy_value_phae3iew4W"}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "data[0] must contain [\\'action\\', \\'data\\'] properties",
            str(response.data),
        )

    def test_wsgi_request_no_existing_action(self) -> None:
        client = Client(self.application, ResponseWrapper)
        response = client.post(
            "/system/api/actions",
            json=[{"action": "fuzzy_action_hamzaeNg4a", "data": [{}]}],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Action fuzzy_action_hamzaeNg4a does not exist.", str(response.data)
        )


class TypesTester(TestCase):
    """
    Tests some utils and types
    """

    def test_collection(self) -> None:
        collection = Collection("collection_vi8cah2Eih")
        self.assertEqual(str(collection), "collection_vi8cah2Eih")

    def test_collection_comparing(self) -> None:
        collection_1 = Collection("collection_aeboo3ieSh")
        collection_2 = Collection("collection_aeboo3ieSh")
        self.assertEqual(collection_1, collection_2)

    def test_collection_hashing(self) -> None:
        collection = Collection("collection_Din9chosoo")
        self.assertEqual(hash(collection), hash("collection_Din9chosoo"))

    def test_full_qualified_id(self) -> None:
        fqid = FullQualifiedId(Collection("collection_Aid6ahdooT"), 8283937728)
        self.assertEqual(str(fqid), "collection_Aid6ahdooT/8283937728")

    def test_full_qualified_id_comparing(self) -> None:
        fqid_1 = FullQualifiedId(Collection("collection_reeyie3Woo"), 2133862900)
        fqid_2 = FullQualifiedId(Collection("collection_reeyie3Woo"), 2133862900)
        self.assertEqual(fqid_1, fqid_2)

    def test_full_qualified_id_hashing(self) -> None:
        fqid = FullQualifiedId(Collection("collection_ia5Ooyuiso"), 9638688299)
        self.assertEqual(hash(fqid), hash("collection_ia5Ooyuiso/9638688299"))

    def test_full_qualified_field(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_Shoo1uut4u"), 7208641662, "field_ais1aBau6d"
        )
        self.assertEqual(
            str(fqfield), "collection_Shoo1uut4u/7208641662/field_ais1aBau6d"
        )

    def test_full_qualified_field_comparing(self) -> None:
        fqfield_1 = FullQualifiedField(
            Collection("collection_ioMohcui0u"), 7208641662, "field_epee2jeRee"
        )
        fqfield_2 = FullQualifiedField(
            Collection("collection_ioMohcui0u"), 7208641662, "field_epee2jeRee"
        )
        self.assertEqual(fqfield_1, fqfield_2)

    def test_full_qualified_field_hashing(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_ohf3Thoo9i"), 8432643375, "field_Raechee5ee"
        )
        self.assertEqual(
            hash(fqfield), hash("collection_ohf3Thoo9i/8432643375/field_Raechee5ee")
        )
