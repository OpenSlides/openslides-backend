DATASTORE_BASE_URL = "/internal/datastore/"


def unify_urls(*parts):
    return "/" + "/".join(p.strip("/") for p in parts)


def build_url_prefix(module):
    return unify_urls(DATASTORE_BASE_URL, module)
