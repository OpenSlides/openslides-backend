from enum import Enum as BaseEnum


class Enum(BaseEnum):
    """
    Needed base class since for some reason, python switches up the meaning of repr() and str() for enums: Normally,
    str() provides a human-readable representation of the object, while repr() provides the exact string that can be
    injected into eval() to recreate this object. For enums, this behaviour is exactly switched. Thanks for nothing.
    """

    def __str__(self) -> str:
        return super().__repr__()

    def __repr__(self) -> str:
        return super().__str__()
