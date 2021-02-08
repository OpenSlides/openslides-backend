import re
import time
from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....shared.patterns import KEYSEPARATOR, Collection, FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action

RERIDS_PATTERN = re.compile(r"\[(?P<fqid>\w+/\d+)\]")


@register_action("motion.update_metadata")
class MotionUpdateMetadata(UpdateAction):
    """
    Action to update motion metadata.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_update_schema(
        optional_properties=[
            "state_extension",
            "recommendation_extension",
            "category_id",
            "block_id",
            "supporter_ids",
            "tag_ids",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["last_modified"] = round(time.time())

        if instance.get("recommendation_extension"):
            self.set_recommendation_extension_reference_ids(instance)
        return instance

    def set_recommendation_extension_reference_ids(
        self, instance: Dict[str, Any]
    ) -> None:
        recommendation_extension_reference_ids = []
        possible_rerids = RERIDS_PATTERN.findall(instance["recommendation_extension"])
        for fqid_str in possible_rerids:
            collection, id_ = fqid_str.split(KEYSEPARATOR)
            if collection != "motion":
                raise ActionException(f"Found {fqid_str} but only motion is allowed.")
            exists = self.datastore.exists(
                collection=Collection(collection),
                filter=FilterOperator("id", "=", int(id_)),
            )
            if exists:
                recommendation_extension_reference_ids.append(
                    FullQualifiedId(Collection(collection), id_)
                )
        instance[
            "recommendation_extension_reference_ids"
        ] = recommendation_extension_reference_ids
