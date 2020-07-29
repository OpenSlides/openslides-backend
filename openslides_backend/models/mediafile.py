from ..shared.patterns import Collection
from .base import Model


class Mediafile(Model):
    """
    Model for mediafiles.

    There are the following reverse relation fields: TODO
    """

    collection = Collection("mediafile")
    verbose_name = "mediafile"

    # TODO: add fields
