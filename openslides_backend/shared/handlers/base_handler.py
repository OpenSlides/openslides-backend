from ..interfaces.env import Env
from ..interfaces.logging import LoggingModule
from ..interfaces.services import Services


class BaseHandler:
    """
    Base class for handlers
    """

    def __init__(self, env: Env, services: Services, logging: LoggingModule) -> None:
        self.env = env
        self.services = services
        self.logging = logging
        self.logger = logging.getLogger(__name__)

        # Now initialize datastore instance.
        self.datastore = services.datastore()
        # self.extended_db = ExtendedDatabase(self.logging, self.env)
        # self.database = services.database()
