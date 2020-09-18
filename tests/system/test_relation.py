from typing import cast

from openslides_backend.action.relations import RelationsHandler
from openslides_backend.models import fields
from openslides_backend.models.base import Model
from openslides_backend.shared.interfaces import WSGIApplication
from openslides_backend.shared.patterns import Collection
from tests.system.base import BaseSystemTestCase
from tests.system.util import create_action_test_application
from tests.util import get_fqfield


class FakeModel(Model):
    """
    Fake model for testing purposes.
    """

    collection = Collection("fake_model_gingaosh")
    verbose_name = "fake_model_gingaosh"
    id = fields.IdField(description="The id of this fake model.")


class FakeModel2(Model):
    """
    Fake model for testing purposes. With relation field.
    """

    collection = Collection("fake_model_yafhnzreer")
    verbose_name = "fake_model_yafhnzreer"

    id = fields.IdField(description="The id of this fake model.")
    meeting_id = fields.RequiredForeignKeyField(
        description="The id of the meeting of this fake model.",
        to=Collection("meeting"),
        related_name="fake_model_yafhnzreer_ids",
    )
    structured_relation_field = fields.ForeignKeyField(
        description="The foreign key to fake_model.",
        to=Collection("fake_model_gingaosh"),
        related_name="fake_model_yafhnzreer_$_ids",
        structured_relation=["meeting_id"],
    )


class FakeModel3(Model):
    """
    Fake model for testing purposes.
    """

    collection = Collection("fake_model_vcbjlbkvriewopsd")
    verbose_name = "fake_model_vcbjlbkvriewopsd"
    id = fields.IdField(description="The id of this fake model.")
    foreign_key_field = fields.ForeignKeyField(
        description="The id of the meeting of this fake model.",
        to=Collection("fake_model_yafhnzreer"),
        related_name="fake_model_vcbjlbkvriewopsd_ids",
    )
    structured_relation_field = fields.ForeignKeyField(
        description="The foreign key to fake_model.",
        to=Collection("fake_model_gingaosh"),
        related_name="fake_model_vcbjlbkvriewopsd_$_ids",
        structured_relation=["foreign_key_field", "meeting_id"],
    )


class StructuredRelationTester(BaseSystemTestCase):
    def get_application(self) -> WSGIApplication:
        return create_action_test_application()

    def test_simple_structured_relation(self) -> None:
        meeting_id = 222
        self.create_model("fake_model_gingaosh/333", {})
        self.create_model("fake_model_yafhnzreer/111", {"meeting_id": meeting_id})
        field = cast(
            fields.RelationMixin, FakeModel2().get_field("structured_relation_field")
        )
        relations_handler = RelationsHandler(
            database=self.datastore,
            model=FakeModel2(),
            id=111,
            field=field,
            field_name="structured_relation_field",
            obj={"structured_relation_field": 333},
        )
        result = relations_handler.perform()
        self.assertEqual(
            result,
            {
                get_fqfield(
                    f"fake_model_gingaosh/333/fake_model_yafhnzreer_{meeting_id}_ids"
                ): {
                    "type": "add",
                    "value": [111],
                }
            },
        )

    def test_nested_structured_relation(self) -> None:
        meeting_id = 222
        self.create_model("fake_model_gingaosh/333", {})
        self.create_model("fake_model_yafhnzreer/111", {"meeting_id": meeting_id})
        self.create_model("fake_model_vcbjlbkvriewopsd/444", {"foreign_key_field": 111})
        field = cast(
            fields.RelationMixin, FakeModel3().get_field("structured_relation_field")
        )
        relations_handler = RelationsHandler(
            database=self.datastore,
            model=FakeModel3(),
            id=444,
            field=field,
            field_name="structured_relation_field",
            obj={"structured_relation_field": 333},
        )
        result = relations_handler.perform()
        self.assertEqual(
            result,
            {
                get_fqfield(
                    f"fake_model_gingaosh/333/fake_model_vcbjlbkvriewopsd_{meeting_id}_ids"
                ): {
                    "type": "add",
                    "value": [444],
                }
            },
        )
