from typing import cast
from unittest import TestCase

from fastjsonschema import validate

from openslides_backend.action.util.default_schema import DefaultSchema
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.exceptions import ActionException


class FakeModel(Model):
    """
    Fake Model for testing purposes.
    """

    collection = "fake_model"
    verbose_name = "fake_model"

    id = fields.IntegerField(required=True)
    read_only = fields.IntegerField(read_only=True)
    json = fields.JSONField()
    text = fields.CharField(
        required=True, constraints={"description": "The text of this fake model."}
    )
    fake_model_2_ids = fields.RelationListField(to={"fake_model_2": "relation_field"})
    fake_model_2_generic_ids = fields.GenericRelationListField(
        to={"fake_model_2": "generic_relation_field"}
    )


class FakeModel2(Model):
    """
    Fake model for testing purposes. With relation field.
    """

    collection = "fake_model_2"
    verbose_name = "fake_model_2"

    id = fields.IntegerField(required=True)
    relation_field = fields.RelationField(
        to={"fake_model": "fake_model_2_ids"},
    )
    generic_relation_field = fields.RelationField(
        to={"fake_model": "fake_model_2_generic_ids"},
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
            [
                "fake_model_2_generic_ids",
                "fake_model_2_ids",
                "id",
                "json",
                "read_only",
                "text",
            ],
            [field.own_field_name for field in FakeModel().get_fields()],
        )

    def test_own_collection_attr(self) -> None:
        rels = [
            FakeModel().get_field("fake_model_2_ids"),
            FakeModel().get_field("fake_model_2_generic_ids"),
        ]
        for rel in rels:
            field = cast(fields.BaseRelationField, rel)
            self.assertEqual(str(field.own_collection), "fake_model")

    def test_get_field_unknown_field(self) -> None:
        with self.assertRaises(ValueError):
            FakeModel().get_field("Unknown field")

    def test_get_read_only_field(self) -> None:
        with self.assertRaises(ActionException):
            FakeModel().get_property("read_only")

    def test_json_field_array(self) -> None:
        schema = DefaultSchema(FakeModel()).get_default_schema(
            optional_properties=["json"]
        )
        validate(schema, {"json": [1, 2]})
