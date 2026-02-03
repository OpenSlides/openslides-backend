from dataclasses import dataclass


@dataclass
class RedirectResponse:
    """
    Represents an HTTP redirect response with optional cookies and headers.
    Used for OIDC provisioning flow to redirect after session creation.
    """

    location: str
    access_token: str | None = None
    refresh_cookie: str | None = None
    status_code: int = 302
