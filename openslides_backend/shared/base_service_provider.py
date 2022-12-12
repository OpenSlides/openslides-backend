from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.datastore.interface import DatastoreService
from openslides_backend.services.media.interface import MediaService
from openslides_backend.services.vote.interface import VoteService
from openslides_backend.shared.interfaces.logging import Logger, LoggingModule
from openslides_backend.shared.interfaces.services import Services


class BaseServiceProvider:
    """
    Base class for actions and presenters.
    """

    services: Services
    datastore: DatastoreService
    auth: AuthenticationService
    media: MediaService
    vote: VoteService

    logging: LoggingModule
    logger: Logger

    user_id: int

    def __init__(
        self,
        services: Services,
        datastore: DatastoreService,
        logging: LoggingModule,
    ) -> None:
        self.services = services
        self.auth = services.authentication()
        self.media = services.media()
        self.vote_service = services.vote()
        self.datastore = datastore
        self.logging = logging
