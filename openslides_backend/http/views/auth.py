import threading

import requests
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc9068 import JWTBearerTokenValidator
from authlib.oidc.discovery import OpenIDProviderMetadata, get_well_known_url
from werkzeug.exceptions import Unauthorized, Forbidden

from os_authlib.token_validator import JWTBearerOpenSlidesTokenValidator, create_openslides_token_validator
from ..token_storage import token_storage, TokenStorageUpdate

KEYCLOAK_DOMAIN = 'http://keycloak:8080/idp'
KEYCLOAK_REALM = 'os'
ISSUER = f"{KEYCLOAK_DOMAIN}/realms/{KEYCLOAK_REALM}"
CERTS_URI = f"{KEYCLOAK_DOMAIN}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

def token_required(f):
    def decorated_function(view, request, *args, **kwargs):
        auth_header = request.headers.get('Authentication') or request.headers.get('Authorization')
        if not auth_header:
            raise Unauthorized('missing token')

        token = auth_header.split(" ")[1]
        validator = create_openslides_token_validator()
        claims = validator.authenticate_token(token)

        if not claims:
            raise Forbidden('missing or invalid token')

        view.logger.debug(f"Saving Token claims to thread: {threading.get_ident()}")

        token_storage.update(TokenStorageUpdate(access_token=token, claims=claims))

        return f(view, request, claims, *args, **kwargs)
    return decorated_function
