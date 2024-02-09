import base64
import copy
import cProfile
import os
from abc import abstractmethod
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from dependency_injector import providers
from requests.models import Response as RequestsResponse

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.http.views import ActionView, PresenterView
from openslides_backend.http.views.base_view import ROUTE_OPTIONS_ATTR, RouteFunction
from openslides_backend.models.models import Poll
from openslides_backend.services.datastore.adapter import DatastoreAdapter
from openslides_backend.services.datastore.interface import DatastoreService
from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from openslides_backend.services.media.interface import MediaService
from openslides_backend.services.vote.adapter import VoteAdapter
from openslides_backend.services.vote.interface import VoteService
from openslides_backend.shared.env import Environment, is_truthy
from openslides_backend.shared.exceptions import ActionException, MediaServiceException
from openslides_backend.shared.interfaces.wsgi import Headers, View, WSGIApplication
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.wsgi import OpenSlidesBackendServices, OpenSlidesBackendWSGI
from tests.util import Response

with open("public_vote_main_key", "rb") as keyfile:
    PUBLIC_MAIN_KEY = keyfile.read()


def convert_to_test_response(response: RequestsResponse) -> Response:
    """Helper function to convert a requests Response to a TestResponse."""
    return Response(
        response.iter_content(),
        str(response.status_code),
        Headers({**dict(response.headers), "Content-Type": "application/json"}),
        MagicMock(),
    )


class TestVoteService(VoteService):
    url: str
    datastore: DatastoreService

    @abstractmethod
    def vote(self, data: dict[str, Any]) -> Response: ...


class TestVoteAdapter(VoteAdapter, TestVoteService):
    @with_database_context
    def vote(self, data: dict[str, Any]) -> Response:
        data_copy = copy.deepcopy(data)
        poll = self.datastore.get(
            fqid_from_collection_and_id("poll", data["id"]),
            mapped_fields=["type", "crypt_key", "crypt_signature", "state"],
            lock_result=False,
        )
        if poll["state"] != Poll.STATE_STARTED:
            raise ActionException("Backendtest: Poll not started!")
        del data_copy["id"]
        if poll["type"] == Poll.TYPE_CRYPTOGRAPHIC:
            crypt_key = base64.b64decode(poll.get("crypt_key", ""))
            crypt_signature = base64.b64decode(poll.get("crypt_signature", ""))
            self.encrypt_votes(data_copy, crypt_key, crypt_signature)
        response = self.make_request(
            self.url.replace("internal", "system") + f"?id={data['id']}",
            data_copy,
        )
        return convert_to_test_response(response)

    def encrypt_votes(
        self, data: dict[str, Any], crypt_key: bytes, crypt_signature: bytes
    ) -> None:
        pubKeySize = 32
        nonceSize = 12
        public_main_key = ed25519.Ed25519PublicKey.from_public_bytes(PUBLIC_MAIN_KEY)
        public_main_key.verify(crypt_signature, crypt_key)

        private_key = x25519.X25519PrivateKey.generate()
        public_private_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        public_poll_key = x25519.X25519PublicKey.from_public_bytes(crypt_key)
        shared_key = private_key.exchange(public_poll_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=pubKeySize,
            salt=None,
            info=None,
        ).derive(shared_key)
        nonce = os.urandom(nonceSize)
        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        value_string = str(data.get("value")).replace("'", '"')
        user_token = get_random_string(8)
        encrypt_string = bytes(
            f'{{"votes":{value_string},"token":"{user_token}"}}', encoding="utf-8"
        )
        encrypted = encryptor.update(encrypt_string)
        encryptor.finalize()
        encrypted += encryptor.tag
        base64_encoded = base64.encodebytes(
            b"".join([public_private_key, nonce, encrypted])
        )
        data["value"] = base64_encoded


def create_action_test_application() -> WSGIApplication:
    return create_test_application(ActionView)


def create_presenter_test_application() -> WSGIApplication:
    return create_test_application(PresenterView)


