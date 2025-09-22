from typing import Any, cast

from ....models.models import AgendaItem
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.schema import id_list_schema
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResultElement
from ..group.create import GroupCreate
from ..list_of_speakers.update import ListOfSpeakersUpdateAction
from ..mediafile.duplicate_to_another_meeting import (
    MediafileDuplicateToAnotherMeetingAction,
)
from ..meeting_user.set_data import MeetingUserSetData
from ..point_of_order_category.create import PointOfOrderCategoryCreate
from ..speaker.create_for_merge import SpeakerCreateForMerge
from ..structure_level.create import StructureLevelCreateAction
from ..structure_level_list_of_speakers.create import (
    StructureLevelListOfSpeakersCreateAction,
)
from ..structure_level_list_of_speakers.update import (
    StructureLevelListOfSpeakersUpdateAction,
)
from ..structure_level_list_of_speakers.add_time import (
    StructureLevelListOfSpeakersAddTimeAction,
)
from ..topic.create import TopicCreate

# agenda_item, topic_data, los data, speakers, sllos, list of children
TreeNode = tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    list["TreeNode"],
]
MEDIAFILE_FIELDS = [
    "title",
    "is_directory",
    "filesize",
    "filename",
    "mimetype",
    "pdf_information",
    "published_to_meetings_in_organization_id",
    "child_ids",
]
TRANSFERRABLE_POOC_FIELDS = ["text", "rank"]
TRANSFERRABLE_STRUCTURE_LEVEL_FIELDS = ["name", "color"]
TRANSFERRABLE_MEETING_USER_FIELDS = [
    "comment",
    "number",
    "about_me",
]
TRANSFERRABLE_AGENDA_FIELD = [
    "type",
    "comment",
    "weight",
]
TRANSFERRABLE_SPEAKER_FIELDS = [
    "begin_time",
    "end_time",
    "unpause_time",
    "total_pause",
    "weight",
    "speech_state",
    "answer",
    "note",
    "point_of_order",
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
        if "id" in instance or "meeting_id" in instance:
            super().get_meeting_id(instance)
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

        origin_items = self.datastore.get_many(
            [
                GetManyRequest(
                    "agenda_item",
                    origin_item_ids,
                    [
                        "id",
                        "content_object_id",
                        *TRANSFERRABLE_AGENDA_FIELD,
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
            if not item["content_object_id"].startswith("topic/"):
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
        data = self.datastore.get_many(
            [
                GetManyRequest(
                    "topic",
                    [
                        id_from_fqid(item["content_object_id"])
                        for item in origin_items.values()
                    ],
                    [*transferable_topic_fields, "list_of_speakers_id"],
                ),
                GetManyRequest(
                    "meeting",
                    [self.meeting_id, *target_meeting_ids],
                    [
                        "admin_group_id",
                        "committee_id",
                        "meeting_user_ids",
                        "group_ids",
                        "structure_level_ids",
                        "point_of_order_category_ids",
                    ],
                ),
            ]
        )
        original_topics = data["topic"]
        meetings = data["meeting"]
        origin_committee = self.datastore.get(
            fqid_from_collection_and_id(
                "committee", meetings[self.meeting_id]["committee_id"]
            ),
            ["forward_agenda_to_committee_ids"],
        )
        forbidden_committees = {
            committee_id
            for meeting_id in target_meeting_ids
            if (committee_id := meetings[meeting_id]["committee_id"])
            not in origin_committee.get("forward_agenda_to_committee_ids", [])
        }
        if forbidden_committees:
            raise ActionException(
                f"Cannot forward to the following committee(s): {forbidden_committees}"
            )
        with_speakers = instance.get("with_speakers")
        with_moderator_notes = instance.get("with_moderator_notes")
        with_attachments = instance.get("with_attachments")
        more_data_gmrs: list[GetManyRequest] = []
        more_data: dict[str, dict[int, dict[str, Any]]] = {}
        transferable_los_fields = ["closed", "moderator_notes"]
        if with_speakers or with_moderator_notes or with_attachments:
            if with_attachments:
                more_data_gmrs = self.get_gmr_list_from_relation_field(
                    "meeting_mediafile",
                    ["mediafile_id"],
                    original_topics,
                    "attachment_meeting_mediafile_ids",
                    is_list_field=True,
                )
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
                more_data_gmrs.extend(
                    self.get_gmr_list_from_relation_field(
                        "list_of_speakers",
                        los_fields,
                        original_topics,
                        "list_of_speakers_id",
                    )
                )
            more_data = self.datastore.get_many(more_data_gmrs)
            more_data_gmrs = [
                *self.get_gmr_list_from_relation_field(
                    "mediafile",
                    MEDIAFILE_FIELDS,
                    more_data.get("meeting_mediafile", {}),
                    "mediafile_id",
                ),
                *self.get_gmr_list_from_relation_field(
                    "speaker",
                    [
                        *TRANSFERRABLE_SPEAKER_FIELDS,
                        "structure_level_list_of_speakers_id",
                        "meeting_user_id",
                        "point_of_order_category_id",
                    ],
                    more_data.get("list_of_speakers", {}),
                    "speaker_ids",
                    is_list_field=True,
                ),
                *self.get_gmr_list_from_relation_field(
                    "structure_level_list_of_speakers",
                    [
                        "structure_level_id",
                        "initial_time",
                        "additional_time",
                        "remaining_time",
                    ],
                    more_data.get("list_of_speakers", {}),
                    "structure_level_list_of_speakers_ids",
                    is_list_field=True,
                ),
            ]
            if more_data_gmrs:
                more_data.update(self.datastore.get_many(more_data_gmrs))
                new_mediafiles = more_data.get("mediafile", {})

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

                more_data_gmrs = [
                    *self.get_gmr_list_with_mediafile_child_gmr(
                        new_mediafiles, new_mediafiles
                    ),
                    *self.get_gmr_list_from_relation_field(
                        "meeting_user",
                        [
                            "user_id",
                            "group_ids",
                            "structure_level_ids",
                            *TRANSFERRABLE_MEETING_USER_FIELDS,
                        ],
                        more_data.get("speaker", {}),
                        "meeting_user_id",
                    ),
                    *self.get_gmr_list_from_relation_field(
                        "point_of_order_category",
                        TRANSFERRABLE_POOC_FIELDS,
                        more_data.get("speaker", {}),
                        "point_of_order_category_id",
                    ),
                ]

                if more_data_gmrs:
                    new_data = self.datastore.get_many(more_data_gmrs)
                    new_mediafiles = new_data.get("mediafile", {})
                    if new_mediafiles:
                        more_data["mediafile"].update(new_mediafiles)
                        del new_data["mediafile"]
                    more_data.update(new_data)

                    more_data_gmrs = [
                        *self.get_gmr_list_with_mediafile_child_gmr(
                            new_mediafiles, more_data.get("mediafile", {})
                        ),
                        *self.get_gmr_list_from_relation_field(
                            "group",
                            ["name"],
                            more_data.get("meeting_user", {}),
                            "group_ids",
                            is_list_field=True,
                        ),
                    ]
                    structure_level_id_set = {
                        id_
                        for meeting_user in more_data.get("meeting_user", {}).values()
                        for id_ in meeting_user.get("structure_level_ids", [])
                    }
                    structure_level_id_set.update(
                        {
                            sllos["structure_level_id"]
                            for sllos in more_data.get(
                                "structure_level_list_of_speakers", {}
                            ).values()
                        }
                    )
                    if structure_level_id_set:
                        more_data_gmrs.append(
                            GetManyRequest(
                                "structure_level",
                                list(structure_level_id_set),
                                TRANSFERRABLE_STRUCTURE_LEVEL_FIELDS,
                            )
                        )
                    if more_data_gmrs:
                        new_data = self.datastore.get_many(more_data_gmrs)
                        new_mediafiles = new_data.get("mediafile", {})
                        if new_mediafiles:
                            more_data["mediafile"].update(new_mediafiles)
                            del new_data["mediafile"]
                        more_data.update(new_data)
                        while len(
                            more_data_gmrs := self.get_gmr_list_with_mediafile_child_gmr(
                                new_mediafiles, more_data.get("mediafile", {})
                            )
                        ):
                            new_mediafiles = self.datastore.get_many(
                                more_data_gmrs
                            ).get("mediafile", {})
                            more_data["mediafile"].update(new_mediafiles)

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
                        id_: more_data.get("speaker", {})[id_]
                        for id_ in los.get("speaker_ids", [])
                    }
                    sllos = {
                        id_: more_data.get("structure_level_list_of_speakers", {})[id_]
                        for id_ in los.get("structure_level_list_of_speakers_ids", [])
                    }
                    id_to_node[id_] = (
                        {
                            field: item[field]
                            for field in TRANSFERRABLE_AGENDA_FIELD
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
                    else:
                        id_to_node[parent_id][5].append(id_to_node[id_])
                    del child_id_to_parent_id[id_]

        for meeting_id in target_meeting_ids:
            yield from self.get_updated_instances_for_meeting(
                meeting_id,
                meetings[meeting_id],
                tree_list,
                more_data.get("meeting_mediafile", {}),
                more_data.get("mediafile", {}),
                more_data.get("meeting_user", {}),
                more_data.get("group", {}),
                more_data.get("structure_level", {}),
                more_data.get("point_of_order_category", {}),
                more_data.get("structure_level_list_of_speakers", {}),
            )

    def get_updated_instances_for_meeting(
        self,
        target_meeting_id: int,
        target_meeting: dict[str, Any],
        origin_tree_list: list[TreeNode],
        origin_meeting_mediafiles: dict[int, dict[str, Any]],
        origin_mediafiles: dict[int, dict[str, Any]],
        origin_musers: dict[int, dict[str, Any]],
        origin_groups: dict[int, dict[str, Any]],
        origin_structure_levels: dict[int, dict[str, Any]],
        origin_poocs: dict[int, dict[str, Any]],
        origin_sllos: dict[int, dict[str, Any]],
    ) -> ActionData:
        muser_matches, group_matches, structure_level_matches, pooc_matches = (
            self.create_and_update_non_mediafile_meeting_models(
                target_meeting_id,
                target_meeting,
                origin_musers,
                origin_groups,
                origin_structure_levels,
                origin_poocs,
                origin_sllos,
            )
        )
        mediafile_matches = self.create_mediafile_meeting_models(
            target_meeting_id, origin_mediafiles
        )
        max_weight = self.datastore.max("agenda_item", FilterOperator("meeting_id", "=", target_meeting_id), "weight", use_changed_models=False) or 0
        yield from self.get_updated_instances_from_tree_node(
            target_meeting_id,
            target_meeting,
            max_weight,
            origin_tree_list,
            muser_matches,
            group_matches,
            structure_level_matches,
            pooc_matches,
            mediafile_matches,
        )

    def get_updated_instances_from_tree_node(
        self,
        target_meeting_id: int,
        target_meeting: dict[str, Any],
        max_meeting_agenda_weight: int,
        origin_tree_list: list[TreeNode],
        muser_matches: dict[int, int],
        group_matches: dict[int, int],
        structure_level_matches: dict[int, int],
        pooc_matches: dict[int, int],
        mediafile_matches: dict[int, int],
        parent_id: int | None = None,
    ) -> ActionData:
        parent_data_dict = {"agenda_parent_id": parent_id} if parent_id else {}
        topic_payloads = [
            {
                "meeting_id": target_meeting_id,
                **parent_data_dict,
                **{
                    field: val
                    for field, val in topic.items()
                    if field != "attachment_meeting_mediafile_ids"
                },
                **(
                    {"attachment_mediafile_ids": mediafile_ids}
                    if (
                        mediafile_ids := [
                            mediafile_matches[origin_id]
                            for origin_id in topic.get("attachment_mediafile_ids", [])
                        ]
                    )
                    else {}
                ),
                **{f"agenda_{field}": (val if field != "weight" else val + max_meeting_agenda_weight) for field, val in agenda_item.items()},
            }
            for agenda_item, topic, los, speakers, sllos, list_of_children in origin_tree_list
        ]
        topic_results = self.execute_other_action(TopicCreate, topic_payloads)
        assert topic_results is not None
        topic_id_to_tree_node = {
            cast(ActionResultElement, top_res)["id"]: node
            for top_res, node in zip(topic_results, origin_tree_list)
        }
        new_topics = self.datastore.get_many(
            [
                GetManyRequest(
                    "topic",
                    list(topic_id_to_tree_node),
                    ["list_of_speakers_id", "agenda_item_id"],
                )
            ]
        )["topic"]
        # only if there are los, speakers or sllos
        topic_id_to_tree_node_with_los_data = {
            id_: node for id_, node in topic_id_to_tree_node.items() if node[2]
        }
        topic_id_to_tree_node_with_speaker_data = {
            id_: node for id_, node in topic_id_to_tree_node.items() if node[3]
        }
        topic_id_to_tree_node_with_sllos_data = {
            id_: node for id_, node in topic_id_to_tree_node.items() if node[4]
        }
        if topic_id_to_tree_node_with_los_data:
            self.execute_other_action(
                ListOfSpeakersUpdateAction,
                [
                    {"id": new_topics[topic_id]["list_of_speakers_id"], **node[2]}
                    for topic_id, node in topic_id_to_tree_node_with_los_data.items()
                ],
            )
        topic_id_to_sl_to_sllos_id: dict[int, dict[int, int]] = {}
        if topic_id_to_tree_node_with_sllos_data:
            payloads = [
                (
                    topic_id,
                    {
                        "initial_time": sllos["initial_time"],
                        "list_of_speakers_id": new_topics[topic_id][
                            "list_of_speakers_id"
                        ],
                        "structure_level_id": structure_level_matches[
                            sllos["structure_level_id"]
                        ],
                    },
                )
                for topic_id, node in topic_id_to_tree_node_with_sllos_data.items()
                for origin_sllos_id, sllos in node[4].items()
            ]
            result = self.execute_other_action(
                StructureLevelListOfSpeakersCreateAction,
                [payload for topic_id, payload in payloads],
            )
            assert result is not None
            for topiced_payload, res in zip(payloads, result):
                if topiced_payload[0] not in topic_id_to_sl_to_sllos_id:
                    topic_id_to_sl_to_sllos_id[topiced_payload[0]] = {}
                topic_id_to_sl_to_sllos_id[topiced_payload[0]][
                    topiced_payload[1]["structure_level_id"]
                ] = cast(ActionResultElement, res)["id"]
            fields = ["additional_time", "remaining_time"]
            update_payloads = [
                {
                    "id": topic_id_to_sl_to_sllos_id[topic_id][
                        structure_level_matches[sllos["structure_level_id"]]
                    ],
                    **{
                        field: val
                        for field in fields
                        if (val := sllos.get(field)) is not None
                    },
                }
                for topic_id, node in topic_id_to_tree_node_with_sllos_data.items()
                for origin_sllos_id, sllos in node[4].items()
                if any(sllos.get(field) is not None for field in fields)
            ]
            if update_payloads:
                self.execute_other_action(
                    StructureLevelListOfSpeakersUpdateAction, update_payloads
                )

        if topic_id_to_tree_node_with_speaker_data:
            speaker_payloads = [
                {
                    "meeting_user_id": muser_matches[speaker["meeting_user_id"]],
                    "list_of_speakers_id": new_topics[topic_id]["list_of_speakers_id"],
                    **(
                        {
                            "structure_level_list_of_speakers_id": topic_id_to_sl_to_sllos_id[
                                topic_id
                            ][
                                structure_level_matches[
                                    node[4][sllos_id]["structure_level_id"]
                                ]
                            ]
                        }
                        if (
                            sllos_id := speaker.get(
                                "structure_level_list_of_speakers_id"
                            )
                        )
                        else {}
                    ),
                    **(
                        {"point_of_order_category_id": pooc_matches[pooc_id]}
                        if (pooc_id := speaker.get("point_of_order_category_id"))
                        else {}
                    ),
                    **{
                        field: val
                        for field in TRANSFERRABLE_SPEAKER_FIELDS
                        if (val := speaker.get(field)) is not None
                    },
                }
                for topic_id, node in topic_id_to_tree_node_with_sllos_data.items()
                for origin_speaker_id, speaker in node[3].items()
            ]
            result = self.execute_other_action(SpeakerCreateForMerge, speaker_payloads)
        for topic_id, tree_node in topic_id_to_tree_node.items():
            agenda_item_id = new_topics[topic_id]["agenda_item_id"]
            yield {"id": agenda_item_id}
            if tree_node[5]:
                yield from self.get_updated_instances_from_tree_node(
                    target_meeting_id,
                    target_meeting,
                    max_meeting_agenda_weight,
                    tree_node[5],
                    muser_matches,
                    group_matches,
                    structure_level_matches,
                    pooc_matches,
                    mediafile_matches,
                    agenda_item_id,
                )

    def create_mediafile_meeting_models(
        self,
        target_meeting_id: int,
        origin_mediafiles: dict[int, dict[str, Any]],
    ) -> dict[int, int]:
        matches = {
            id_: id_
            for id_, mediafile in origin_mediafiles.items()
            if mediafile.get("published_to_meetings_in_organization_id")
        }
        unpublished_ids = sorted(
            [id_ for id_ in origin_mediafiles if id_ not in matches]
        )
        if unpublished_ids:
            origin_to_new_id = {
                origin_id: id_
                for id_, origin_id in zip(
                    self.datastore.reserve_ids("mediafile", len(unpublished_ids)),
                    unpublished_ids,
                )
            }
            payloads = [
                {
                    "id": id_,
                    "origin_id": origin_id,
                    "owner_id": fqid_from_collection_and_id(
                        "meeting", target_meeting_id
                    ),
                    **(
                        {"parent_id": origin_to_new_id[parent_id]}
                        if (parent_id := origin_mediafiles[origin_id].get("parent_id"))
                        else {}
                    ),
                }
                for origin_id, id_ in origin_to_new_id.items()
            ]
            self.execute_other_action(
                MediafileDuplicateToAnotherMeetingAction, payloads
            )
            matches.update(origin_to_new_id)
        return matches

    def create_and_update_non_mediafile_meeting_models(
        self,
        target_meeting_id: int,
        target_meeting: dict[str, Any],
        origin_musers: dict[int, dict[str, Any]],
        origin_groups: dict[int, dict[str, Any]],
        origin_structure_levels: dict[int, dict[str, Any]],
        origin_poocs: dict[int, dict[str, Any]],
        origin_sllos: dict[int, dict[str, Any]],
    ) -> tuple[dict[int, int], dict[int, int], dict[int, int], dict[int, int]]:
        """
        Matches origin meeting collection data to matching targed meeting data.
        Creates non-existant models and makes necessary updates to existing ones.
        Returns a origin-meeting-model-id to target-meeting-model-id dicts for
        meeting_users, groups, structure_levels and poocs in that order.
        """
        # using gmrs instead of filters bc probably more performant in this case
        gmrs = [
            GetManyRequest(collection, ids, fields)
            for collection, from_field, fields in [
                (
                    "meeting_user",
                    "meeting_user_ids",
                    ["user_id", "group_ids", "structure_level_ids"],
                ),
                ("group", "group_ids", ["name"]),
                ("structure_level", "structure_level_ids", ["name"]),
                ("point_of_order_category", "point_of_order_category_ids", ["text"]),
            ]
            if (ids := target_meeting.get(from_field, []))
        ]
        if gmrs:
            target_meeting_models = self.datastore.get_many(gmrs)
        else:
            target_meeting_models = {}
        muser_matches, unmatched_muser_ids = self.match_by_field_content(
            "user_id", origin_musers, target_meeting_models.get("meeting_user", {})
        )
        group_matches, unmatched_group_ids = self.match_by_field_content(
            "name", origin_groups, target_meeting_models.get("group", {})
        )
        structure_level_matches, unmatched_structure_level_ids = (
            self.match_by_field_content(
                "name",
                origin_structure_levels,
                target_meeting_models.get("structure_level", {}),
            )
        )
        pooc_matches, unmatched_pooc_ids = self.match_by_field_content(
            "text",
            origin_poocs,
            target_meeting_models.get("point_of_order_category", {}),
        )
        if unmatched_pooc_ids:
            pooc_payloads = [
                {
                    "meeting_id": target_meeting_id,
                    **{
                        field: origin_poocs[id_][field]
                        for field in TRANSFERRABLE_POOC_FIELDS
                    },
                }
                for id_ in unmatched_pooc_ids
            ]
            new_poocs = self.execute_other_action(
                PointOfOrderCategoryCreate, pooc_payloads
            )
            assert new_poocs is not None
            for pooc, payload, origin_id in zip(
                new_poocs, pooc_payloads, unmatched_pooc_ids
            ):
                assert pooc is not None
                pooc_matches[origin_id] = pooc["id"]
                target_meeting_models["point_of_order_category"][pooc["id"]] = {
                    **pooc,
                    **payload,
                }
        if unmatched_group_ids:
            group_payloads = [
                {"meeting_id": target_meeting_id, "name": origin_groups[id_]["name"]}
                for id_ in unmatched_group_ids
            ]
            new_groups = self.execute_other_action(GroupCreate, group_payloads)
            assert new_groups is not None
            for group, payload, origin_id in zip(
                new_groups, group_payloads, unmatched_group_ids
            ):
                assert group is not None
                group_matches[origin_id] = group["id"]
                target_meeting_models["group"][group["id"]] = {**group, **payload}
        unmatched_meeting_users = {
            id_: origin_musers[id_] for id_ in unmatched_muser_ids
        }
        relevant_structure_level_ids_set = {
            id_
            for meeting_user in unmatched_meeting_users.values()
            for id_ in meeting_user.get("structure_level_ids", [])
        }
        relevant_structure_level_ids_set.update(
            {sllos["structure_level_id"] for sllos in origin_sllos.values()}
        )
        relevant_unmatched_structure_level_ids_set = (
            relevant_structure_level_ids_set.intersection(unmatched_structure_level_ids)
        )
        if relevant_unmatched_structure_level_ids_set:
            relevant_unmatched_structure_level_ids: list[int] = sorted(
                relevant_unmatched_structure_level_ids_set
            )
            structure_level_payloads = [
                {
                    "meeting_id": target_meeting_id,
                    **{
                        field: val
                        for field in TRANSFERRABLE_STRUCTURE_LEVEL_FIELDS
                        if (val := origin_structure_levels[id_].get(field))
                    },
                }
                for id_ in relevant_unmatched_structure_level_ids
            ]
            new_structure_levels = self.execute_other_action(
                StructureLevelCreateAction, structure_level_payloads
            )
            assert new_structure_levels is not None
            for structure_level, payload, origin_id in zip(
                new_structure_levels,
                structure_level_payloads,
                relevant_unmatched_structure_level_ids,
            ):
                assert structure_level is not None
                structure_level_matches[origin_id] = structure_level["id"]
                target_meeting_models["structure_level"][structure_level["id"]] = {
                    **structure_level,
                    **payload,
                }
        if unmatched_muser_ids:
            muser_payloads = [
                {
                    "meeting_id": target_meeting_id,
                    "user_id": origin_musers[id_]["user_id"],
                    "group_ids": [
                        *target_meeting_models.get("meeting_user", {})
                        .get(muser_matches.get(id_, 0), {})
                        .get("group_ids", []),
                        *[
                            group_matches[group_id]
                            for group_id in origin_musers[id_].get("group_ids", [])
                            if group_matches[group_id]
                            not in target_meeting_models.get("meeting_user", {})
                            .get(muser_matches.get(id_, 0), {})
                            .get("group_ids", [])
                        ],
                    ],
                    **(
                        {}
                        if target
                        else {
                            "structure_level_ids": [
                                structure_level_matches[structure_level_id]
                                for structure_level_id in origin_musers[id_].get(
                                    "structure_level_ids", []
                                )
                            ],
                            **{
                                field: val
                                for field in TRANSFERRABLE_MEETING_USER_FIELDS
                                if (val := origin_musers.get(id_,{}).get(field))
                            },
                        }
                    ),
                }
                for id_, target in [*muser_matches.items(), *[(mu_id, None) for mu_id in unmatched_muser_ids]]
            ]
            new_musers = self.execute_other_action(MeetingUserSetData, muser_payloads)
            assert new_musers is not None
            for muser, payload, origin_id in zip(
                new_musers, muser_payloads, unmatched_muser_ids
            ):
                assert muser is not None
                muser_matches[origin_id] = muser["id"]
                target_meeting_models["meeting_user"][muser["id"]] = {
                    **muser,
                    **payload,
                }
        return (muser_matches, group_matches, structure_level_matches, pooc_matches)

    def get_gmr_list_with_mediafile_child_gmr(
        self,
        last_loaded_mediafiles: dict[int, dict[str, Any]],
        all_loaded_mediafiles: dict[int, dict[str, Any]],
    ) -> list[GetManyRequest]:
        mediafile_ids = {
            child_id
            for mediafile in last_loaded_mediafiles.values()
            for child_id in mediafile.get("child_ids", [])
        }
        mediafile_ids = mediafile_ids - set(all_loaded_mediafiles)
        if mediafile_ids:
            return [
                GetManyRequest(
                    "mediafile",
                    list(mediafile_ids),
                    MEDIAFILE_FIELDS,
                )
            ]
        return []

    def get_gmr_list_from_relation_field(
        self,
        collection: str,
        fields: list[str],
        from_data: dict[int, dict[str, Any]],
        from_field: str,
        is_list_field: bool = False,
    ) -> list[GetManyRequest]:
        if is_list_field:
            id_set = {
                id_ for model in from_data.values() for id_ in model.get(from_field, [])
            }
        else:
            id_set = {
                id_ for model in from_data.values() if (id_ := model.get(from_field))
            }
        if id_set:
            return [GetManyRequest(collection, list(id_set), fields)]
        return []

    def match_by_field_content(
        self,
        match_field: str,
        origin_meeting_data: dict[int, dict[str, Any]],
        target_meeting_data: dict[int, dict[str, Any]],
    ) -> tuple[dict[int, int], list[int]]:
        """
        Matches origin meeting collection data to matching targed meeting data.
        Returns a origin-meeting-model-id to target-meeting-model-id dict for the matches and a list of non-matched ids
        """
        target_match_to_id = {
            model[match_field]: id_ for id_, model in target_meeting_data.items()
        }
        matches = {
            id_: target_id
            for id_, model in origin_meeting_data.items()
            if (target_id := target_match_to_id.get(model[match_field]))
        }
        return (matches, list(set(origin_meeting_data) - set(matches)))
