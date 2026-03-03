from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from ....models.models import Motion, MotionCategory
from ....permissions.permissions import Permissions
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...action import ActionData
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion_category.number_motions")
class MotionCategoryNumberMotions(UpdateAction):
    """
    Action to number motions for a category.
    """

    model = Motion()
    schema = DefaultSchema(MotionCategory()).get_default_schema(
        title="Number motions of a motion category.",
        description="An object containing an array of main category id.",
        required_properties=["id"],
    )
    permission = Permissions.Motion.CAN_MANAGE
    permission_model = MotionCategory()
    history_information = "Number set"

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            self.init_memory(instance["id"])

            affected_categories = self.get_affected_categories(instance["id"])
            affected_motions = self.get_affected_motions(affected_categories)
            non_affected_motion_ids = [
                id for id in self.mem_motions if id not in affected_motions
            ]
            non_affected_numbers = [
                self.mem_motions[id].get("number") for id in non_affected_motion_ids
            ]

            # check for missing lead_motion_ids in affected_motions.
            for motion_id in affected_motions:
                lead_motion_id = self.get_lead_motion_id(motion_id)
                if lead_motion_id and lead_motion_id not in affected_motions:
                    raise ActionException(
                        f'Amendment "{motion_id}" cannot be numbered, because it\'s lead motion ({lead_motion_id}) is not in category {instance["id"]} or any subcategory.'
                    )

            # generate number_value_map with the number_values for motion_ids.
            main_counter = 1
            lead_motions_counter: dict[int, int] = defaultdict(lambda: 1)
            number_value_map: dict[int, int] = dict()
            for motion_id in affected_motions:
                lead_motion_id = self.get_lead_motion_id(motion_id)
                if lead_motion_id:
                    number_value_map[motion_id] = lead_motions_counter[lead_motion_id]
                    lead_motions_counter[lead_motion_id] += 1
                else:
                    number_value_map[motion_id] = main_counter
                    main_counter += 1

            for motion_id in affected_motions:
                number, number_value = self.get_number(motion_id, number_value_map)
                if number in non_affected_numbers:
                    raise ActionException(
                        f'Numbering aborted because the motion identifier "{number}" already exists.'
                    )

                yield {
                    "id": motion_id,
                    "number": number,
                    "number_value": number_value,
                    "last_modified": datetime.now(ZoneInfo("UTC")),
                }

    def init_memory(self, main_category_id: int) -> None:
        """Preload all categories with needed fields, all motions with needed fields
        and meeting with needed fields."""
        category = self.datastore.get(
            fqid_from_collection_and_id("motion_category", main_category_id),
            ["meeting_id"],
        )
        self.main_category_id = main_category_id

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", category["meeting_id"]),
            [
                "motion_ids",
                "motion_category_ids",
                "motions_number_with_blank",
                "motions_number_min_digits",
                "motions_amendments_prefix",
            ],
        )
        self.meeting = meeting

        gmr_categories = GetManyRequest(
            "motion_category",
            meeting.get("motion_category_ids", []),
            ["prefix", "parent_id", "child_ids", "weight", "motion_ids"],
        )
        gmr_motions = GetManyRequest(
            "motion",
            meeting.get("motion_ids", []),
            [
                "lead_motion_id",
                "category_weight",
                "category_id",
                "number",
            ],
        )
        result = self.datastore.get_many([gmr_categories, gmr_motions])
        self.mem_categories = result.get("motion_category", {})
        self.mem_motions = result.get("motion", {})
        self.mem_meetings = {category.get("meeting_id"): meeting}

    def get_prefix(self, category_id: int) -> str:
        """Get the prefix of a category. If none, get the prefix of the parent if exists."""
        category = self.mem_categories.get(category_id, {})
        if category.get("prefix"):
            return category["prefix"]
        elif (not category.get("parent_id")) or category_id == self.main_category_id:
            return ""
        else:
            return self.get_prefix(category["parent_id"])

    def get_lead_motion_id(self, motion_id: int) -> int | None:
        """Helper to get the lead_motions_id."""
        motion = self.mem_motions.get(motion_id, {})
        return motion.get("lead_motion_id")

    def get_affected_categories(self, category_id: int) -> list[int]:
        """Get all affected categories, inits and calls the helper."""
        affected_categories: list[int] = []
        queue = [category_id]
        self.helper_affected_categories(queue, affected_categories)
        return affected_categories

    def helper_affected_categories(
        self, queue: list[int], aff_categories: list[int]
    ) -> None:
        """Fill the aff_categories, tree walk by level."""
        if not queue:
            return
        aff_categories.append(queue[0])
        category = self.mem_categories.get(queue[0], {})
        queue.extend(self.sort_category_children(category.get("child_ids", [])))
        self.helper_affected_categories(queue[1:], aff_categories)

    def sort_category_children(self, child_ids: list[int]) -> list[int]:
        """Sort the categories by weight. Important for the helper_affected_categories."""
        weighted_child_ids = []
        for id in child_ids:
            category = self.mem_categories.get(id, {})
            weighted_child_ids.append((category.get("weight"), id))
        weighted_child_ids.sort()
        return [id for (_, id) in weighted_child_ids]

    def get_affected_motions(self, category_ids: list[int]) -> list[int]:
        """Get the affected motions from the categories"""
        affected_motions = []
        for category_id in category_ids:
            category = self.mem_categories.get(category_id, {})
            affected_motions.extend(self.sort_motions(category.get("motion_ids", [])))
        return affected_motions

    def sort_motions(self, ids: list[int]) -> list[int]:
        """Sort motions by category_weight."""
        weighted_motion_ids = []
        for id in ids:
            motion = self.mem_motions.get(id, {})
            weighted_motion_ids.append((motion.get("category_weight"), id))
        weighted_motion_ids.sort()
        return [id for (_, id) in weighted_motion_ids]

    def get_number(
        self, motion_id: int, number_value_map: dict[int, int]
    ) -> tuple[str, int]:
        """Get number, uses the number_value_map, two main cases."""
        lead_motion_id = self.get_lead_motion_id(motion_id)
        if lead_motion_id:
            lead_number, _ = self.get_number(lead_motion_id, number_value_map)
            meeting = self.meeting
            blank = " " if meeting.get("motions_number_with_blank") else ""
            amendments_prefix = meeting.get("motions_amendments_prefix", "")
            number_value_str = str(number_value_map[motion_id]).rjust(
                meeting.get("motions_number_min_digits", 0), "0"
            )
            number = f"{lead_number}{blank}{amendments_prefix}{blank}{number_value_str}"
        else:
            motion = self.mem_motions.get(motion_id, {})
            if motion.get("category_id"):
                prefix = self.get_prefix(motion["category_id"])
            else:
                prefix = ""
            meeting = self.meeting
            blank = " " if meeting.get("motions_number_with_blank") else ""
            number_value_str = str(number_value_map[motion_id]).rjust(
                meeting.get("motions_number_min_digits", 0), "0"
            )
            number = f"{prefix}{blank}{number_value_str}"
        return number, number_value_map[motion_id]
