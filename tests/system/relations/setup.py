from unittest.mock import MagicMock, _patch, patch

from openslides_backend.action.generics.create import CreateAction
from openslides_backend.action.generics.update import UpdateAction
from openslides_backend.action.relations.single_relation_handler import (
    SingleRelationHandler,
)
from openslides_backend.action.relations.typing import RelationFieldUpdates
from openslides_backend.action.util.action_type import ActionType
from openslides_backend.action.util.register import register_action
from openslides_backend.models import fields
from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)
from tests.patch_model_registry_helper import FakeModel, PatchModelRegistryMixin

from ..action.base_generic import BaseGenericTestCase

fake_meeting = "fake_meeting"
collection_a = "fake_model_a"
collection_b = "fake_model_b"
collection_c = "fake_model_c"


class BaseRelationsTestCase(PatchModelRegistryMixin, BaseGenericTestCase):
    yml = f"""
    _meta:
        id_field: &id_field
            type: number
            restriction_mode: A
            constant: true
            required: true
    {collection_a}:
        id: *id_field
        meeting_id:
            type: relation
            to: {fake_meeting}/{collection_a}_ids
            reference: {fake_meeting}
            default: 1
        {collection_b}_oo:
            type: relation
            to: {collection_b}/{collection_a}_oo
            reference: {collection_b}
        {collection_b}_om:
            type: relation
            to: {collection_b}/{collection_a}_mo
            reference: {collection_b}
        {collection_b}_mm:
            type: relation-list
            to: {collection_b}/{collection_a}_mm
            equal_fields: meeting_id
        {collection_b}_generic_oo:
            type: relation
            to: {collection_b}/{collection_a}_generic_oo
            reference: {collection_b}
        {collection_b}_generic_mm:
            type: relation-list
            to: {collection_b}/{collection_a}_generic_mm
        fake_model_generic_multitype:
            type: generic-relation
            reference:
            - {collection_c}
            - {collection_b}
            to:
            - {collection_c}/{collection_a}_generic_multitype_o
            - {collection_b}/{collection_a}_generic_multitype_m
    {collection_b}:
        id: *id_field
        meeting_id:
            type: relation
            to: {fake_meeting}/{collection_b}_ids
            reference: {fake_meeting}
            required: true
            default: 1
        {collection_a}_oo:
            type: relation
            to: {collection_a}/{collection_b}_oo
            reference: {collection_a}
        {collection_a}_mo:
            type: relation-list
            to: {collection_a}/{collection_b}_om
            reference: {collection_a}
        {collection_a}_mm:
            type: relation-list
            to: {collection_a}/{collection_b}_mm
            equal_fields: meeting_id
        {collection_a}_generic_oo:
            type: generic-relation
            reference:
            - {collection_a}
            to:
            - {collection_a}/{collection_b}_generic_oo
        {collection_a}_generic_mm:
            type: generic-relation-list
            to:
                collections:
                    - {collection_a}
                field: {collection_b}_generic_mm
        {collection_a}_generic_multitype_m:
            type: relation-list
            to: {collection_a}/fake_model_generic_multitype
            reference: {collection_a}
        {collection_c}_ids:
            type: relation-list
            to: {collection_c}/foreign_key_field
            reference: {collection_c}
    {collection_c}:
        id: *id_field
        meeting_id:
            type: relation
            to: {fake_meeting}/{collection_c}_ids
            reference: {fake_meeting}
            required: true
            default: 1
        {collection_a}_generic_multitype_o:
            type: relation
            to: {collection_a}/fake_model_generic_multitype
            reference: {collection_a}
        foreign_key_field:
            type: relation
            to: {collection_b}/{collection_c}_ids
            reference: {collection_b}
    {fake_meeting}:
        id: *id_field
        {collection_a}_ids:
            type: relation-list
            to: {collection_a}/meeting_id
            reference: {collection_a}
        {collection_b}_ids:
            type: relation-list
            to: {collection_b}/meeting_id
            reference: {collection_b}
        {collection_c}_ids:
            type: relation-list
            to: {collection_c}/meeting_id
            reference: {collection_c}
    """
    patcher: _patch

    @classmethod
    def setUpClass(cls) -> None:
        cls.patcher = patch(
            "meta.dev.src.helper_get_names.HelperGetNames.trigger_unique_list", []
        )
        cls.patcher.start()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.patcher.stop()

    def setUp(self) -> None:
        super().setUp()
        self.set_models({"fake_meeting/1": {"id": 1}})


