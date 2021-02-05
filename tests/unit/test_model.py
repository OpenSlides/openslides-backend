from typing import cast
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

    id = fields.IntegerField(required=True)
    text = fields.CharField(
        required=True, constraints={"description": "The text of this fake model."}
    )
    fake_model_2_ids = fields.RelationListField(
        to={Collection("fake_model_2"): "relation_field"}
    )
    fake_model_2_generic_ids = fields.GenericRelationListField(
        to={Collection("fake_model_2"): "generic_relation_field"}
    )


class FakeModel2(Model):
    """
    Fake model for testing purposes. With relation field.
    """

    collection = Collection("fake_model_2")
    verbose_name = "fake_model_2"

    id = fields.IntegerField(required=True)
    relation_field = fields.RelationField(
        to={Collection("fake_model"): "fake_model_2_ids"},
    )
    generic_relation_field = fields.RelationField(
        to={Collection("fake_model"): "fake_model_2_generic_ids"},
    )


class ModelBaseTester(TestCase):
    """
    Tests methods of base Action class and also some helper functions.
    """

    def test_get_properties(self) -> None:
        expected = {
            "id": {"type": "integer"},
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
            "Model fake_model has no field unknown_property.",
        )

    def test_get_fields_fake_model(self) -> None:
        self.assertEqual(
            ["fake_model_2_generic_ids", "fake_model_2_ids", "id", "text"],
            [field.own_field_name for field in FakeModel().get_fields()],
        )

    def test_own_collection_attr(self) -> None:
        rels = [
            FakeModel().get_field("fake_model_2_ids"),
            FakeModel().get_field("fake_model_2_generic_ids"),
        ]
        field = cast(fields.BaseRelationField, rels[0])
        self.assertEqual(str(field.own_collection), "fake_model")
        field = cast(fields.BaseRelationField, rels[1])
        self.assertEqual(str(field.own_collection), "fake_model")

    def test_get_field_unknown_field(self) -> None:
        with self.assertRaises(ValueError):
            FakeModel().get_field("Unknown field")
