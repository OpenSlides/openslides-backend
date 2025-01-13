from collections import defaultdict
from typing import Dict, List

from openslides_backend.shared.typing import Collection, Field, Fqid


# Postgres only supports 1664 columns per query, so choose a number below that
MAX_UNIQUE_FIELDS_PER_QUERY = 1000


class MappedFields:
    """
    Container class for mapped fields and all related data. Only automatically calculated field is
    `needs_whole_model`, all other fields have to be set by the user.
    """

    per_fqid: Dict[Fqid, List[Field]]
    unique_fields: List[Field]
    collections: List[Collection]
    fqids: List[Fqid]
    needs_whole_model: bool

    def __init__(self, mapped_fields: List[Field] = []) -> None:
        self.per_fqid = defaultdict(list)
        self.unique_fields = mapped_fields
        self.collections = []
        self.post_init()

    def post_init(self) -> None:
        self.fqids = list(self.per_fqid.keys())
        self.needs_whole_model = (
            len(self.unique_fields) == 0
            or any(len(fields) == 0 for fields in self.per_fqid.values())
            or len(self.unique_fields) > MAX_UNIQUE_FIELDS_PER_QUERY
        )
