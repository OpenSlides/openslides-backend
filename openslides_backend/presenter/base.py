from typing import Any

presenters = {}


def register_presenter(name: str) -> Any:
    """Decoratorfunction
       @register_presenter is used for
       automagic adding presenters to the registry (presenters)
    Arguments:
        name {string} -- registry the decorated class
    """

    def wrapper(clazz: object) -> object:
        """Wrapper / inner function of decorator

        Arguments:
            clazz {object} -- The actual decorated class

        Returns:
            [object] -- The decorated class
        """
        presenters[name] = clazz
        return clazz

    return wrapper


class PresenterBase:
    """Baseclass for Presenters
    """

    pass
