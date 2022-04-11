class VerbosePermission:
    """
    Base class for all kinds of permissions for easier error messages.
    """

    def get_verbose_type(self) -> str:
        return type(self).__name__

    def get_base_model(self) -> str:
        raise NotImplementedError()


class Permission(VerbosePermission):
    """Marker class to use typing with permissions."""

    def get_verbose_type(self) -> str:
        return Permission.__name__

    def get_base_model(self) -> str:
        return "meeting"
