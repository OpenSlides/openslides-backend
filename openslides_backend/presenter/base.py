from typing import Any, Dict


class PresenterBase:  # pragma: no cover
    """
    Abstract base class for presenters.
    """

    @property
    def data(self) -> Dict[Any, Any]:
        ...


class Presenter(PresenterBase):
    """
    Base clase for presenters.
    """

    pass
