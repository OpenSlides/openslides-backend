from typing import Protocol

from ...services.auth.interface import AuthenticationService
from ...services.datastore.interface import DatastoreService
from ...services.media.interface import MediaService
from ...services.vote.interface import VoteService


class Services(Protocol):
    """
    Interface for service container used for dependency injection.
    """

    def authentication(self) -> AuthenticationService: ...

    def datastore(self) -> DatastoreService: ...

    def media(self) -> MediaService: ...

    def vote(self) -> VoteService: ...
