from typing import Any, Dict, Iterable, List, Tuple, Type

from ...models.fields import (
    BaseGenericRelationField,
    BaseRelationField,
    BaseTemplateRelationField,
    OnDelete,
)
from ...shared.exceptions import ActionException, ProtectedModelsException
from ...shared.interfaces.event import EventType
from ...shared.interfaces.write_request import WriteRequest
from ...shared.patterns import FullQualifiedId
from ...shared.typing import DeletedModel, ModelMap
from ..action import Action
from ..util.actions_map import actions_map
from ..util.typing import ActionData


class DeleteAction(Action):
    """
    Generic delete action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes care of on_delete handling.
        """
        # TODO: Check if instance exists in DB and is not deleted. Ensure that meta_deleted field is added to locked_fields.

        # Update instance (by default this does nothing)
        instance = self.update_instance(instance)

        # Fetch db instance with all relevant fields
        this_fqid = FullQualifiedId(self.model.collection, instance["id"])
        relevant_fields = [
            field.own_field_name
            for field in self.model.get_relation_fields()
            if field.on_delete != OnDelete.SET_NULL
        ]
        db_instance = self.datastore.get(
            fqid=this_fqid,
            mapped_fields=relevant_fields,
            lock_result=True,
        )

        # Collect relation fields and also update instance and set
        # all relation fields to None.
        relation_fields: List[Tuple[str, BaseRelationField]] = []
        # Gather all delete actions with action data and also all models to be deleted
        delete_actions: List[Tuple[Type[Action], ActionData]] = []
        additional_relation_models: ModelMap = {this_fqid: DeletedModel()}
        for field in self.model.get_relation_fields():
            # Check on_delete.
            if field.on_delete != OnDelete.SET_NULL:
                if isinstance(field, BaseTemplateRelationField):
                    # We currently do not support such template fields.
                    raise NotImplementedError

                # Extract all foreign keys as fqids from the model
                foreign_fqids = db_instance.get(field.own_field_name, [])
                if not isinstance(foreign_fqids, list):
                    foreign_fqids = [foreign_fqids]
                if not isinstance(field, BaseGenericRelationField):
                    assert len(field.to) == 1
                    foreign_fqids = [
                        FullQualifiedId(field.get_target_collection(), id)
                        for id in foreign_fqids
                    ]

                if field.on_delete == OnDelete.PROTECT:
                    protected_fqids = [
                        fqid
                        for fqid in foreign_fqids
                        if not isinstance(
                            self.additional_relation_models.get(fqid), DeletedModel
                        )
                    ]
                    if protected_fqids:
                        raise ProtectedModelsException(this_fqid, protected_fqids)
                else:
                    # field.on_delete == OnDelete.CASCADE
                    # Extract all foreign keys as fqids from the model
                    value = db_instance.get(field.own_field_name, [])
                    foreign_fqids = self.get_field_value_as_fqid_list(field, value)

                    # Execute the delete action for all fqids
                    for fqid in foreign_fqids:
                        if isinstance(
                            self.additional_relation_models.get(fqid), DeletedModel
                        ):
                            # skip models that are already deleted
                            continue
                        delete_action_class = actions_map.get(
                            f"{str(fqid.collection)}.delete"
                        )
                        if not delete_action_class:
                            raise ActionException(
                                f"Can't cascade the delete action to {str(fqid.collection)} "
                                "since no delete action was found."
                            )
                        # Assume that the delete action uses the standard action data
                        action_data = [{"id": fqid.id}]
                        delete_actions.append((delete_action_class, action_data))
                        additional_relation_models[fqid] = DeletedModel()
            else:
                # field.on_delete == OnDelete.SET_NULL
                if isinstance(field, BaseTemplateRelationField):
                    template_field_name = field.get_template_field_name()
                    db_instance = self.datastore.get(
                        fqid=FullQualifiedId(self.model.collection, instance["id"]),
                        mapped_fields=[template_field_name],
                        lock_result=True,
                    )
                    for replacement in db_instance.get(template_field_name, []):
                        structured_field_name = field.get_structured_field_name(
                            replacement
                        )
                        instance[structured_field_name] = None
                        relation_fields.append((structured_field_name, field))
                else:
                    instance[field.own_field_name] = None
                    relation_fields.append((field.own_field_name, field))

        # Add additional relation models and execute all previously gathered delete actions
        # catch all protected models exception to gather all protected fqids
        all_protected_fqids: List[FullQualifiedId] = []
        for delete_action_class, delete_action_data in delete_actions:
            try:
                self.execute_other_action(
                    delete_action_class, delete_action_data, additional_relation_models
                )
            except ProtectedModelsException as e:
                all_protected_fqids.extend(e.fqids)

        if all_protected_fqids:
            raise ProtectedModelsException(this_fqid, all_protected_fqids)

        return instance

    def create_write_requests(self, instance: Dict[str, Any]) -> Iterable[WriteRequest]:
        fqid = FullQualifiedId(self.model.collection, instance["id"])
        information = "Object deleted"
        yield self.build_write_request(EventType.Delete, fqid, information)
