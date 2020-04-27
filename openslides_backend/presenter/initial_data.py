from .base import PresenterBase, register_presenter


@register_presenter("initial-data")
class InitialData(PresenterBase):
    """Initial Data for setup
    """

    @property
    def data(self) -> object:
        return {
            "privacy_policy": "The PP",
            "legal_notice": "The LN",
            "theme": "openslides-default",
            "logo_web_header_path": None,
            "login_info_text": None,
            "saml_settings": None,
        }
