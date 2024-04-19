from unittest.mock import MagicMock

from openslides_backend.datastore.reader.flask_frontend.routes import Route
from openslides_backend.datastore.reader.flask_frontend.routes_handler import (
    register_routes,
)


def test_register_routes():
    app = MagicMock()

    register_routes(app, "prefix")

    # `call` objects are tuples in the fashion of (args, kwargs)
    routes = [call[0][1] for call in app.add_url_rule.call_args_list]
    assert routes == list(Route) + ["health"]
