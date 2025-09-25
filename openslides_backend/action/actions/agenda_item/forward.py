from typing import Any, cast

from ....models.models import AgendaItem
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.schema import id_list_schema
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
from ..meeting_mediafile.create import MeetingMediafileCreate
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
    "parent_id",
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
TRANSFERRABLE_TOPIC_FIELDS = [
    "title",
    "text",
    "attachment_meeting_mediafile_ids",
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
    use_meeting_ids_for_archived_meeting_check = True

    def get_meeting_id(self, instance: dict[str, Any]) -> int:
        if origin_item_ids := instance.get("agenda_item_ids"):
            return self.datastore.get(
                fqid_from_collection_and_id("agenda_item", origin_item_ids[0]),
                ["meeting_id"],
            )["meeting_id"]
        elif origin_item_ids == []:
            raise ActionException(
                "Cannot forward an agenda without the agenda_item_ids."
            )
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

        data = self.load_and_check_data(
            origin_item_ids,
            target_meeting_ids,
            with_speakers=instance.get("with_speakers", False),
            with_moderator_notes=instance.get("with_moderator_notes", False),
            with_attachments=instance.get("with_attachments", False),
        )

        tree_list: list[TreeNode] = self.calculate_agenda_item_related_data_tree_list(
            data
        )

        for meeting_id in target_meeting_ids:
            yield from self.get_updated_instances_for_meeting(
                meeting_id,
                data["meeting"][meeting_id],
                tree_list,
                data.get("meeting_mediafile", {}),
                data.get("mediafile", {}),
                data.get("meeting_user", {}),
                data.get("group", {}),
                data.get("structure_level", {}),
                data.get("point_of_order_category", {}),
                data.get("structure_level_list_of_speakers", {}),
            )

    def load_and_check_data(
        self,
        origin_item_ids: list[int],
        target_meeting_ids: list[int],
        with_speakers: bool,
        with_moderator_notes: bool,
        with_attachments: bool,
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Loads all data directly relevant to the forwarding.
        Only exception is agenda_item ancestry data.

        Checks all data that can be checked at this stage.
        """
        data = self.datastore.get_many(
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
        )

        self.meeting_id = data["agenda_item"][next(iter(data["agenda_item"]))][
            "meeting_id"
        ]
        self.check_agenda_items_and_meeting_ids(data["agenda_item"], target_meeting_ids)

        data.update(
            self.get_all_topic_and_meeting_data(target_meeting_ids, data["agenda_item"])
        )

        if not data["meeting"][self.meeting_id].get("is_active_in_organization_id"):
            raise ActionException("Cannot forward if origin meeting is archived.")

        self.check_committee_forwarding_settings(data["meeting"])

        data.update(
            self.get_all_meeting_mediafile_and_los_data(
                data["topic"],
                with_speakers,
                with_moderator_notes,
                with_attachments,
            )
        )

        data.update(
            self.get_direct_mediafile_and_all_speaker_and_sllos_data(
                data.get("meeting_mediafile", {}), data.get("list_of_speakers", {})
            )
        )

        self.check_speaker_data(data.get("speaker", {}))

        new_data = self.get_mediafile_children_and_all_meeting_users_and_poocs(
            data.get("mediafile", {}), data.get("speaker", {})
        )

        new_mediafiles = new_data.get("mediafile", {})
        if new_mediafiles:
            data["mediafile"].update(new_mediafiles)
            del new_data["mediafile"]
        data.update(new_data)

        new_data = self.get_mediafile_grandchildren_and_all_groups_and_structure_levels(
            new_mediafiles,
            data.get("mediafile", {}),
            data.get("meeting_user", {}),
            data.get("structure_level_list_of_speakers", {}),
        )

        new_mediafiles = new_data.get("mediafile", {})
        if new_mediafiles:
            data["mediafile"].update(new_mediafiles)
            del new_data["mediafile"]
        data.update(new_data)

        self.load_remaining_mediafile_descendants(data, new_mediafiles)
        return data

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
        """
        Creates all data pertaining the meeting.
        Id-order of the created agenda_items will not be the same as
        for the origin agenda items. See get_updated_instances_from_tree_node
        for more information.

        Yields a { "id": <agenda_item_id> } dict for every thus-created agenda_item
        """
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
            target_meeting_id, origin_mediafiles, target_meeting
        )
        max_weight = (
            self.datastore.max(
                "agenda_item",
                FilterOperator("meeting_id", "=", target_meeting_id),
                "weight",
                use_changed_models=False,
            )
            or 0
        )
        yield from self.get_updated_instances_from_tree_node(
            target_meeting_id,
            max_weight,
            origin_tree_list,
            muser_matches,
            structure_level_matches,
            pooc_matches,
            mediafile_matches,
            origin_meeting_mediafiles,
        )

    def get_updated_instances_from_tree_node(
        self,
        target_meeting_id: int,
        max_meeting_agenda_weight: int,
        origin_tree_list: list[TreeNode],
        muser_matches: dict[int, int],
        structure_level_matches: dict[int, int],
        pooc_matches: dict[int, int],
        mediafile_matches: dict[int, int],
        origin_meeting_mediafiles: dict[int, dict[str, Any]],
        parent_id: int | None = None,
    ) -> ActionData:
        """
        Creates all non-meeting-wide agenda_item-specific data (agenda_items,
        topics, los, sllos, speakers) from the info in the origin_tree_list.
        It does this by first creating them all for the root-level items of
        the origin_tree list, then continuing to recursively call itself for
        the child node lists of each of the nodes.
        So the data for A->[B->[C,D], E->[F]], G, H->[I,J]
        will be created in the order (A,G,H),(B,E),(C,D),(F),(I,J).

        Yields a { "id": <agenda_item_id> } dict for every thus-created agenda_item
        """
        topic_id_to_tree_node = self.create_topics(
            target_meeting_id,
            max_meeting_agenda_weight,
            origin_tree_list,
            mediafile_matches,
            origin_meeting_mediafiles,
            parent_id,
        )
        new_topics = self.datastore.get_many(
            [
                GetManyRequest(
                    "topic",
                    list(topic_id_to_tree_node),
                    ["list_of_speakers_id", "agenda_item_id"],
                )
            ]
        )["topic"]

        self.update_loss(new_topics, topic_id_to_tree_node)

        topic_id_to_old_to_new_sllos_id = self.create_slloss(
            structure_level_matches, new_topics, topic_id_to_tree_node
        )

        self.create_speakers(
            muser_matches,
            pooc_matches,
            new_topics,
            topic_id_to_tree_node,
            topic_id_to_old_to_new_sllos_id,
        )

        for topic_id, tree_node in topic_id_to_tree_node.items():
            agenda_item_id = new_topics[topic_id]["agenda_item_id"]
            yield {"id": agenda_item_id}
            if tree_node[5]:
                yield from self.get_updated_instances_from_tree_node(
                    target_meeting_id,
                    max_meeting_agenda_weight,
                    tree_node[5],
                    muser_matches,
                    structure_level_matches,
                    pooc_matches,
                    mediafile_matches,
                    origin_meeting_mediafiles,
                    agenda_item_id,
                )

    def create_mediafile_meeting_models(
        self,
        target_meeting_id: int,
        origin_mediafiles: dict[int, dict[str, Any]],
        target_meeting: dict[str, Any],
    ) -> dict[int, int]:
        """
        Duplicates all meeting-owned mediafiles to the target meeting.
        """
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
                        and parent_id in origin_to_new_id
                        else {}
                    ),
                }
                for origin_id, id_ in origin_to_new_id.items()
            ]
            mm_payloads = [
                {
                    "meeting_id": target_meeting_id,
                    "mediafile_id": payload["id"],
                    "is_public": False,
                    "inherited_access_group_ids": [target_meeting["admin_group_id"]],
                    "access_group_ids": (
                        [target_meeting["admin_group_id"]]
                        if not payload.get("parent_id")
                        else []
                    ),
                }
                for payload in payloads
            ]
            self.execute_other_action(
                MediafileDuplicateToAnotherMeetingAction, payloads
            )
            self.execute_other_action(MeetingMediafileCreate, mm_payloads)
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

        pooc_matches = self.create_and_update_poocs(
            target_meeting_id,
            target_meeting_models.get("point_of_order_category", {}),
            origin_poocs,
        )

        group_matches = self.create_and_update_groups(
            target_meeting_id, target_meeting_models.get("group", {}), origin_groups
        )

        muser_matches, unmatched_muser_ids = self.match_by_field_content(
            "user_id", origin_musers, target_meeting_models.get("meeting_user", {})
        )
        structure_level_matches = self.create_and_update_structure_levels(
            target_meeting_id,
            target_meeting_models.get("structure_level", {}),
            origin_musers,
            origin_structure_levels,
            origin_sllos,
            unmatched_muser_ids,
        )

        self.create_and_update_meeting_users(
            target_meeting_id,
            target_meeting_models.get("meeting_user", {}),
            origin_musers,
            group_matches,
            structure_level_matches,
            unmatched_muser_ids,
            muser_matches,
        )
        return (muser_matches, group_matches, structure_level_matches, pooc_matches)

    def get_gmr_list_with_mediafile_child_gmr(
        self,
        last_loaded_mediafiles: dict[int, dict[str, Any]],
        all_loaded_mediafiles: dict[int, dict[str, Any]],
    ) -> list[GetManyRequest]:
        """
        For the sake of easily writing expansive GetManyRequest lists,
        this method checks if any of the recently loaded mediafiles have
        yet-unloaded child mediafiles.
        If yes, it returns a list containing a GetManyRequest for these children,
        if not, it returns an empty list.
        """
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
        """
        For the sake of easily writing expansive GetManyRequest lists,
        this method checks if there are any relations to the given collection
        in the given field of any of the given model data.
        If yes, it returns a list containing a GetManyRequest for these relations,
        if not, it returns an empty list.
        """
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

    def calculate_reduced_parentage_dict(
        self, agenda_items: dict[int, Any]
    ) -> dict[int, int | None]:
        """
        Returns a dictionary pointing from all agenda_item ids in the given dict
        to each ones closest ancestor that is also in the list.
        So A->B->C->D->E->F turns into A->C->F if only [A,C,F] are contained in the dict.
        """
        agenda_items = agenda_items.copy()
        agenda_item_ids = list(agenda_items.keys())
        child_id_to_parent_id: dict[int, int | None] = {
            id_: parent_id
            for id_, item in agenda_items.items()
            if (parent_id := item.get("parent_id")) in agenda_item_ids
            or parent_id is None
        }
        child_id_to_curr_parent_id: dict[int, int] = {
            id_: parent_id
            for id_, item in agenda_items.items()
            if (parent_id := item.get("parent_id")) and parent_id not in agenda_item_ids
        }
        while len(child_id_to_curr_parent_id) > 0:
            agenda_items.update(
                self.datastore.get_many(
                    [
                        GetManyRequest(
                            "agenda_item",
                            list(set(child_id_to_curr_parent_id.values())),
                            ["parent_id"],
                        )
                    ]
                )["agenda_item"]
            )
            for id_, curr_parent_id in list(child_id_to_curr_parent_id.items()):
                if (
                    not (parent_id := agenda_items[curr_parent_id].get("parent_id"))
                    or parent_id in agenda_item_ids
                ):
                    child_id_to_parent_id[id_] = parent_id
                    del child_id_to_curr_parent_id[id_]
                else:
                    child_id_to_curr_parent_id[id_] = parent_id
        return child_id_to_parent_id

    def calculate_agenda_item_related_data_tree_list(
        self, data: dict[str, dict[int, dict[str, Any]]]
    ) -> list[TreeNode]:
        """
        Calculates and returns a list of TreeNode items representing the agenda_item tree.
        Skips agenda_items that are not part of the data, instead assigning their
        children to their closest ancestor that is in the data.

        Each TreeNode contains (in that order)
        - a dict with the data of the agenda_item
        - a dict with the data of the topic
        - a dict with the data of the los
        - a list with dicts of the data of the speakers
        - a list with dicts of the data of the sllos
        - a list with dicts of the data of the speakers
        - a list with TreeNodes representing the children of the item.
        """
        child_id_to_parent_id: dict[int, int | None] = (
            self.calculate_reduced_parentage_dict(data["agenda_item"])
        )

        tree_list: list[TreeNode] = []
        id_to_node: dict[int, TreeNode] = {}
        while len(child_id_to_parent_id):
            ids = list(child_id_to_parent_id)
            for id_ in ids:
                if (
                    parent_id := child_id_to_parent_id[id_]
                ) is None or parent_id in id_to_node:
                    item = data["agenda_item"][id_]
                    topic = data["topic"][id_from_fqid(item["content_object_id"])]
                    los = data["list_of_speakers"][topic["list_of_speakers_id"]]
                    speakers = {
                        id_: data["speaker"][id_] for id_ in los.get("speaker_ids", [])
                    }
                    sllos = {
                        id_: data["structure_level_list_of_speakers"][id_]
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
                            for field in TRANSFERRABLE_TOPIC_FIELDS
                            if field in topic
                        },
                        {
                            field: los[field]
                            for field in ["closed", "moderator_notes"]
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
        return tree_list

    def check_agenda_items_and_meeting_ids(
        self, agenda_items: dict[int, dict[str, Any]], target_meeting_ids: list[int]
    ) -> None:
        """
        Checks if
        - The agenda_items are in the same meeting
        - The agenda_items are not a topic
        - The origin meetings id is not in the target_meeting_ids
        based on the class instances meeting id and the given agenda_item data
        """
        for id_, item in agenda_items.items():
            if item["meeting_id"] != self.meeting_id:
                raise ActionException(
                    "Agenda forwarding requires all agenda_items to be part of the same meeting."
                )
            if not item["content_object_id"].startswith("topic/"):
                raise ActionException(
                    f"Cannot forward agenda_item/{id_}: Not linked to a topic."
                )

        if self.meeting_id in target_meeting_ids:
            raise ActionException("Cannot forward agenda to the same meeting")

    def check_committee_forwarding_settings(
        self, meetings: dict[int, dict[str, Any]]
    ) -> None:
        """
        Checks whether the origin meeting can even forward into all the
        target committees.
        """
        origin_committee = self.datastore.get(
            fqid_from_collection_and_id(
                "committee", meetings[self.meeting_id]["committee_id"]
            ),
            ["forward_agenda_to_committee_ids"],
        )
        forbidden_committees = {
            committee_id
            for meeting_id in meetings
            if meeting_id != self.meeting_id
            and (committee_id := meetings[meeting_id]["committee_id"])
            not in origin_committee.get("forward_agenda_to_committee_ids", [])
        }
        if forbidden_committees:
            raise ActionException(
                f"Cannot forward to the following committee(s): {forbidden_committees}"
            )

    def check_speaker_data(self, speakers: dict[int, dict[str, Any]]) -> None:
        for speaker in speakers.values():
            if not speaker.get("end_time"):
                if speaker.get("begin_time"):
                    raise ActionException(
                        "Cannot forward when there are running or paused speakers."
                    )
                if speaker.get("point_of_order"):
                    raise ActionException(
                        "Cannot forward when there are waiting points of order."
                    )

    def get_all_topic_and_meeting_data(
        self, target_meeting_ids: list[int], agenda_items: dict[int, dict[str, Any]]
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Helper function to load data.
        """
        return self.datastore.get_many(
            [
                GetManyRequest(
                    "topic",
                    [
                        id_from_fqid(item["content_object_id"])
                        for item in agenda_items.values()
                    ],
                    [*TRANSFERRABLE_TOPIC_FIELDS, "list_of_speakers_id"],
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
                        "is_active_in_organization_id",
                    ],
                ),
            ]
        )

    def get_all_meeting_mediafile_and_los_data(
        self,
        topics: dict[int, dict[str, Any]],
        with_speakers: bool,
        with_moderator_notes: bool,
        with_attachments: bool,
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Helper function to load data.
        """
        gmrs: list[GetManyRequest] = []
        if with_attachments:
            gmrs = self.get_gmr_list_from_relation_field(
                "meeting_mediafile",
                ["mediafile_id"],
                topics,
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
            gmrs.extend(
                self.get_gmr_list_from_relation_field(
                    "list_of_speakers",
                    los_fields,
                    topics,
                    "list_of_speakers_id",
                )
            )
        return self.datastore.get_many(gmrs)

    def get_direct_mediafile_and_all_speaker_and_sllos_data(
        self,
        meeting_mediafiles: dict[int, dict[str, Any]],
        lists_of_speakers: dict[int, dict[str, Any]],
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Helper function to load data.
        """
        gmrs = [
            *self.get_gmr_list_from_relation_field(
                "mediafile",
                MEDIAFILE_FIELDS,
                meeting_mediafiles,
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
                lists_of_speakers,
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
                lists_of_speakers,
                "structure_level_list_of_speakers_ids",
                is_list_field=True,
            ),
        ]
        if gmrs:
            return self.datastore.get_many(gmrs)
        return {}

    def get_mediafile_children_and_all_meeting_users_and_poocs(
        self,
        mediafiles: dict[int, dict[str, Any]],
        speakers: dict[int, dict[str, Any]],
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Helper function to load data.
        """
        gmrs = [
            *self.get_gmr_list_with_mediafile_child_gmr(mediafiles, mediafiles),
            *self.get_gmr_list_from_relation_field(
                "meeting_user",
                [
                    "user_id",
                    "group_ids",
                    "structure_level_ids",
                    *TRANSFERRABLE_MEETING_USER_FIELDS,
                ],
                speakers,
                "meeting_user_id",
            ),
            *self.get_gmr_list_from_relation_field(
                "point_of_order_category",
                TRANSFERRABLE_POOC_FIELDS,
                speakers,
                "point_of_order_category_id",
            ),
        ]

        if gmrs:
            return self.datastore.get_many(gmrs)
        return {}

    def get_mediafile_grandchildren_and_all_groups_and_structure_levels(
        self,
        last_loaded_mediafiles: dict[int, dict[str, Any]],
        all_mediafiles: dict[int, dict[str, Any]],
        meeting_users: dict[int, dict[str, Any]],
        slloss: dict[int, dict[str, Any]],
    ) -> dict[str, dict[int, dict[str, Any]]]:
        """
        Helper function to load data.
        """
        gmrs = [
            *self.get_gmr_list_with_mediafile_child_gmr(
                last_loaded_mediafiles, all_mediafiles
            ),
            *self.get_gmr_list_from_relation_field(
                "group",
                ["name"],
                meeting_users,
                "group_ids",
                is_list_field=True,
            ),
        ]
        structure_level_id_set = {
            id_
            for meeting_user in meeting_users.values()
            for id_ in meeting_user.get("structure_level_ids", [])
        }
        structure_level_id_set.update(
            {sllos["structure_level_id"] for sllos in slloss.values()}
        )
        if structure_level_id_set:
            gmrs.append(
                GetManyRequest(
                    "structure_level",
                    list(structure_level_id_set),
                    TRANSFERRABLE_STRUCTURE_LEVEL_FIELDS,
                )
            )
        if gmrs:
            return self.datastore.get_many(gmrs)
        return {}

    def load_remaining_mediafile_descendants(
        self,
        data: dict[str, dict[int, dict[str, Any]]],
        new_mediafiles: dict[int, dict[str, Any]],
    ) -> None:
        while len(
            gmrs := self.get_gmr_list_with_mediafile_child_gmr(
                new_mediafiles, data.get("mediafile", {})
            )
        ):
            new_mediafiles = self.datastore.get_many(gmrs).get("mediafile", {})
            data["mediafile"].update(new_mediafiles)

    def create_topics(
        self,
        target_meeting_id: int,
        max_meeting_agenda_weight: int,
        origin_tree_list: list[TreeNode],
        mediafile_matches: dict[int, int],
        origin_meeting_mediafiles: dict[int, dict[str, Any]],
        parent_id: int | None,
    ) -> dict[int, TreeNode]:
        """
        Creates all topics (and automatically agenda_items and los)
        from the root-level info in the origin_tree_list.
        Returns a dict that points from the newly created topic id
        to the TreeNode that provided its data.
        """
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
                    if origin_meeting_mediafiles
                    and (
                        mediafile_ids := [
                            mediafile_matches[
                                origin_meeting_mediafiles[origin_id]["mediafile_id"]
                            ]
                            for origin_id in topic.get(
                                "attachment_meeting_mediafile_ids", []
                            )
                        ]
                    )
                    else {}
                ),
                **{
                    f"agenda_{field}": (
                        val if field != "weight" else val + max_meeting_agenda_weight
                    )
                    for field, val in agenda_item.items()
                },
            }
            for agenda_item, topic, los, speakers, sllos, list_of_children in origin_tree_list
        ]
        topic_results = self.execute_other_action(TopicCreate, topic_payloads)
        assert topic_results is not None
        topic_id_to_tree_node = {
            cast(ActionResultElement, top_res)["id"]: node
            for top_res, node in zip(topic_results, origin_tree_list)
        }
        return topic_id_to_tree_node

    def update_loss(
        self,
        topics: dict[int, dict[str, Any]],
        topic_id_to_tree_node: dict[int, TreeNode],
    ) -> None:
        if topic_id_to_los_data := {
            id_: node[2] for id_, node in topic_id_to_tree_node.items() if node[2]
        }:
            self.execute_other_action(
                ListOfSpeakersUpdateAction,
                [
                    {"id": topics[topic_id]["list_of_speakers_id"], **los}
                    for topic_id, los in topic_id_to_los_data.items()
                ],
            )

    def create_slloss(
        self,
        structure_level_matches: dict[int, int],
        topics: dict[int, dict[str, Any]],
        topic_id_to_tree_node: dict[int, TreeNode],
    ) -> dict[int, dict[int, int]]:
        topic_id_to_old_to_new_sllos_id: dict[int, dict[int, int]] = {}
        if topic_id_to_sllos_data := {
            id_: node[4] for id_, node in topic_id_to_tree_node.items() if node[4]
        }:
            payloads = [
                (
                    topic_id,
                    old_sllos_id,
                    {
                        "initial_time": sllos["initial_time"],
                        "list_of_speakers_id": topics[topic_id]["list_of_speakers_id"],
                        "structure_level_id": structure_level_matches[
                            sllos["structure_level_id"]
                        ],
                    },
                )
                for topic_id, node in topic_id_to_sllos_data.items()
                for old_sllos_id, sllos in node.items()
            ]
            result = self.execute_other_action(
                StructureLevelListOfSpeakersCreateAction,
                [payload for topic_id, old_sllos_id, payload in payloads],
            )
            assert result is not None
            for topiced_payload, res in zip(payloads, result):
                if topiced_payload[0] not in topic_id_to_old_to_new_sllos_id:
                    topic_id_to_old_to_new_sllos_id[topiced_payload[0]] = {}
                topic_id_to_old_to_new_sllos_id[topiced_payload[0]][
                    topiced_payload[1]
                ] = cast(ActionResultElement, res)["id"]
            fields = ["additional_time", "remaining_time"]
            update_payloads = [
                {
                    "id": topic_id_to_old_to_new_sllos_id[topic_id][old_sllos_id],
                    **{
                        field: val
                        for field in fields
                        if (val := sllos.get(field)) is not None
                    },
                }
                for topic_id, node in topic_id_to_sllos_data.items()
                for old_sllos_id, sllos in node.items()
                if any(sllos.get(field) is not None for field in fields)
            ]
            if update_payloads:
                self.execute_other_action(
                    StructureLevelListOfSpeakersUpdateAction, update_payloads
                )
        return topic_id_to_old_to_new_sllos_id

    def create_speakers(
        self,
        muser_matches: dict[int, int],
        pooc_matches: dict[int, int],
        topics: dict[int, dict[str, Any]],
        topic_id_to_tree_node: dict[int, TreeNode],
        topic_id_to_old_to_new_sllos_id: dict[int, dict[int, int]],
    ) -> None:
        if topic_id_to_tree_node_with_speaker_data := {
            id_: node for id_, node in topic_id_to_tree_node.items() if node[3]
        }:
            speaker_payloads = [
                {
                    "meeting_user_id": muser_matches[speaker["meeting_user_id"]],
                    "list_of_speakers_id": topics[topic_id]["list_of_speakers_id"],
                    **(
                        {
                            "structure_level_list_of_speakers_id": topic_id_to_old_to_new_sllos_id[
                                topic_id
                            ][
                                sllos_id
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
                for topic_id, node in topic_id_to_tree_node_with_speaker_data.items()
                for speaker in node[3].values()
            ]
            self.execute_other_action(SpeakerCreateForMerge, speaker_payloads)

    def create_and_update_meeting_users(
        self,
        target_meeting_id: int,
        target_meeting_meeting_users: dict[int, dict[str, Any]],
        origin_musers: dict[int, dict[str, Any]],
        group_matches: dict[int, int],
        structure_level_matches: dict[int, int],
        unmatched_muser_ids: list[int],
        prelim_muser_matches: dict[int, int],
    ) -> None:
        """
        Helper function of create_and_update_non_mediafile_meeting_models.
        Creates and updates the meeting_users,
        updates muser_matches using the result.
        """
        muser_payloads: list[dict[str, Any]] = []
        changed_or_new_muser_ids: list[int] = []
        for id_, target in [
            *prelim_muser_matches.items(),
            *[(mu_id, None) for mu_id in unmatched_muser_ids],
        ]:
            origin_model = origin_musers[id_]
            if target:
                target_model = target_meeting_meeting_users.get(
                    prelim_muser_matches.get(id_, 0), {}
                )
                new_group_ids = [
                    new_group_id
                    for group_id in origin_model.get("group_ids", [])
                    if (new_group_id := group_matches[group_id])
                    not in target_model.get("group_ids", [])
                ]
                if new_group_ids:
                    changed_or_new_muser_ids.append(id_)
                    muser_payloads.append(
                        {
                            "id": target,
                            "group_ids": [
                                *target_model.get("group_ids", []),
                                *new_group_ids,
                            ],
                        }
                    )
            else:
                changed_or_new_muser_ids.append(id_)
                muser_payloads.append(
                    {
                        "meeting_id": target_meeting_id,
                        "user_id": origin_model["user_id"],
                        "group_ids": [
                            group_matches[group_id]
                            for group_id in origin_model.get("group_ids", [])
                        ],
                        "structure_level_ids": [
                            structure_level_matches[structure_level_id]
                            for structure_level_id in origin_model.get(
                                "structure_level_ids", []
                            )
                        ],
                        **{
                            field: val
                            for field in TRANSFERRABLE_MEETING_USER_FIELDS
                            if (val := origin_model.get(field)) is not None
                        },
                    }
                )
        if muser_payloads:
            new_musers = self.execute_other_action(MeetingUserSetData, muser_payloads)
            assert new_musers is not None
            for muser, payload, origin_id in zip(
                new_musers,
                muser_payloads,
                changed_or_new_muser_ids,
            ):
                assert muser is not None
                prelim_muser_matches[origin_id] = muser["id"]
                target_meeting_meeting_users[muser["id"]] = {
                    **muser,
                    **payload,
                }

    def create_and_update_structure_levels(
        self,
        target_meeting_id: int,
        target_meeting_structure_levels: dict[int, dict[str, Any]],
        origin_musers: dict[int, dict[str, Any]],
        origin_structure_levels: dict[int, dict[str, Any]],
        origin_sllos: dict[int, dict[str, Any]],
        unmatched_muser_ids: list[int],
    ) -> dict[int, int]:
        """
        Helper function of create_and_update_non_mediafile_meeting_models.
        Creates and updates the structure_levels,
        returns structure_level_matches.
        """
        unmatched_meeting_users = {
            id_: origin_musers[id_] for id_ in unmatched_muser_ids
        }
        structure_level_matches, unmatched_structure_level_ids = (
            self.match_by_field_content(
                "name",
                origin_structure_levels,
                target_meeting_structure_levels,
            )
        )
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
                target_meeting_structure_levels[structure_level["id"]] = {
                    **structure_level,
                    **payload,
                }
        return structure_level_matches

    def create_and_update_groups(
        self,
        target_meeting_id: int,
        target_meeting_groups: dict[int, dict[str, Any]],
        origin_groups: dict[int, dict[str, Any]],
    ) -> dict[int, int]:
        """
        Helper function of create_and_update_non_mediafile_meeting_models.
        Creates and updates the groups,
        returns group_matches.
        """
        group_matches, unmatched_group_ids = self.match_by_field_content(
            "name", origin_groups, target_meeting_groups
        )
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
                target_meeting_groups[group["id"]] = {**group, **payload}
        return group_matches

    def create_and_update_poocs(
        self,
        target_meeting_id: int,
        target_meeting_poocs: dict[int, dict[str, Any]],
        origin_poocs: dict[int, dict[str, Any]],
    ) -> dict[int, int]:
        """
        Helper function of create_and_update_non_mediafile_meeting_models.
        Creates and updates the poocs,
        returns pooc_matches.
        """
        pooc_matches, unmatched_pooc_ids = self.match_by_field_content(
            "text",
            origin_poocs,
            target_meeting_poocs,
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
                target_meeting_poocs[pooc["id"]] = {**pooc, **payload}
        return pooc_matches
