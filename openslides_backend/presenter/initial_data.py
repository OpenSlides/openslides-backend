from typing import Any

from .base import BasePresenter
from .presenter import register_presenter


@register_presenter("initial-data")
class InitialData(BasePresenter):
    """
    Initial data for setup
    """

    def get_result(self) -> Any:
        return {
            "privacy_policy": "The PP",
            "legal_notice": "The LN",
            "theme": "openslides-default",
            "logo_web_header_path": None,
            "login_info_text": None,
            "saml_settings": None,
        }
