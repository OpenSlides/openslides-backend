from authlib.jose import JWTClaims
from werkzeug.local import Local
from typing import Optional, TypedDict


class TokenStorageUpdate(TypedDict, total=False):
    access_token: Optional[str]
    claims: Optional[JWTClaims]

class TokenStorage(Local):
    access_token: Optional[str]
    claims: Optional[JWTClaims]

    def update(self, data: TokenStorageUpdate) -> None:
        if 'access_token' in data:
            self.access_token = data['access_token']
        if 'claims' in data:
            self.claims = data['claims']

    def clear(self) -> None:
        self.access_token = None
        self.claims = None

token_storage = TokenStorage()