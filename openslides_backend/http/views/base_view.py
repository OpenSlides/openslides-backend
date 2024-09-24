import inspect
import re
from collections.abc import Callable
from re import Pattern
from typing import Any, Optional

from os_authlib import AUTHENTICATION_HEADER, COOKIE_NAME
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest

from ...shared.exceptions import View400Exception
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.services import Services
from ...shared.interfaces.wsgi import Headers, ResponseBody, RouteResponse, View
from ...shared.otel import make_span
from ..http_exceptions import MethodNotAllowed, NotFound
from ..request import Request

ROUTE_OPTIONS_ATTR = "__route_options"

RouteFunction = Callable[[Any, Request], tuple[ResponseBody, Optional[str]]]


def route(
    name: str | list[str],
    internal: bool = False,
    method: str = "POST",
    json: bool = True,
) -> Callable[[RouteFunction], RouteFunction]:
    route_options_list = []
    if isinstance(name, str):
        name = [name]
    for _name in name:
        route_parts: list[str] = [""]
        if internal:
            route_parts.append("internal")
        else:
            # extract the callers name to deduce the path's prefix
            frame = inspect.currentframe()
            assert frame and frame.f_back
            caller = inspect.getframeinfo(frame.f_back)[2]
            prefix = caller.replace("View", "").lower()
            route_parts.extend(["system", prefix])
        route_parts.append(_name.strip("/"))
        path = "/".join(route_parts)
        regex = re.compile("^" + path + "/?$")
        route_options = {
            "raw_path": path,
            "path": regex,
            "method": method,
            "json": json,
        }
        route_options_list.append(route_options)

    def wrapper(func: RouteFunction) -> RouteFunction:
        setattr(func, ROUTE_OPTIONS_ATTR, route_options_list)
        return func

    return wrapper


class BaseView(View):
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    routes: dict[Pattern, Callable[[Request], RouteResponse]]

    def __init__(self, env: Env, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.env = env
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.routes = {}

    def get_user_id_from_headers(
        self, headers: Headers, cookies: dict
    ) -> tuple[int, str | None]:
        """
        Returns user id from authentication service using HTTP headers.
        """
        self.services.authentication().set_authentication(
            headers.get(AUTHENTICATION_HEADER, ""), cookies.get(COOKIE_NAME, "")
        )
        user_id, access_token = self.services.authentication().authenticate()
        self.logger.debug(f"User id is {user_id}.")
        return user_id, access_token

    def dispatch(self, request: Request) -> RouteResponse:
        functions = inspect.getmembers(
            self,
            predicate=lambda attr: inspect.ismethod(attr)
            and hasattr(attr, ROUTE_OPTIONS_ATTR),
        )
        with make_span(self.env, "base view"):
            for _, func in functions:
                route_options_list = getattr(func, ROUTE_OPTIONS_ATTR)
                for route_options in route_options_list:
                    if route_options["path"].match(request.environ["RAW_URI"]):
                        # Check request method
                        if request.method != route_options["method"]:
                            raise MethodNotAllowed(
                                valid_methods=[route_options["method"]]
                            )
                        self.logger.debug(f"Request method is {request.method}.")

                        if route_options["json"]:
                            # Check mimetype and parse JSON body. The result is cached in request.json
                            if not request.is_json:
                                raise View400Exception(
                                    "Wrong media type. Use 'Content-Type: application/json' instead."
                                )
                            try:
                                request_body = request.get_json()
                            except WerkzeugBadRequest as exception:
                                raise View400Exception(exception.description)
                            self.logger.debug(f"Request contains JSON: {request_body}.")

                        return func(request)
            raise NotFound()
