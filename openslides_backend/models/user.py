from ..shared.patterns import Collection
from . import fields
from .base import Model


class User(Model):
    """
    Model for users.

    There are the following reverse relation fields:
        TODO
    """

    # TODO: Add reverse relation fields to docstring.

    collection = Collection("user")
    verbose_name = "user"

    id = fields.IdField(description="The id of this user.")

    # TODO: Add all fields.
