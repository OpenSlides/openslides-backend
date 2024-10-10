import threading

import requests
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc9068 import JWTBearerTokenValidator
from authlib.oidc.discovery import OpenIDProviderMetadata, get_well_known_url
from werkzeug.exceptions import Unauthorized, Forbidden
from ..token_storage import token_storage

KEYCLOAK_DOMAIN = 'http://keycloak:8080'
KEYCLOAK_REALM = 'os'
ISSUER = f"{KEYCLOAK_DOMAIN}/realms/{KEYCLOAK_REALM}"

class MyBearerTokenValidator(JWTBearerTokenValidator):
    # Cache the JWKS keys to avoid fetching them repeatedly
    jwk_set = None

    def get_jwks(self):
        if self.jwk_set is None:
            oidc_configuration = OpenIDProviderMetadata(requests.get(get_well_known_url(ISSUER, True)).json())
            response = requests.get(oidc_configuration.get('jwks_uri'))
            response.raise_for_status()
            jwks_keys = response.json()
            self.jwk_set = JsonWebKey.import_key_set(jwks_keys)
        return self.jwk_set

    # def verify_token(self, token):
    #     try:
    #         claims = jwt.decode(token, key=self.get_jwks_key_set())
    #         claims.validate()
    #         return claims
    #     except Exception as e:
    #         return None

def token_required(f):
    def decorated_function(view, request, *args, **kwargs):
        auth_header = request.headers.get('Authentication')
        if not auth_header:
            raise Unauthorized('missing token')

        token = auth_header.split(" ")[1]
        validator = MyBearerTokenValidator(ISSUER, 'https://localhost:8000/system')
        claims = validator.authenticate_token(token)

        if not claims:
            raise Forbidden('missing or invalid token')

        view.logger.debug(f"Saving Token claims to thread: {threading.get_ident()}")

        token_storage.claims = claims
        token_storage.access_token = token

        return f(view, request, claims, *args, **kwargs)
    return decorated_function
