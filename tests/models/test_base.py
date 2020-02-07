from unittest import TestCase

from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.patterns import Collection


class FakeModel(Model):
    """
    Fake Model for testing purposes.
    """

    collection = Collection("fake_model")
    verbose_name = "fake_model"

    id = fields.IdField(description="The id of this fake model.")
    text = fields.RequiredCharField(description="The text of this fake model.")


class ActionsBaseTester(TestCase):
    """
    Tests methods of base Action class and also some helper functions.
    """

    def setUp(self) -> None:
        pass

    def test_get_properties(self) -> None:
        expected = {
            "id": {
                "description": "The id of this fake model.",
                "type": "integer",
                "minimum": 1,
            },
            "text": {
                "description": "The text of this fake model.",
                "type": "string",
                "minLength": 1,
                "maxLength": 256,
            },
        }
        self.assertEqual(FakeModel().get_properties("id", "text"), expected)

    def test_get_properties_invalid(self) -> None:
        with self.assertRaises(TypeError) as context_manager:
            FakeModel().get_properties("unknown_property")
        self.assertEqual(
            context_manager.exception.args[0],
            "unknown_property is not a field of fake_model",
        )
