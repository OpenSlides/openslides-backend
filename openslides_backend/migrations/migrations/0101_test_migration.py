from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.data.mig_0100_resulting_models import (
    Assignment as PrevAssignment,
)
from openslides_backend.migrations.data.mig_0100_resulting_models import (
    Meeting as PrevMeeting,
)
from openslides_backend.migrations.data.mig_0100_resulting_models import (
    MeetingUser as PrevMeetingUser,
)
from openslides_backend.migrations.data.mig_0100_resulting_models import (
    model_registry as prev_model_registry,
)
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.migration_models import (
    MigrationModelCreateUpdate,
    MigrationModelDelete,
    MigrationModelRegistry,
)
from openslides_backend.migrations.migrations.base import BaseMigration
from openslides_backend.models import fields

registry_class_instance = MigrationModelRegistry(prev_model_registry)


class CreateModel(MigrationModelCreateUpdate):
    _migration_registry = registry_class_instance


class DeleteModel(MigrationModelDelete):
    _migration_registry = registry_class_instance


# newly created
class AssignmentCategory(CreateModel):
    collection = "assignment_category"
    verbose_name = "assignment category"

    name = fields.CharField(required=True)
    prefix = fields.CharField()
    weight = fields.IntegerField(default=10000)
    level = fields.IntegerField(
        read_only=True, constraints={"description": "Calculated field."}
    )
    sequential_number = fields.IntegerField(
        required=True,
        read_only=True,
        constant=True,
        constraints={
            "sequence_scope": "meeting_id",
            "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.",
        },
    )
    parent_id = fields.RelationField(to={"assignment_category": "child_ids"})
    child_ids = fields.RelationListField(
        to={"assignment_category": "parent_id"}, is_view_field=True
    )
    assignment_ids = fields.RelationListField(
        to={"assignment": "category_id"}, is_view_field=True
    )
    meeting_id = fields.RelationField(
        to={"meeting": "assignment_category_ids"}, required=True, constant=True
    )


# updated
class Meeting(PrevMeeting):
    assignment_category_ids = fields.RelationListField(
        to={"assignment_category": "meeting_id"},
        on_delete=fields.OnDelete.CASCADE,
        is_view_field=True,
    )

    # Rename motions_number_type to motions_assignments_number_type
    motions_assignments_number_type = fields.CharField(
        default="per_category",
        constraints={"enum": ["per_category", "serially_numbered", "manually"]},
    )
    motions_number_type = None  # type: ignore
    # relations to deleted models
    assignment_candidate_ids = None  # type: ignore


class Assignment(PrevAssignment):
    category_id = fields.RelationField(to={"assignment_category": "motion_ids"})
    # relations to deleted models
    candidate_ids = None  # type: ignore


class MeetingUser(PrevMeetingUser):
    # relations to deleted models
    assignment_candidate_ids = None  # type: ignore


# deleted
class AssignmentCandidate(DeleteModel):
    collection = "assignment_candidate"


model_registry = registry_class_instance.get_model_registry()


class Migration(BaseMigration):
    ORIGIN_COLLECTIONS = [
        "meeting",
        "assignment",
        "meeting_user",
        "assignment_candidate",
    ]
    RESULTING_MODEL_REGISTRY = model_registry
    PREVIOUS_MODEL_REGISTRY = prev_model_registry

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        MigrationHelper.rename_field(curs, "meeting", "motions_number_type", "motions_assignments_number_type")
        MigrationHelper.delete_collection(curs, "assignment_candidate")
        MigrationHelper.create_collection(curs, "assignment_category")
        # relations to deleted models
        # MigrationHelper.delete_field(curs, "meeting", "assignment_candidate_ids")
        # MigrationHelper.delete_field(curs, "assignment", "candidate_ids")
        # MigrationHelper.delete_field(curs, "meeting_user", "assignment_candidate_ids")

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow]) -> None:
        pass

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        pass