def create_test_application(view: type[View]) -> WSGIApplication:
    env = Environment(os.environ)
    services = OpenSlidesBackendServices(
        config=env.get_service_url(),
        logging=MagicMock(),
    )
    services.vote = providers.Singleton(
        TestVoteAdapter, services.config.vote_url, MagicMock()
    )
    mock_media_service = Mock(MediaService)
    mock_media_service.upload_mediafile = Mock(
        side_effect=side_effect_for_upload_method
    )
    mock_media_service.upload_resource = Mock(side_effect=side_effect_for_upload_method)
    services.media = MagicMock(return_value=mock_media_service)

    # Create WSGI application instance. Inject logging module, view class and services container.
    application_factory = OpenSlidesBackendWSGI(
        env=env, logging=MagicMock(), view=view, services=services
    )
    application = application_factory.setup()

    return application


def side_effect_for_upload_method(
    file: str, id: int, mimetype: str, **kwargs: Any
) -> None:
    # Check against encoded version of "Do me a favour and trigger a mock mediaservice error, will you?"
    if (
        file
        == "RG8gbWUgYSBmYXZvdXIgYW5kIHRyaWdnZXIgYSBtb2NrIG1lZGlhc2VydmljZSBlcnJvciwgd2lsbCB5b3U/"
    ):
        raise MediaServiceException("Mocked error on media service upload")


def get_route_path(route_function: RouteFunction, name: str = "") -> str:
    route_options_list = getattr(route_function, ROUTE_OPTIONS_ATTR)
    for route_options in route_options_list:
        if route_options["raw_path"].endswith(name):
            return route_options["raw_path"]
    raise ValueError(f"Route {name} does not exist")


def mock_datastore_method(method: str, verbose: bool = False) -> tuple[Mock, Any]:
    """
    Patches the given method of the DatastoreAdapter and returns the created mock as well as the
    patcher.
    """
    orig_method = getattr(DatastoreAdapter, method)

    def mock_method(inner_self: DatastoreAdapter, *args: Any, **kwargs: Any) -> Any:
        if verbose:
            print(orig_method.__name__, args, kwargs)
        return orig_method(inner_self, *args, **kwargs)

    patcher = patch.object(DatastoreAdapter, method, autospec=True)
    mock = patcher.start()
    mock.side_effect = mock_method
    return mock, patcher


def disable_dev_mode(fn: Callable) -> Callable:
    return patch(
        "openslides_backend.shared.env.Environment.is_dev_mode",
        MagicMock(return_value=False),
    )(fn)


def performance(func: Callable) -> Callable:
    return pytest.mark.skipif(
        not is_truthy(os.environ.get("OPENSLIDES_PERFORMANCE_TESTS", "")),
        reason="Performance tests are disabled.",
    )(func)


class Profiler:
    """
    Helper class to profile a block of code. Use as context manager and provide filename to save the
    output to.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def __enter__(self) -> None:
        self.profiler = cProfile.Profile()
        self.profiler.enable()

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self.profiler.disable()
        self.profiler.dump_stats(self.filename)


class CountDatastoreCalls:
    """
    Helper class to track the amount of datastore calls (= cache misses). Use as context manager and
    access the result via the `count` property.
    """

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def __enter__(self) -> "CountDatastoreCalls":
        self.patcher: list[Any] = []
        self.mocks: list[Mock] = []
        for method in ("get", "get_many"):
            mock, patcher = mock_datastore_method(method, self.verbose)
            self.mocks.append(mock)
            self.patcher.append(patcher)
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        for patcher in self.patcher:
            patcher.stop()

    @property
    def calls(self) -> int:
        return sum(mock.call_count for mock in self.mocks)


def remove_files_from_vote_decrypt_service() -> None:
    path = "tests/system/action/poll/vote_decrypt_clear_data"
    files = os.listdir(path)
    for file in files:
        os.remove(os.path.join(path, file))
