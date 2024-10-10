from authlib.jose import JWTClaims

class AuthContext:
    user_id: int
    access_token: str
    claims: JWTClaims

    def __init__(self, user_id: int, access_token: str, claims: JWTClaims):
        self.user_id = user_id
        self.access_token = access_token
        self.claims = claims