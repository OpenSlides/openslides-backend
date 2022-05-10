from typing import Any, Dict

import fastjsonschema

from ..action.actions.meeting.export_helper import export_meeting
from ..models.fields import (
    TemplateCharField,
    TemplateDecimalField,
    TemplateHTMLStrictField,
    TemplateRelationListField,
)
from ..models.models import User
from ..permissions.management_levels import OrganizationManagementLevel
from ..permissions.permission_helper import has_organization_management_level
from ..services.datastore.commands import GetManyRequest
from ..shared.exceptions import PermissionDenied
from ..shared.patterns import Collection
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

export_meeting_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "export meeting",
        "description": "export meeting",
        "properties": {
            "meeting_id": required_id_schema,
        },
    }
)


@register_presenter("export_meeting")
class Export(BasePresenter):
    """
    Export meeting presenter.
    It calls the export meeting function and should be used by the superadmin.
    """

    schema = export_meeting_schema

    def get_result(self) -> Any:
        # check permissions
        if not has_organization_management_level(
            self.datastore, self.user_id, OrganizationManagementLevel.SUPERADMIN
        ):
            msg = "You are not allowed to perform presenter export_meeting."
            msg += f" Missing permission: {OrganizationManagementLevel.SUPERADMIN}"
            raise PermissionDenied(msg)
        export_data = export_meeting(self.datastore, self.data["meeting_id"])
        self.exclude_organization_tags_and_default_meeting_for_committee(export_data)
        self.add_users(export_data, self.data["meeting_id"])
        return export_data

    def exclude_organization_tags_and_default_meeting_for_committee(
        self, export_data: Dict[str, Any]
    ) -> None:
        self.get_meeting_from_json(export_data)["organization_tag_ids"] = None
        self.get_meeting_from_json(export_data)[
            "default_meeting_for_committee_id"
        ] = None

    def add_users(self, export_data: Dict[str, Any], meeting_id: int) -> None:
        user_ids = self.get_meeting_from_json(export_data)["user_ids"]
        if not user_ids:
            return
        fields = []
        for field in User().get_fields():
            if isinstance(
                field,
                (
                    TemplateCharField,
                    TemplateHTMLStrictField,
                    TemplateDecimalField,
                    TemplateRelationListField,
                ),
            ):
                fields.append(
                    (
                        field.get_structured_field_name(meeting_id),
                        field.get_template_field_name(),
                    )
                )

        gmr = GetManyRequest(
            Collection("user"),
            user_ids,
            [
                "id",
                "username",
                "pronoun",
                "title",
                "first_name",
                "last_name",
                "is_active",
                "is_physical_person",
                "password",
                "default",
                "can_change_own_password",
                "gender",
                "email",
                "default_number",
                "default_structure_level",
                "default_vote_weight",
                "last_email_send",
                "is_demo_user",
                "organization_management_level",
                "is_present_in_meeting_ids",
            ]
            + [field_pair[0] for field_pair in fields],
        )
        users: Any = self.datastore.get_many([gmr])[Collection("user")]
        # remove meta_* keys
        users = {
            key: {
                key_inner: value_inner
                for key_inner, value_inner in value.items()
                if not key_inner.startswith("meta_")
            }
            for key, value in users.items()
        }

        for user_key in users:
            for field_name, field_template_name in fields:
                if users[user_key].get(field_name):
                    users[user_key][field_name] = users[user_key].get(field_name)
                    users[user_key][field_template_name] = [str(meeting_id)]
            users[user_key]["meeting_ids"] = [meeting_id]
            if meeting_id in (users[user_key].get("is_present_in_meeting_ids") or []):
                users[user_key]["is_present_in_meeting_ids"] = [meeting_id]
            else:
                users[user_key]["is_present_in_meeting_ids"] = None

        export_data["user"] = users

    def get_meeting_from_json(self, export_data: Any) -> Any:
        key = next(iter(export_data["meeting"]))
        return export_data["meeting"][key]
