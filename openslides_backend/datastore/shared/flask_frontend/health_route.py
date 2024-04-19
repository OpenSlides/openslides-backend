from ..di import injector
from ..services import ReadDatabase
from .errors import handle_internal_errors
from .urls import unify_urls


@handle_internal_errors
def health():
    read_database = injector.get(ReadDatabase)
    with read_database.get_context():
        read_database.get_current_migration_index()
    return "", 200


def get_health_url(url_prefix):
    return unify_urls(url_prefix, "health")


def add_health_route(app, url_prefix):
    app.add_url_rule(
        get_health_url(url_prefix),
        "health",
        health,
        methods=["GET"],
        strict_slashes=False,
    )
