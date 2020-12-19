from ..interfaces.logging import LoggingModule
from ..interfaces.services import Services


class BaseHandler:
    """
    Base class for handlers
    """

    def __init__(self, services: Services, logging: LoggingModule) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

        # Now initialize datastore instance.
        self.datastore = services.datastore()
