import inspect
import re
from typing import Any, Callable, Dict, Optional, Pattern, Tuple

from werkzeug.exceptions import BadRequest as WerkzeugBadRequest
from werkzeug.exceptions import NotFound

from ...shared.exceptions import View400Exception
from ...shared.interfaces.logging import LoggingModule
from ...shared.interfaces.services import Services
from ...shared.interfaces.wsgi import Headers, ResponseBody, View
from ..http_exceptions import MethodNotAllowed
from ..request import Request

ROUTE_OPTIONS_ATTR = "__route_options"

RouteFunction = Callable[[Any, Request], Tuple[ResponseBody, Optional[str]]]


def route(
    name: str, internal: bool = False, method: str = "POST", json: bool = True
) -> Callable[[RouteFunction], RouteFunction]:
    # extract the callers name to deduce the path's prefix
    frame = inspect.currentframe()
    assert frame and frame.f_back
    caller = inspect.getframeinfo(frame.f_back)[2]
    prefix = caller.replace("View", "").lower()

    def wrapper(func: RouteFunction) -> RouteFunction:
        path = prefix + "/" + name.strip("/")
        if internal:
            path = "/internal/" + path
        else:
            path = "/system/" + path
        regex = re.compile("^" + path + "/?$")
        route_options = {
            "raw_path": path,
            "path": regex,
            "method": method,
            "json": json,
        }
        setattr(func, ROUTE_OPTIONS_ATTR, route_options)
        return func

    return wrapper


class BaseView(View):
    """
    Base class for views of this service.

    During initialization we bind the dependencies to the instance.
    """

    routes: Dict[Pattern, Callable[[Request], Tuple[ResponseBody, Optional[str]]]]

    def __init__(self, logging: LoggingModule, services: Services) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.routes = {}

    def get_user_id_from_headers(
        self, headers: Headers, cookies: Dict
    ) -> Tuple[int, Optional[str]]:
        """
        Returns user id from authentication service using HTTP headers.
        """
        user_id, access_token = self.services.authentication().authenticate(
            headers, cookies
        )
        self.logger.debug(f"User id is {user_id}.")
        return user_id, access_token

    def dispatch(self, request: Request) -> Tuple[ResponseBody, Optional[str]]:
        functions = inspect.getmembers(
            self,
            predicate=lambda attr: inspect.ismethod(attr)
            and hasattr(attr, ROUTE_OPTIONS_ATTR),
        )
        for _, func in functions:
            route_options = getattr(func, ROUTE_OPTIONS_ATTR)
            if route_options["path"].match(request.environ["RAW_URI"]):
                # Check request method
                if request.method != route_options["method"]:
                    raise MethodNotAllowed(valid_methods=[route_options["method"]])
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
