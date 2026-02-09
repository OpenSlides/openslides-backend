from collections.abc import Iterable
from typing import Any, cast

from ...models.fields import BaseRelationField, OnDelete
from ...shared.exceptions import ActionException, ProtectedModelsException
from ...shared.interfaces.event import Event, EventType
from ...shared.patterns import (
    FullQualifiedId,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
    transform_to_fqids,
)
from ...shared.typing import DeletedModel
from ..action import Action
from ..util.actions_map import actions_map
from ..util.typing import ActionData


class DeleteAction(Action):
    """
    Generic delete action.
    """

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Takes care of on_delete handling.
        """
        this_fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])

        if self.datastore.is_to_be_deleted(this_fqid):
            return instance
        self.datastore.apply_to_be_deleted(this_fqid)

        relevant_fields = [
            field.get_own_field_name() for field in self.model.get_relation_fields()
        ]
        # Fetch db instance with all relevant fields
        # Executed before update_instance so that actions can manually set a
        # DeletedModel or other changed_models without changing the result of this.
        db_instance = self.datastore.get(
            fqid=this_fqid,
            mapped_fields=relevant_fields,
        )

        # Update instance (by default this does nothing)
        instance = self.update_instance(instance)

        # Update instance and set relation fields to None.
        # Gather all delete actions with action data and also all models to be deleted
        delete_actions: list[tuple[FullQualifiedId, type[Action], ActionData]] = []
        for field_name, value in dict(sorted(db_instance.items())).items():
            if field_name == "id":
                continue
            field = cast(BaseRelationField, self.model.get_field(field_name))
            # Check on_delete.
            # Extract all foreign keys as fqids from the model
            foreign_fqids = transform_to_fqids(value, field.get_target_collection())
            if field.on_delete != OnDelete.SET_NULL:
                if field.on_delete == OnDelete.PROTECT:
                    protected_fqids = [
                        fqid
                        for fqid in foreign_fqids
                        if not self.datastore.is_to_be_deleted_for_protected(fqid)
                    ]
                    if protected_fqids:
                        raise ProtectedModelsException(this_fqid, protected_fqids)
                else:
                    # case: field.on_delete == OnDelete.CASCADE
                    # Execute the delete action for all fqids
                    for fqid in foreign_fqids:
                        if self.datastore.is_to_be_deleted(fqid):
                            # Skip models that are already tracked for deletion
                            continue
                        delete_action_class = actions_map.get(
                            f"{collection_from_fqid(fqid)}.delete"
                        )
                        if not delete_action_class:
                            raise ActionException(
                                f"Can't cascade the delete action to {collection_from_fqid(fqid)} "
                                "since no delete action was found."
                            )
                        # Assume that the delete action uses the standard action data
                        action_data = [{"id": id_from_fqid(fqid)}]
                        delete_actions.append((fqid, delete_action_class, action_data))
                        self.datastore.apply_to_be_deleted_for_protected(fqid)
            elif field.is_view_field:
                # case: field.on_delete == OnDelete.SET_NULL
                instance[field_name] = None

        # Add additional relation models and execute all previously gathered delete actions
        # catch all protected models exception to gather all protected fqids
        all_protected_fqids: list[FullQualifiedId] = []
        for fqid, delete_action_class, delete_action_data in delete_actions:
            try:
                # Skip models that were deleted in the meantime
                if not self.datastore.is_deleted(fqid):
                    self.execute_other_action(delete_action_class, delete_action_data)
            except ProtectedModelsException as e:
                all_protected_fqids.extend(e.fqids)

        if all_protected_fqids:
            raise ProtectedModelsException(this_fqid, all_protected_fqids)

        self.datastore.apply_changed_model(this_fqid, DeletedModel())
        return instance

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        fqid = fqid_from_collection_and_id(self.model.collection, instance["id"])
        yield self.build_event(EventType.Delete, fqid)

    def is_meeting_to_be_deleted(self, meeting_id: int) -> bool:
        """
        Returns whether the given meeting was/will be deleted during this request or not.
        """
        return self.datastore.is_to_be_deleted(
            fqid_from_collection_and_id("meeting", meeting_id)
        )

    def is_to_be_deleted(self, fqid: FullQualifiedId) -> bool:
        return self.datastore.is_to_be_deleted(fqid)
