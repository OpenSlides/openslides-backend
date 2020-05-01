from typing import Any, Dict

from .base import Presenter
from .presenter import register_presenter


@register_presenter("initial-data")
class InitialData(Presenter):
    """
    Initial data for setup
    """

    @property
    def data(self) -> Dict[Any, Any]:
        return {
            "privacy_policy": "The PP",
            "legal_notice": "The LN",
            "theme": "openslides-default",
            "logo_web_header_path": None,
            "login_info_text": None,
            "saml_settings": None,
        }
