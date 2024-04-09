from openslides_backend.datastore.shared.flask_frontend import (
    build_url_prefix,
    unify_urls,
)

URL_PREFIX = build_url_prefix("writer")


WRITE_URL = unify_urls(URL_PREFIX, "/write")
RESERVE_IDS_URL = unify_urls(URL_PREFIX, "/reserve_ids")
DELETE_HISTORY_INFORMATION_URL = unify_urls(URL_PREFIX, "/delete_history_information")
TRUNCATE_DB_URL = unify_urls(URL_PREFIX, "/truncate_db")
WRITE_WITHOUT_EVENTS_URL = unify_urls(URL_PREFIX, "/write_without_events")
