import copy
import os
from typing import Any, Dict, Type
from unittest.mock import MagicMock, Mock

from dependency_injector import providers
from requests.models import Response as RequestsResponse

from openslides_backend.http.views import ActionView, PresenterView
from openslides_backend.http.views.base_view import ROUTE_OPTIONS_ATTR, RouteFunction
from openslides_backend.services.media.interface import MediaService
from openslides_backend.services.vote.adapter import VoteAdapter
from openslides_backend.services.vote.interface import VoteService
from openslides_backend.shared.env import Environment
from openslides_backend.shared.exceptions import MediaServiceException
from openslides_backend.shared.interfaces.wsgi import Headers, View, WSGIApplication
from openslides_backend.wsgi import OpenSlidesBackendServices, OpenSlidesBackendWSGI
from tests.util import Response


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

    def vote(self, data: Dict[str, Any]) -> Response:
        ...


class TestVoteAdapter(VoteAdapter, TestVoteService):
    def vote(self, data: Dict[str, Any]) -> Response:
        data_copy = copy.deepcopy(data)
        del data_copy["id"]
        response = self.make_request(
            self.url.replace("internal", "system") + f"?id={data['id']}",
            data_copy,
        )
        return convert_to_test_response(response)


def create_action_test_application() -> WSGIApplication:
    return create_test_application(ActionView)


def create_presenter_test_application() -> WSGIApplication:
    return create_test_application(PresenterView)


def create_test_application(view: Type[View]) -> WSGIApplication:
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
    if mimetype == "application/x-shockwave-flash":
        raise MediaServiceException("Mocked error on media service upload")


def get_route_path(route_function: RouteFunction, name: str = "") -> str:
    route_options_list = getattr(route_function, ROUTE_OPTIONS_ATTR)
    for route_options in route_options_list:
        if route_options["raw_path"].endswith(name):
            return route_options["raw_path"]
    raise ValueError(f"Route {name} does not exist")
