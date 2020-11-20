from ...models.models import MotionCommentSection
from ...services.datastore.commands import GetManyRequest
from ...shared.exceptions import ActionException, ProtectedModelsException
from ...shared.patterns import Collection
from ..base import ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("motion_comment_section.delete")
class MotionCommentSectionDeleteAction(DeleteAction):
    """
    Delete Action with check for empty comments.
    """

    model = MotionCommentSection()
    schema = DefaultSchema(MotionCommentSection()).get_delete_schema()

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        try:
            return self.delete_action_prepare_dataset(payload)
        except ProtectedModelsException as e:
            comment_ids = [fqid.id for fqid in e.fqids]
            get_many_request = GetManyRequest(
                Collection("motion_comment"), comment_ids, ["motion_id"]
            )
            gm_result = self.datastore.get_many([get_many_request])
            comments = gm_result.get(Collection("motion_comment"), {})

            motions = set(
                f'"{instance["motion_id"]}"' for instance in comments.values()
            )

            count = len(motions)
            motions_verbose = ", ".join(list(motions)[:3])
            if count > 3:
                motions_verbose += ", .."

            if count == 1:
                msg = f"This section has still comments in motion {motions_verbose}."
            else:
                msg = f"This section has still comments in motions {motions_verbose}."
            msg += " Please remove all comments before deletion."
            raise ActionException(msg)