class FakeModelA(FakeModel):
    collection = "fake_model_a"
    verbose_name = "fake model a"

    id = fields.IntegerField(required=True, constant=True)

    meeting_id = fields.RelationField(
        default=1, to={"fake_meeting": "fake_model_a_ids"}
    )

    # normal relations
    fake_model_b_oo = fields.RelationField(to={"fake_model_b": "fake_model_a_oo"})
    fake_model_b_om = fields.RelationField(to={"fake_model_b": "fake_model_a_mo"})
    fake_model_b_mm = fields.RelationListField(
        to={"fake_model_b": "fake_model_a_mm"},
        is_view_field=True,
        is_primary=True,
        equal_fields="meeting_id",
        write_fields=(
            "nm_fake_model_a_fake_model_b_mm_fake_model_b_t",
            "fake_model_a_id",
            "fake_model_b_id",
            [],
        ),
    )
    fake_model_b_generic_oo = fields.RelationField(
        to={"fake_model_b": "fake_model_a_generic_oo"}
    )
    # fake_model_b_generic_om = fields.RelationField(
    #     to={"fake_model_b": "fake_model_a_generic_mo"},
    # )
    fake_model_b_generic_mm = fields.RelationListField(
        to={"fake_model_b": "fake_model_a_generic_mm"},
        is_view_field=True,
        write_fields=(
            "gm_fake_model_b_fake_model_a_generic_mm_t",
            "fake_model_a_id",
            "fake_model_b_generic_m",
            ["fake_model_b_generic_m_fake_model_b_id"],
        ),
    )
    # generic field which is m2m in one target collection and m2o in another
    # Important: First comes the m2o relation
    fake_model_generic_multitype = fields.GenericRelationField(
        to={
            "fake_model_b": "fake_model_a_generic_multitype_m",
            "fake_model_c": "fake_model_a_generic_multitype_o",
        }
    )


class FakeModelB(FakeModel):
    collection = "fake_model_b"
    verbose_name = "fake model b"

    id = fields.IntegerField(required=True, constant=True)

    meeting_id = fields.RelationField(
        default=1,
        to={"fake_meeting": "fake_model_b_ids"},
        required=True,
    )

    fake_model_a_oo = fields.RelationField(to={"fake_model_a": "fake_model_b_oo"})
    fake_model_a_mo = fields.RelationListField(
        to={"fake_model_a": "fake_model_b_om"}, is_view_field=True, is_primary=True
    )
    fake_model_a_mm = fields.RelationListField(
        to={"fake_model_a": "fake_model_b_mm"},
        is_view_field=True,
        equal_fields="meeting_id",
        write_fields=(
            "nm_fake_model_a_fake_model_b_mm_fake_model_b_t",
            "fake_model_b_id",
            "fake_model_a_id",
            [],
        ),
    )
    fake_model_a_generic_oo = fields.GenericRelationField(
        to={"fake_model_a": "fake_model_b_generic_oo"}
    )
    # fake_model_a_generic_mo = fields.GenericRelationListField(
    #     to={"fake_model_a": "fake_model_b_generic_om"},
    # )
    fake_model_a_generic_mm = fields.GenericRelationListField(
        to={"fake_model_a": "fake_model_b_generic_mm"},
        is_view_field=True,
        is_primary=True,
        write_fields=(
            "gm_fake_model_b_fake_model_a_generic_mm_t",
            "fake_model_b_id",
            "fake_model_a_generic_m",
            ["fake_model_a_generic_m_fake_model_a_id"],
        ),
    )
    fake_model_a_generic_multitype_m = fields.RelationListField(
        to={"fake_model_a": "fake_model_generic_multitype"},
        is_view_field=True,
        is_primary=True,
    )
    fake_model_c_ids = fields.RelationListField(
        to={"fake_model_c": "foreign_key_field"}, is_view_field=True, is_primary=True
    )


class FakeModelC(FakeModel):
    collection = "fake_model_c"
    verbose_name = "fake model c"

    id = fields.IntegerField(required=True, constant=True)

    meeting_id = fields.RelationField(
        default=1,
        to={"fake_meeting": "fake_model_c_ids"},
        required=True,
    )

    fake_model_a_generic_multitype_o = fields.RelationField(
        to={"fake_model_a": "fake_model_generic_multitype"}
    )

    foreign_key_field = fields.RelationField(to={"fake_model_b": "fake_model_c_ids"})


class FakeMeeting(FakeModel):
    collection = "fake_meeting"
    verbose_name = "fake meeting"

    id = fields.IntegerField(required=True, constant=True)
    fake_model_a_ids = fields.RelationListField(
        to={"fake_model_a": "meeting_id"}, is_view_field=True, is_primary=True
    )
    fake_model_b_ids = fields.RelationListField(
        to={"fake_model_b": "meeting_id"}, is_view_field=True, is_primary=True
    )
    fake_model_c_ids = fields.RelationListField(
        to={"fake_model_c": "meeting_id"}, is_view_field=True, is_primary=True
    )


@register_action("fake_model_a.create", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelACreateAction(CreateAction):
    model = FakeModelA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


@register_action("fake_model_a.update", action_type=ActionType.BACKEND_INTERNAL)
class FakeModelAUpdateAction(UpdateAction):
    model = FakeModelA()
    schema = {}  # type: ignore
    skip_archived_meeting_check = True


class SingleRelationHandlerWithContext(SingleRelationHandler):
    """
    Overwrites the perform method of the SingleRelationHandler to provide a datastore context.
    """

    def perform(self) -> RelationFieldUpdates:
        with get_new_os_conn() as conn:
            self.datastore = ExtendedDatabase(conn, MagicMock(), MagicMock())
            return super().perform()
