from typing import cast

from openslides_backend.action.relations import RelationsHandler
from openslides_backend.models import fields
from tests.util import get_fqfield

from .setup import BaseRelationsTestCase, FakeModelB, FakeModelC


class StructuredRelationTester(BaseRelationsTestCase):
    maxDiff = None

    def test_simple_structured_relation(self) -> None:
        meeting_id = 222
        self.create_model("fake_model_a/333", {})
        self.create_model("fake_model_b/111", {"meeting_id": meeting_id})
        field = cast(
            fields.BaseRelationField,
            FakeModelB().get_field("structured_relation_field"),
        )
        relations_handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelB(),
            id=111,
            field=field,
            field_name="structured_relation_field",
            obj={"structured_relation_field": 333},
        )
        result = relations_handler.perform()
        self.assertEqual(
            result,
            {
                get_fqfield("fake_model_a/333/fake_model_b_$_ids"): {
                    "type": "add",
                    "value": [str(meeting_id)],
                    "modified_element": str(meeting_id),
                },
                get_fqfield(f"fake_model_a/333/fake_model_b_${meeting_id}_ids"): {
                    "type": "add",
                    "value": [111],
                    "modified_element": 111,
                },
            },
        )

    def test_nested_structured_relation(self) -> None:
        meeting_id = 222
        self.create_model("fake_model_a/333", {})
        self.create_model("fake_model_b/111", {"meeting_id": meeting_id})
        self.create_model("fake_model_c/444", {"foreign_key_field": 111})
        field = cast(
            fields.BaseRelationField,
            FakeModelC().get_field("structured_relation_field"),
        )
        relations_handler = RelationsHandler(
            datastore=self.datastore,
            model=FakeModelC(),
            id=444,
            field=field,
            field_name="structured_relation_field",
            obj={"structured_relation_field": 333},
        )
        result = relations_handler.perform()
        self.assertEqual(
            result,
            {
                get_fqfield("fake_model_a/333/fake_model_c_$_ids"): {
                    "type": "add",
                    "value": [str(meeting_id)],
                    "modified_element": str(meeting_id),
                },
                get_fqfield(f"fake_model_a/333/fake_model_c_${meeting_id}_ids"): {
                    "type": "add",
                    "value": [444],
                    "modified_element": 444,
                },
            },
        )
