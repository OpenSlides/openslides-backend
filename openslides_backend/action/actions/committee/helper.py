from typing import Dict, List, Optional

from ....shared.filters import FilterOperator, Or
from ....shared.interfaces.services import DatastoreService


class Lookup:
    def __init__(
        self,
        datastore: DatastoreService,
        collection: str,
        names: List[str],
        field: str = "name",
    ) -> None:
        if not names:
            self.name_to_id: Dict[str, Optional[int]] = {}
        else:
            self.name_to_id = {
                entry[field]: entry["id"]
                for entry in datastore.filter(
                    collection,
                    Or(*[FilterOperator(field, "=", name) for name in names]),
                    ["id", field],
                ).values()
            }

    def check_duplicate(self, name: str) -> bool:
        result = name in self.name_to_id
        if not result:
            self.name_to_id[name] = None
        return result

    def get_id_by_name(self, name: str) -> Optional[int]:
        return self.name_to_id.get(name)


class CommitteeDuplicateChecker(Lookup):
    def __init__(self, datastore: DatastoreService, names: List[str]) -> None:
        super().__init__(datastore, "committee", names)
