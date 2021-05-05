from ....shared.exceptions import PermissionDenied
from ....shared.patterns import Collection, FullQualifiedId
from ...action import Action


class PermissionMixin(Action):
    def check_anonymous_and_user_in_meeting(self, meeting_id: int) -> None:
        if self.auth.is_anonymous(self.user_id):
            raise PermissionDenied(f"Anonymous user cannot do {self.name}.")

        user = self.datastore.get(
            FullQualifiedId(Collection("user"), self.user_id), ["meeting_ids"]
        )
        if meeting_id not in user.get("meeting_ids", []):
            raise PermissionDenied("User not associated with meeting.")
