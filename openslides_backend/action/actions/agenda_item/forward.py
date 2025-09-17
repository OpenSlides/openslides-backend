from typing import Any

from ....models.models import AgendaItem
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData

# agenda_item, topic_data, los data, speakers, sllos, list of children
TreeNode = tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    list["TreeNode"],
]


@register_action("agenda_item.forward")
class AgendaItemForward(SingularActionMixin, UpdateAction):
    """
    Action to forward a list of agenda_items.
    """

    model = AgendaItem()
    schema = DefaultSchema(AgendaItem()).get_create_schema(
        additional_required_fields={
            "meeting_ids": id_list_schema,
            "agenda_item_ids": id_list_schema,
        },
        additional_optional_fields={
            "with_speakers": {"type": "boolean"},
            "with_moderator_notes": {"type": "boolean"},
            "with_attachments": {"type": "boolean"},
        },
    )
    permission = Permissions.AgendaItem.CAN_FORWARD

    meeting_id: int

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        if origin_item_ids := instance.get("agenda_item_ids"):
            return self.datastore.get(
                fqid_from_collection_and_id("agenda_item", origin_item_ids[0]),
                ["meeting_id"],
            )["meeting_id"]
        return self.meeting_id

    def check_permissions(self, instance: dict[str, Any]) -> None:
        super().check_permissions(instance)
        if instance.get("with_speakers"):
            banned_meetings = {
                meeting_id
                for meeting_id in instance.get("meeting_ids", [])
                if not has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.User.CAN_MANAGE,
                    meeting_id,
                )
            }
            if banned_meetings:
                raise MissingPermission({Permissions.User.CAN_MANAGE: banned_meetings})

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        action_data = super().get_updated_instances(action_data)
        # Action data is an iterable with exactly one item
        instance = next(iter(action_data))
        if not (target_meeting_ids := instance.get("meeting_ids", [])):
            raise ActionException("Cannot forward without target meetings.")
        if not (origin_item_ids := instance.get("agenda_item_ids", [])):
            raise ActionException(
                "Cannot forward an agenda without the agenda_item_ids."
            )
        transferable_agenda_fields = [
            "type",
            "item_number",
            "comment",
            "closed",
            "duration",
            "tag_ids",
            "weight",
        ]
        origin_items = self.datastore.get_many(
            [
                GetManyRequest(
                    "agenda_item",
                    origin_item_ids,
                    [
                        "id",
                        "content_object_id",
                        *transferable_agenda_fields,
                        "meeting_id",
                        "parent_id",
                    ],
                )
            ]
        )["agenda_item"]
        child_id_to_parent_id: dict[int, int | None] = {}
        origin_meeting_id = origin_items[origin_item_ids[0]]["meeting_id"]
        for id_, item in origin_items.items():
            if item["meeting_id"] != origin_meeting_id:
                raise ActionException(
                    "Agenda forwarding requires all agenda_items to be part of the same meeting."
                )
            if not item["content_object_id"].startsWith("topic/"):
                raise ActionException(
                    f"Cannot forward agenda_item/{id_}: Not linked to a topic."
                )
            if parent_id := item.get("parent_id"):
                if parent_id not in origin_item_ids:
                    while (
                        parent_id := self.datastore.get(
                            fqid_from_collection_and_id("agenda_item", parent_id),
                            ["parent_id"],
                        ).get("parent_id")
                    ) is not None:
                        if parent_id in origin_item_ids:
                            break
                child_id_to_parent_id[id_] = parent_id
            else:
                child_id_to_parent_id[id_] = None

        self.meeting_id = origin_meeting_id
        if origin_meeting_id in target_meeting_ids:
            raise ActionException(
                f"Cannot forward agenda to the same meeting: meeting/{origin_meeting_id}"
            )
        transferable_topic_fields = [
            "title",
            "text",
            "attachment_meeting_mediafile_ids",
        ]
        original_topics = self.datastore.get_many(
            [
                GetManyRequest(
                    "topic",
                    [
                        id_from_fqid(item["content_object_id"])
                        for item in origin_items.values()
                    ],
                    [*transferable_topic_fields, "list_of_speakers_id"],
                )
            ]
        )["topic"]
        with_speakers = instance.get("with_speakers")
        with_moderator_notes = instance.get("with_moderator_notes")
        with_attachments = instance.get("with_attachments")
        more_data_gmrs: list[GetManyRequest] = []
        more_data: dict[str, dict[int, dict[str, Any]]] = {}
        transferable_los_fields = ["closed", "moderator_notes"]
        if with_speakers or with_moderator_notes or with_attachments:
            if with_attachments:
                original_meeting_mediafile_ids = {
                    id_
                    for topic in original_topics.values()
                    for id_ in topic.get("attachment_meeting_mediafile_ids", [])
                }
                if original_meeting_mediafile_ids:
                    more_data_gmrs = [
                        GetManyRequest(
                            "meeting_mediafile",
                            list(original_meeting_mediafile_ids),
                            ["mediafile_id"],
                        )
                    ]
            los_fields: list[str] = []
            if with_speakers:
                los_fields = [
                    "closed",
                    "speaker_ids",
                    "structure_level_list_of_speakers_ids",
                ]
            if with_moderator_notes:
                los_fields.append("moderator_notes")
            if los_fields:
                more_data_gmrs.append(
                    GetManyRequest(
                        "list_of_speakers",
                        [
                            topic["list_of_speakers_id"]
                            for topic in original_topics.values()
                        ],
                        los_fields,
                    )
                )
            more_data = self.datastore.get_many(more_data_gmrs)
            more_data_gmrs = []
            mediafile_fields = [
                "title",
                "is_directory",
                "filesize",
                "filename",
                "mimetype",
                "pdf_information",
                "create_timestamp",
                "published_to_meetings_in_organization_id",
                "child_ids",
            ]
            if "meeting_mediafile" in more_data:
                more_data_gmrs = [
                    GetManyRequest(
                        "mediafile",
                        [
                            mm["mediafile_id"]
                            for mm in more_data["meeting_mediafile"].values()
                        ],
                        mediafile_fields,
                    )
                ]
            if with_speakers:
                speaker_ids = {
                    id_
                    for los in more_data.get("list_of_speakers", {}).values()
                    for id_ in los.get("speaker_ids", [])
                }
                if speaker_ids:
                    more_data_gmrs.append(
                        GetManyRequest(
                            "speaker",
                            list(speaker_ids),
                            [
                                "begin_time",
                                "end_time",
                                "pause_time",
                                "unpause_time",
                                "total_pause",
                                "weight",
                                "speech_state",
                                "answer",
                                "note",
                                "point_of_order",
                                "structure_level_list_of_speakers_id",
                                "meeting_user_id",
                                "point_of_order_category_id",  # TODO: wtf am I to do with this
                            ],
                        )
                    )
                sllos_ids = {
                    id_
                    for los in more_data.get("list_of_speakers", {}).values()
                    for id_ in los.get("structure_level_list_of_speakers_ids", [])
                }
                if sllos_ids:
                    more_data_gmrs.append(
                        GetManyRequest(
                            "structure_level_list_of_speakers",
                            list(sllos_ids),
                            [
                                "structure_level_id",
                                "initial_time",
                                "additional_time",
                                "remaining_time",
                            ],
                        )
                    )
            if more_data_gmrs:
                more_data.update(self.datastore.get_many(more_data_gmrs))
                more_data_gmrs = []

                for id_, speaker in more_data.get("speaker", {}).items():
                    if not speaker.get("end_time"):
                        if speaker.get("begin_time"):
                            raise ActionException(
                                "Cannot forward when there are running speakers."
                            )
                        if speaker.get("point_of_order"):
                            raise ActionException(
                                "Cannot forward when there are waiting points of order."
                            )

                """
                TODO:
                Step 1:
                - All child ids (and subsequent) of all mediafiles need to be loaded (perhaps do circling calls in ongoing steps)
                    -> Same fields
                - All meeting_users connected to the speakers need to be loaded
                    -> fields: user_id, group_ids, structure_level_ids (pending (TODO: See issue): comment, number, about_me, vote_weight, locked_out)
                (- All point_of_order_categories connected to any of the speakers need to be loaded -> TODO: See in issue what needs to be done about them first)
                Step 2:
                - All group_ids from all meeting_users need to be loaded
                    -> fields: name
                - All structure_levels from all meeting_users and sllos need to be loaded
                    -> fields: name, color (pending (TODO: See issue): default_time)
                -> Add all this data to more_data
                """

        tree_list: list[TreeNode] = []
        id_to_node: dict[int, TreeNode] = {}
        while len(child_id_to_parent_id):
            ids = list(child_id_to_parent_id)
            for id_ in ids:
                if (
                    parent_id := child_id_to_parent_id[id_]
                ) is None or parent_id in id_to_node:
                    item = origin_items[id_]
                    topic = original_topics[id_from_fqid(item["content_object_id"])]
                    los = more_data.get("list_of_speakers", {}).get(
                        topic["list_of_speakers_id"], {}
                    )
                    speakers = {
                        id_: more_data.get("speakers", {})[id_]
                        for id_ in los.get("speaker_ids", [])
                    }
                    sllos = {
                        id_: more_data.get("speakers", {})[id_]
                        for id_ in los.get("structure_level_list_of_speakers_ids", [])
                    }
                    id_to_node[id_] = (
                        {
                            field: item[field]
                            for field in transferable_agenda_fields
                            if field in item
                        },
                        {
                            field: topic[field]
                            for field in transferable_topic_fields
                            if field in topic
                        },
                        {
                            field: los[field]
                            for field in transferable_los_fields
                            if field in los
                        },
                        speakers,
                        sllos,
                        [],
                    )
                    if parent_id is None:
                        tree_list.append(id_to_node[id_])
                    del child_id_to_parent_id[id_]

        for meeting_id in target_meeting_ids:
            yield from self.get_updated_instances_for_meeting(
                meeting_id,
                tree_list,
                more_data.get("meeting_mediafile", {}),
                more_data.get("mediafile", {}),
                more_data.get("meeting_user", {}),
                more_data.get("group", {}),
                more_data.get("structure_level", {}),
                more_data.get("point_of_order_category", {}),
            )

    def get_updated_instances_for_meeting(
        self,
        target_meeting_id: int,
        tree_list: list[TreeNode],
        meeting_mediafiles: dict[int, dict[str, Any]],
        mediafiles: dict[int, dict[str, Any]],
        meeting_users: dict[int, dict[str, Any]],
        groups: dict[int, dict[str, Any]],
        structure_levels: dict[int, dict[str, Any]],
        point_of_order_categories: dict[int, dict[str, Any]],
    ) -> ActionData:
        pass
