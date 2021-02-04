from typing import Any, Dict, Optional, Union

from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...action import BaseAction


class SetNumberMixin(BaseAction):
    def set_number(
        self,
        instance: Dict[str, Any],
        meeting_id: int,
        state_id: int,
        lead_motion_id: Optional[int],
        category_id: Optional[int],
        existing_number: Optional[str] = None,
        existing_number_value: Optional[int] = None,
    ) -> None:
        """
        Sets the motion number and the motion number value.
        """
        # Conditions to stop generate an automatic number.
        if instance.get("number"):
            if not self._check_if_unique(instance["number"], meeting_id):
                raise ActionException("Number is not unique.")
            return
        if existing_number:
            return
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["motions_number_type", "motions_number_min_digits"],
        )
        if meeting.get("motions_number_type") == "manually":
            return
        state = self.datastore.get(
            FullQualifiedId(Collection("motion_state"), state_id), ["set_number"]
        )
        if not state.get("set_number"):
            return

        # Generate the components of the number
        prefix = self._get_prefix(meeting_id, lead_motion_id, category_id)
        number_value = self._get_number_value(
            meeting_id, lead_motion_id, category_id, existing_number_value
        )

        # Generate test number and check uniqueness
        number_value_str = str(number_value).rjust(
            meeting.get("motions_number_min_digits", 0), "0"
        )
        number = f"{prefix}{number_value_str}"
        while not self._check_if_unique(number, meeting_id):
            number_value += 1
            number_value_str = str(number_value).rjust(
                meeting.get("motions_number_min_digits", 0), "0"
            )
            number = f"{prefix}{number_value_str}"

        instance["number"] = number
        instance["number_value"] = number_value

    def _get_prefix(
        self, meeting_id: int, lead_motion_id: Optional[int], category_id: Optional[int]
    ) -> str:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id),
            ["motions_number_with_blank", "motions_amendments_prefix"],
        )
        blank = " " if meeting.get("motions_number_with_blank") else ""
        if lead_motion_id:
            lead_motion = self.datastore.get(
                FullQualifiedId(Collection("motion"), lead_motion_id), ["number"]
            )
            prefix = f"{lead_motion.get('number', '')}{blank}{meeting.get('motions_amendments_prefix', '')}"
        elif not category_id:
            prefix = ""
        else:
            category = self.datastore.get(
                FullQualifiedId(Collection("motion_category"), category_id), ["prefix"]
            )
            if category.get("prefix"):
                prefix = f"{category['prefix']}{blank}"
            else:
                prefix = ""
        return prefix

    def _get_number_value(
        self,
        meeting_id: int,
        lead_motion_id: Optional[int],
        category_id: Optional[int],
        existing_number_value: Optional[int],
    ) -> int:
        if existing_number_value:
            return existing_number_value

        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id), ["motions_number_type"]
        )
        if lead_motion_id:
            filter: Union[And, FilterOperator] = FilterOperator(
                "lead_motion_id", "=", lead_motion_id
            )
        elif meeting.get("motions_number_type") == "per_category":
            filter = And(
                FilterOperator("category_id", "=", category_id),
                FilterOperator("meeting_id", "=", meeting_id),
            )
        else:
            filter = And(
                FilterOperator("meeting_id", "=", meeting_id),
                FilterOperator("lead_motion_id", "=", None),
            )
        filter = And(filter, FilterOperator("meta_deleted", "=", False))
        max_result = self.datastore.max(Collection("motion"), filter, "number_value")
        if max_result.get("max"):
            return max_result["max"] + 1
        return 1

    def _check_if_unique(self, number: str, meeting_id: int) -> bool:
        filter = And(
            FilterOperator("meeting_id", "=", meeting_id),
            FilterOperator("number", "=", number),
            FilterOperator("meta_deleted", "=", False),
        )
        exists_result = self.datastore.exists(
            collection=Collection("motion"), filter=filter
        )
        return not exists_result.get("exists")
