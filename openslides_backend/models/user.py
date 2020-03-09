from ..shared.patterns import Collection
from . import fields
from .base import Model


class User(Model):
    """
    Model for users.
    """

    collection = Collection("user")
    verbose_name = "user"

    id = fields.IdField(description="The id of this user.")


#     is_active # Systemweites deaktivieren eines Benutzers
#     username = fields.RequiredCharField(description="The username of this user.")
#     title: string;
#     first_name: string;
#     last_name: string;
#     structure_level: string;
#     gender: string;
#
#     number: string;
#     email: string;
#     last_email_send: number; # Timestamp
#     comment: HTML;
#     about_me: HTML;
#
#     default_password: string;
#     is_committee: boolean;
#
#     role_id: role;
#
#     is_present_in_meeting_ids: meeting[];
#     meeting_id: meeting; // Temporary users
#     guest_meeting_ids: meeting[]; // Links to meeting/guest_ids
#
#
# # Alles Rückreferenzen:
# // All foreign keys are meeting-specific:
# // - Keys are smaller (Space is in O(n^2) for n keys
# //   in the relation), so this saves storagespace
# // - This makes quering things like this possible:
# //   "Give me all groups for User X in Meeting Y" without
# //   the need to get all groups and filter them for the meeting
# group_<meeting_id>_ids: group[];
# personal_note_<meeting_id>_ids: personal_note[];
# projection_<meeting_id>_ids: projection[];
# supported_motion_<meeting_id>_ids: motion[];
# submitted_motion_<meeting_id>_ids: motion_submitter[];
# assignment_related_user_<meeting_id>_ids: assignment_related_user[];
# motion_vote_<meeting_id>_ids: motion_vote[];
# assignment_vote_<meeting_id>_ids: assignment_vote[];
# motion_voted_poll_<meeting_id>_ids: motion_poll[];
# assignment_voted_poll_<meeting_id>_ids: assignment_poll[];
