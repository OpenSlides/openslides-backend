from openslides_backend.datastore.shared.flask_frontend import (
    JsonResponse,
    add_health_route,
    get_json_from_request,
    handle_internal_errors,
    unify_urls,
)

from .json_handler import JSONHandler
from .routes import Route


def make_json_response(fn):
    def wrapper(*args, **kwargs):
        response = fn(*args, **kwargs)
        if isinstance(response, tuple) and isinstance(response[0], dict):
            return JsonResponse(response[0]), response[1]
        elif isinstance(response, dict):
            return JsonResponse(response)
        return response

    return wrapper


def get_route(route: Route):
    @make_json_response
    @handle_internal_errors
    def route_func():
        json_handler = JSONHandler()
        return json_handler.handle_request(route, get_json_from_request())

    return route_func


def register_routes(app, url_prefix):
    for route in list(Route):
        url = unify_urls(url_prefix, route)
        app.add_url_rule(
            url,
            route,
            get_route(route),
            methods=["POST"],
            strict_slashes=False,
        )
    add_health_route(app, url_prefix)
