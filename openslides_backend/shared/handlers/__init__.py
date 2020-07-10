from ..interfaces import LoggingModule, Services


class Base:
    """
    Base class for handlers
    """

    def __init__(self, services: Services, logging: LoggingModule) -> None:
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)
        self.permission = self.services.permission()
        self.database = self.services.datastore()
