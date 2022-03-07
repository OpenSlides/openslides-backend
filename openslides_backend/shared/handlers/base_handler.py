from ..interfaces.config import Config
from ..interfaces.logging import LoggingModule
from ..interfaces.services import Services


class BaseHandler:
    """
    Base class for handlers
    """

    def __init__(
        self, config: Config, services: Services, logging: LoggingModule
    ) -> None:
        self.config = config
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

        # Now initialize datastore instance.
        self.datastore = services.datastore()
