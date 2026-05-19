# from .migration_models import MigrationModelRegistry
# from .previous_migration import model_registry as prev_registry

# from openslides_backend.models import fields

# model_registry_class = MigrationModelRegistry(prev_registry)

# MigrationModelCreateUpdate, MigrationModelDelete = model_registry_class.get_migration_model_base_classes()

# # newly created
# class AssignmentCategory(MigrationModelCreateUpdate):
#     collection = "assignment_category"
#     verbose_name = "assignment category"
    
#     name = fields.CharField(required=True)
#     prefix = fields.CharField()
#     weight = fields.IntegerField(default=10000)
#     level = fields.IntegerField(
#         read_only=True, constraints={"description": "Calculated field."}
#     )
#     sequential_number = fields.IntegerField(
#         required=True,
#         read_only=True,
#         constant=True,
#         constraints={
#             "sequence_scope": "meeting_id",
#             "description": "The (positive) serial number of this model in its meeting. This number is auto-generated and read-only.",
#         },
#     )
#     parent_id = fields.RelationField(to={"assignment_category": "child_ids"})
#     child_ids = fields.RelationListField(
#         to={"assignment_category": "parent_id"}, is_view_field=True
#     )
#     assignment_ids = fields.RelationListField(
#         to={"assignment": "category_id"}, is_view_field=True
#     )
#     meeting_id = fields.RelationField(
#         to={"meeting": "assignment_category_ids"}, required=True, constant=True
#     )

# # updated
# class Meeting(prev_registry["meeting"]):
#     assignment_category_ids = fields.RelationListField(
#         to={"assignment_category": "meeting_id"},
#         on_delete=fields.OnDelete.CASCADE,
#         is_view_field=True,
#     )
    
#     # Rename motions_number_type to motions_assignments_number_type
#     motions_assignments_number_type = fields.CharField(
#         default="per_category",
#         constraints={"enum": ["per_category", "serially_numbered", "manually"]},
#     )
#     motions_number_type = None
#     # relations to deleted models
#     assignment_candidate_ids = None
    
# class Assignment(prev_registry["meeting"]):
#     category_id = fields.RelationField(to={"assignment_category": "motion_ids"})
#     # relations to deleted models
#     candidate_ids = None

# class MeetingUser(prev_registry["meeting_user"]):
#     # relations to deleted models
#     assignment_candidate_ids = None

# # deleted
# class AssignmentCandidate(MigrationModelDelete):
#     pass

# model_registry = model_registry_class.get_model_registry()