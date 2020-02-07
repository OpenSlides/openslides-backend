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


class FakeModel2(Model):
    """
    Fake model for testing purposes. With relation field.
    """

    collection = Collection("fake_model_2")
    verbose_name = "fake_model_2"

    id = fields.IdField(description="The id of this fake model.")
    relation_field = fields.ForeignKeyField(
        description="The foreign key to fake_model.",
        to=Collection("fake_model"),
        related_name="fake_model_2_ids",
    )


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
        with self.assertRaises(ValueError) as context_manager:
            FakeModel().get_properties("unknown_property")
        self.assertEqual(
            context_manager.exception.args[0],
            "unknown_property is not a field of fake_model",
        )

    def test_get_fields_fake_model(self) -> None:
        self.assertEqual(
            ["id", "text", "fake_model_2_ids"],
            [field_name for field_name, _ in FakeModel().get_fields()],
        )
        self.assertEqual(
            ["id", "text"],
            [field_name for field_name, _ in FakeModel().get_fields(only_generic=True)],
        )

    def test_own_collection_attr(self) -> None:
        reverse_relations = list(FakeModel().get_reverse_relations())
        self.assertEqual(len(reverse_relations), 1)
        field_name, field = reverse_relations[0]
        self.assertEqual(field_name, "fake_model_2_ids")
        self.assertEqual(str(field.own_collection), "fake_model_2")

    def test_specific_relation_init(self) -> None:
        with self.assertRaises(ValueError):
            fields.ForeignKeyField(
                description="The foreign key of fake_model_tahheque7O.",
                to=Collection("fake_model_tahheque7O"),
                related_name="invalid_related_name",
                specific_relation="invalid_specific_relation",
            )

    def test_specific_relation_init_2(self) -> None:
        with self.assertRaises(ValueError):
            fields.ForeignKeyField(
                description="The foreign key of fake_model_tahheque7O.",
                to=Collection("fake_model_tahheque7O"),
                related_name="invalid_related_name_with_$",
            )
